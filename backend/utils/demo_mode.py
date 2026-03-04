"""
utils/demo_mode.py — Phase 16 Demo Mode Manager & Cold-Start Preloader.

Handles:
1. Detecting if DEMO_MODE is active
2. Preloading common demo tickers into the cache on startup
3. LLM warm-up (lightweight ping call, optional)
4. DB + Qdrant initialization check

Preloaded tickers: AAPL, TSLA, MSFT, NVDA, AMZN
"""

import logging
import asyncio
from typing import List

logger = logging.getLogger(__name__)

PRELOAD_TICKERS: List[str] = ["AAPL", "TSLA", "MSFT", "NVDA", "AMZN", "GOOGL"]


async def preload_demo_tickers() -> None:
    """
    Preload demo fixture data into the L1+L2 cache at startup.
    Uses static fixtures — no live API calls required.
    Completes in < 100ms.
    """
    from app.config import settings
    if not settings.DEMO_MODE:
        logger.info("Demo mode disabled — skipping ticker preload.")
        return

    from demo.fixtures import get_demo_data
    from utils.cache_manager import cache_manager

    logger.info("Demo mode: Preloading %d tickers into cache...", len(PRELOAD_TICKERS))
    preloaded = []

    for ticker in PRELOAD_TICKERS:
        for mode in ("quick", "deep"):
            key = cache_manager.make_key(ticker, mode, "__demo__")
            payload = get_demo_data(ticker)
            await cache_manager.aset(key, payload, ttl=86400)  # 24 hours — static data
            preloaded.append(f"{ticker}:{mode}")

    logger.info("Demo preload complete — %d entries cached: %s", len(preloaded), preloaded)


async def check_db_health() -> bool:
    """Ping the DB connection to ensure it's ready at startup."""
    try:
        from db.session import AsyncSessionLocal
        async with AsyncSessionLocal() as session:
            await session.execute(__import__("sqlalchemy").text("SELECT 1"))
        logger.info("DB health check: OK")
        return True
    except Exception as e:
        logger.warning("DB health check failed (non-fatal): %s", e)
        return False


async def check_qdrant_health() -> bool:
    """Verify Qdrant connection and collection on startup."""
    try:
        from vector_store.qdrant_client import qdrant_wrapper
        if qdrant_wrapper.is_healthy:
            logger.info("Qdrant health check: OK (connected)")
            return True
        else:
            logger.warning("Qdrant health check: not connected — memory features will be limited.")
            return False
    except Exception as e:
        logger.warning("Qdrant health check failed (non-fatal): %s", e)
        return False


async def warm_up_llm() -> None:
    """
    Optional: Send a tiny no-op prompt to the LLM provider to prime the connection.
    Only runs if DEMO_MODE=false and LLM is enabled.
    """
    from app.config import settings
    if settings.DEMO_MODE or settings.LLM_PROVIDER == "disabled":
        return
    try:
        from llm.llm_service import answer_chat
        await answer_chat(
            query="Respond with: ready",
            session_context="warmup",
            memory_context="",
        )
        logger.info("LLM warm-up call: OK")
    except Exception as e:
        logger.warning("LLM warm-up failed (non-fatal): %s", e)


async def run_cold_start_tasks() -> None:
    """
    Master cold-start routine called from app lifespan on startup.
    Runs all checks and preloads concurrently.
    Any individual failure is non-fatal.
    """
    from utils.cache_manager import cache_manager

    logger.info("Cold-start initialization...")

    # Initialize L2 SQLite cache table
    await cache_manager.init()

    # Run health checks + preload in parallel
    results = await asyncio.gather(
        check_db_health(),
        check_qdrant_health(),
        preload_demo_tickers(),
        return_exceptions=True,
    )

    db_ok = results[0] is True
    qdrant_ok = results[1] is True

    logger.info(
        "Cold-start complete. DB=%s Qdrant=%s DemoPreload=%s",
        "OK" if db_ok else "WARN",
        "OK" if qdrant_ok else "WARN",
        "OK",
    )

    # LLM warm-up is best-effort and separate (can be slow)
    asyncio.create_task(warm_up_llm())
