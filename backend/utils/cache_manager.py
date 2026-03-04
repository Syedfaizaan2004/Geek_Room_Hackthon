"""
utils/cache_manager.py — Phase 16 Multi-Layer Cache Manager.

Layer 1: In-memory TTL dict (fast, volatile — lost on restart)
Layer 2: SQLite persistent cache (survives restarts — async via aiosqlite)

Key format: "{ticker}_{mode}_{user_id}"

Usage:
    cache = CacheManager()
    cache.set("AAPL_quick_user1", payload, ttl=300)
    data = cache.get("AAPL_quick_user1")
    cache.invalidate("AAPL_quick_user1")
"""

import time
import json
import logging
import asyncio
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

_DB_PATH = Path(__file__).resolve().parent.parent / "cache_store.db"
_L1_DEFAULT_TTL = 300   # 5 minutes in-memory
_L2_DEFAULT_TTL = 3600  # 1 hour SQLite


# ─────────────────────────────────────────────────────────────────────────────
# Layer 1 — In-Memory TTL Cache
# ─────────────────────────────────────────────────────────────────────────────

class _L1Cache:
    """Ultra-fast in-process dict cache with TTL expiry."""

    def __init__(self, default_ttl: int = _L1_DEFAULT_TTL):
        self._store: dict[str, tuple[Any, float]] = {}  # key → (value, expires_at)
        self._default_ttl = default_ttl

    def get(self, key: str) -> Optional[Any]:
        entry = self._store.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if time.monotonic() > expires_at:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        ttl = ttl or self._default_ttl
        self._store[key] = (value, time.monotonic() + ttl)

    def invalidate(self, key: str) -> None:
        self._store.pop(key, None)

    def clear(self) -> None:
        self._store.clear()

    def stats(self) -> dict:
        now = time.monotonic()
        live = sum(1 for _, (_, exp) in self._store.items() if exp > now)
        return {"total": len(self._store), "live": live, "expired": len(self._store) - live}


# ─────────────────────────────────────────────────────────────────────────────
# Layer 2 — SQLite Persistent Cache (aiosqlite)
# ─────────────────────────────────────────────────────────────────────────────

_l2_initialized = False

async def _ensure_l2_table() -> None:
    global _l2_initialized
    if _l2_initialized:
        return
    try:
        import aiosqlite
        async with aiosqlite.connect(_DB_PATH) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS cache_store (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    expires_at REAL NOT NULL
                )
            """)
            await db.commit()
        _l2_initialized = True
        logger.debug("L2 SQLite cache table ready at %s", _DB_PATH)
    except ImportError:
        logger.warning("aiosqlite not installed — L2 cache disabled. Run: pip install aiosqlite")
    except Exception as e:
        logger.warning("L2 cache init failed (non-fatal): %s", e)


async def _l2_get(key: str) -> Optional[Any]:
    try:
        import aiosqlite
        async with aiosqlite.connect(_DB_PATH) as db:
            async with db.execute(
                "SELECT value, expires_at FROM cache_store WHERE key=?", (key,)
            ) as cursor:
                row = await cursor.fetchone()
                if row is None:
                    return None
                value_str, expires_at = row
                if time.time() > expires_at:
                    # lazy evict
                    await db.execute("DELETE FROM cache_store WHERE key=?", (key,))
                    await db.commit()
                    return None
                return json.loads(value_str)
    except Exception as e:
        logger.debug("L2 cache get failed (non-fatal): %s", e)
        return None


async def _l2_set(key: str, value: Any, ttl: int = _L2_DEFAULT_TTL) -> None:
    try:
        import aiosqlite
        expires_at = time.time() + ttl
        value_str = json.dumps(value, default=str)
        async with aiosqlite.connect(_DB_PATH) as db:
            await db.execute(
                "INSERT OR REPLACE INTO cache_store (key, value, expires_at) VALUES (?, ?, ?)",
                (key, value_str, expires_at),
            )
            await db.commit()
    except Exception as e:
        logger.debug("L2 cache set failed (non-fatal): %s", e)


async def _l2_invalidate(key: str) -> None:
    try:
        import aiosqlite
        async with aiosqlite.connect(_DB_PATH) as db:
            await db.execute("DELETE FROM cache_store WHERE key=?", (key,))
            await db.commit()
    except Exception as e:
        logger.debug("L2 cache invalidate failed: %s", e)


# ─────────────────────────────────────────────────────────────────────────────
# CacheManager — Unified Interface
# ─────────────────────────────────────────────────────────────────────────────

class CacheManager:
    """
    Two-layer cache manager.
    get() → checks L1 first, then L2 (and promotes to L1 on L2 hit)
    set() → writes to both layers
    invalidate() → removes from both layers
    """

    def __init__(self, l1_ttl: int = _L1_DEFAULT_TTL, l2_ttl: int = _L2_DEFAULT_TTL):
        self._l1 = _L1Cache(default_ttl=l1_ttl)
        self._l2_ttl = l2_ttl

    @staticmethod
    def make_key(ticker: str, mode: str, user_id: str) -> str:
        return f"{ticker.upper()}_{mode}_{user_id}"

    def get(self, key: str) -> Optional[Any]:
        """Synchronous get — L1 only. Use aget() for L1+L2."""
        return self._l1.get(key)

    async def aget(self, key: str) -> Optional[Any]:
        """Async get — checks L1 then falls back to L2."""
        val = self._l1.get(key)
        if val is not None:
            logger.debug("Cache L1 HIT: %s", key)
            return val
        val = await _l2_get(key)
        if val is not None:
            logger.debug("Cache L2 HIT (promoting to L1): %s", key)
            self._l1.set(key, val)
        return val

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Synchronous set to L1 only."""
        self._l1.set(key, value, ttl)

    async def aset(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Async set to both L1 and L2."""
        self._l1.set(key, value, ttl or _L1_DEFAULT_TTL)
        await _l2_set(key, value, ttl or self._l2_ttl)

    def invalidate(self, key: str) -> None:
        self._l1.invalidate(key)

    async def ainvalidate(self, key: str) -> None:
        self._l1.invalidate(key)
        await _l2_invalidate(key)

    def stats(self) -> dict:
        return {"l1": self._l1.stats(), "l2_path": str(_DB_PATH)}

    async def init(self) -> None:
        """Call on startup to ensure L2 table exists."""
        await _ensure_l2_table()


# ── Module-level singleton ────────────────────────────────────────────────────
cache_manager = CacheManager()
