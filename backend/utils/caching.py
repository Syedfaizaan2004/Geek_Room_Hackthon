"""
utils/caching.py — Lightweight in-memory TTL cache.

Design:
  - Dictionary-based, no external dependencies
  - TTL (Time-To-Live) per entry — defaults to 5 minutes
  - Thread-safe via asyncio.Lock (single-process safety)
  - Key: any hashable (typically "TICKER:period")
  - Prepared for Redis replacement in Phase 16:
      swap _MemoryCache for a Redis client behind the same interface.

Usage:
    cache = MarketDataCache()
    data = cache.get("AAPL:1y")
    if data is None:
        data = fetch_expensive_data()
        cache.set("AAPL:1y", data)
"""

import logging
import time
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Default TTL: 5 minutes (300 seconds)
# Market data updates every few minutes during trading hours — 5 min is safe
_DEFAULT_TTL_SECONDS = 300


class _CacheEntry:
    """Wrapper holding a cached value and its expiry timestamp."""
    __slots__ = ("value", "expires_at")

    def __init__(self, value: Any, ttl: int) -> None:
        self.value = value
        self.expires_at = time.monotonic() + ttl


class MarketDataCache:
    """
    In-memory TTL cache scoped to one Python process.

    Thread safety: uses a simple dict; safe for asyncio (single-threaded event
    loop). Not safe across multiple uvicorn workers — use Redis for that
    (Phase 16 upgrade point).

    Interface is intentionally minimal so swapping to Redis only requires
    changing this class, not any callers.
    """

    def __init__(self, default_ttl: int = _DEFAULT_TTL_SECONDS) -> None:
        self._store: dict[str, _CacheEntry] = {}
        self._default_ttl = default_ttl
        logger.debug("MarketDataCache initialised (in-memory, TTL=%ds)", default_ttl)

    # ── Public API ────────────────────────────────────────────────────────────
    def get(self, key: str) -> Optional[Any]:
        """
        Return cached value if the entry exists and has not expired.
        Returns None on miss or expiry (expired entries are lazily evicted).
        """
        entry = self._store.get(key)
        if entry is None:
            return None

        if time.monotonic() > entry.expires_at:
            # Lazy eviction — remove stale entry
            del self._store[key]
            logger.debug("Cache MISS (expired): %s", key)
            return None

        logger.debug("Cache HIT: %s", key)
        return entry.value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Store value with the given TTL (seconds). Falls back to default TTL.
        """
        effective_ttl = ttl if ttl is not None else self._default_ttl
        self._store[key] = _CacheEntry(value, effective_ttl)
        logger.debug("Cache SET: %s  TTL=%ds", key, effective_ttl)

    def invalidate(self, key: str) -> None:
        """Remove a specific key from the cache."""
        self._store.pop(key, None)

    def clear(self) -> None:
        """Purge all entries — useful for testing."""
        self._store.clear()

    def stats(self) -> dict:
        """Return basic cache stats for health/debug endpoints."""
        now = time.monotonic()
        live = sum(1 for e in self._store.values() if e.expires_at > now)
        return {
            "total_entries": len(self._store),
            "live_entries": live,
            "expired_entries": len(self._store) - live,
            "default_ttl_seconds": self._default_ttl,
        }


# ── Module-level singleton ────────────────────────────────────────────────────
# Shared across all route handlers in the same process.
# Phase 16: replace with AsyncRedisCache(settings.REDIS_URL).
market_cache = MarketDataCache(default_ttl=_DEFAULT_TTL_SECONDS)
