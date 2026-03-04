"""
utils/timeout_handler.py — Phase 16 Async Timeout Protection.

Wraps any coroutine with a configurable timeout.
Returns partial results or a fallback payload if the timeout is exceeded.
System must never crash because of a slow external API.
"""

import asyncio
import logging
from typing import Any, Callable, Optional, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")

# Default timeouts (seconds)
TIMEOUT_QUICK = 15      # Quick mode: market + forecast + risk
TIMEOUT_DEEP = 90       # Deep mode: full 8-engine pipeline
TIMEOUT_EXTERNAL_API = 10  # Individual yfinance / Qdrant / LLM call
TIMEOUT_LLM = 20        # LLM enhancement call


async def run_with_timeout(
    coro,
    timeout: float,
    fallback: Any = None,
    label: str = "operation",
) -> Any:
    """
    Run `coro` with a strict timeout.
    Returns `fallback` value if the timeout is exceeded (never raises).

    Args:
        coro:     The awaitable to run.
        timeout:  Seconds before cancellation.
        fallback: Return value on timeout (default: None).
        label:    Human-readable label for the log message.

    Returns:
        The result of `coro`, or `fallback` on timeout / exception.
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        logger.warning("TIMEOUT: %s exceeded %.1fs — returning fallback", label, timeout)
        return fallback
    except Exception as e:
        logger.error("ERROR in %s (non-fatal): %s", label, e)
        return fallback


async def run_with_partial_fallback(
    coro,
    timeout: float,
    partial_key: str = "error",
    label: str = "operation",
) -> dict:
    """
    Run `coro` expecting a dict result.
    On timeout or error, returns a dict with `partial_data=True` and an error note.

    Useful for engine nodes where a partial response is better than silence.
    """
    try:
        result = await asyncio.wait_for(coro, timeout=timeout)
        if result is None:
            return {partial_key: None, "partial_data": True, "reason": "empty_result"}
        return result
    except asyncio.TimeoutError:
        logger.warning("TIMEOUT (partial): %s exceeded %.1fs", label, timeout)
        return {
            "partial_data": True,
            "reason": f"{label}_timeout",
            "timeout_seconds": timeout,
        }
    except Exception as e:
        logger.error("ERROR (partial): %s — %s", label, e)
        return {
            "partial_data": True,
            "reason": f"{label}_error",
            "detail": str(e),
        }


class TimeoutGuard:
    """
    Context manager that cancels a block if it takes too long.
    Usage:
        async with TimeoutGuard(10, label="yfinance call") as guard:
            data = await fetch_something()
    If timeout fires, `guard.timed_out` will be True after the block.
    """

    def __init__(self, timeout: float, label: str = "block"):
        self.timeout = timeout
        self.label = label
        self.timed_out = False
        self._task: Optional[asyncio.Task] = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is asyncio.TimeoutError:
            self.timed_out = True
            logger.warning("TimeoutGuard: %s exceeded %.1fs", self.label, self.timeout)
            return True  # Suppress the exception
        return False
