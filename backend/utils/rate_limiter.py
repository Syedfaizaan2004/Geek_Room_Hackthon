"""
utils/rate_limiter.py — Phase 16 Simple In-Memory Rate Limiter.

Sliding-window rate limiter per user_id.
No Redis required — works with a single uvicorn worker.
For multi-worker deployments: replace with Redis-backed SlideWindow.

Defaults:
  - 30 requests per minute per user for analysis endpoints
  - 60 requests per minute per user for read-only endpoints
"""

import time
import logging
from collections import defaultdict, deque
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Sliding-window store
# ─────────────────────────────────────────────────────────────────────────────
# Keyed by (user_id, endpoint_group) → deque of request timestamps
_windows: dict = defaultdict(deque)


def check_rate_limit(
    user_id: str,
    endpoint_group: str = "default",
    max_requests: int = 30,
    window_seconds: int = 60,
) -> None:
    """
    Raises HTTP 429 if the user has exceeded max_requests in the last window_seconds.
    
    Args:
        user_id:        unique user identifier (from JWT)
        endpoint_group: logical group label (e.g. 'analysis', 'read')
        max_requests:   allowed requests in window
        window_seconds: rolling window size in seconds
    
    Raises:
        HTTPException 429 if rate limit exceeded.
    """
    key = f"{user_id}:{endpoint_group}"
    now = time.monotonic()
    window = _windows[key]

    # Drop timestamps outside the current window
    cutoff = now - window_seconds
    while window and window[0] < cutoff:
        window.popleft()

    if len(window) >= max_requests:
        logger.warning("Rate limit hit: user=%s group=%s (%d/%d req in %ds)",
                       user_id, endpoint_group, len(window), max_requests, window_seconds)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "success": False,
                "error": "Rate limit exceeded",
                "detail": f"Maximum {max_requests} requests per {window_seconds}s. Please wait before retrying.",
                "retry_after_seconds": window_seconds,
            },
            headers={"Retry-After": str(window_seconds)},
        )

    window.append(now)


# ─────────────────────────────────────────────────────────────────────────────
# FastAPI dependency factories
# ─────────────────────────────────────────────────────────────────────────────

def analysis_rate_limit(user_id: str) -> None:
    """
    Dependency for heavy analysis endpoints.
    Limit: 20 requests per minute.
    """
    check_rate_limit(user_id, "analysis", max_requests=20, window_seconds=60)


def read_rate_limit(user_id: str) -> None:
    """
    Dependency for lightweight read endpoints.
    Limit: 60 requests per minute.
    """
    check_rate_limit(user_id, "read", max_requests=60, window_seconds=60)
