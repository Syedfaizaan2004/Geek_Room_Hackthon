"""
utils/performance.py — Phase 16 Performance Middleware and Profiling Utilities.

Provides:
- RequestTimingMiddleware: logs latency for every request
- AgentResultCache: TTL cache for full agent run results (not just market data)
- cache_or_run(): decorator/helper to serve cached agent results
"""

import logging
import time
from typing import Any, Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.config import settings
from utils.caching import MarketDataCache

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# 1. Request Timing Middleware
# ─────────────────────────────────────────────────────────────────────────────

class RequestTimingMiddleware(BaseHTTPMiddleware):
    """
    Logs request method, path, status code, and elapsed time for every request.
    Only active when ENABLE_PERFORMANCE_LOGS=true.
    Adds X-Response-Time header to every response.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000

        response.headers["X-Response-Time"] = f"{elapsed_ms:.1f}ms"

        if settings.ENABLE_PERFORMANCE_LOGS:
            logger.info(
                "REQUEST %s %s → %d  (%.1fms)",
                request.method,
                request.url.path,
                response.status_code,
                elapsed_ms,
            )

        # Warn on slow requests
        if elapsed_ms > 5000:
            logger.warning("SLOW REQUEST: %s %s took %.0fms", request.method, request.url.path, elapsed_ms)

        return response


# ─────────────────────────────────────────────────────────────────────────────
# 2. Agent Result Cache (full analysis payloads)
# ─────────────────────────────────────────────────────────────────────────────

# Separate cache for full analysis results (longer TTL — 15 min)
_RESULT_CACHE_TTL = 900  # seconds

agent_result_cache = MarketDataCache(default_ttl=_RESULT_CACHE_TTL)


def get_cached_result(ticker: str, mode: str, user_id: str) -> Optional[Any]:
    """
    Returns a cached agent result if one exists and hasn't expired.
    Key: ticker:mode:user_id
    """
    if not settings.ENABLE_CACHE:
        return None
    key = f"result:{ticker.upper()}:{mode}:{user_id}"
    return agent_result_cache.get(key)


def cache_result(ticker: str, mode: str, user_id: str, payload: Any) -> None:
    """
    Stores agent result in the result cache.
    """
    if not settings.ENABLE_CACHE:
        return
    key = f"result:{ticker.upper()}:{mode}:{user_id}"
    agent_result_cache.set(key, payload)
    logger.debug("Cached agent result: %s", key)


def invalidate_result(ticker: str, mode: str, user_id: str) -> None:
    """Evict a specific cached result."""
    key = f"result:{ticker.upper()}:{mode}:{user_id}"
    agent_result_cache.invalidate(key)


def get_cache_stats() -> dict:
    """Returns stats for both market and result caches."""
    from utils.caching import market_cache
    return {
        "market_cache": market_cache.stats(),
        "result_cache": agent_result_cache.stats(),
        "cache_enabled": settings.ENABLE_CACHE,
        "result_cache_ttl_seconds": _RESULT_CACHE_TTL,
    }
