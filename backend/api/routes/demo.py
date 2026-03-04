"""
api/routes/demo.py — Phase 16 Demo Mode Endpoint.

Provides instant analysis without live API calls or Qdrant.
Ideal for evaluators, hackathons, and initial setup.

Endpoints:
  GET /demo/tickers          — list of supported demo tickers
  GET /demo/analyze/{ticker} — return pre-built analysis payload
  GET /demo/status           — demo mode status + cache stats
"""

import logging
from fastapi import APIRouter, HTTPException

from app.config import settings
from demo.fixtures import get_demo_data, DEMO_TICKERS

router = APIRouter(prefix="/demo", tags=["Demo Mode"])
logger = logging.getLogger(__name__)


@router.get("/status")
async def demo_status():
    """Returns demo mode configuration and cache stats."""
    from utils.performance import get_cache_stats
    return {
        "demo_mode_enabled": settings.DEMO_MODE,
        "demo_tickers": DEMO_TICKERS,
        "default_ticker": settings.DEMO_DEFAULT_TICKER,
        "cache": get_cache_stats(),
        "version": "0.16.0",
        "message": (
            "Demo mode active — no API keys required."
            if settings.DEMO_MODE
            else "Demo mode is disabled. Set DEMO_MODE=true in .env to enable."
        ),
    }


@router.get("/tickers")
async def list_demo_tickers():
    """Returns the list of tickers available in demo mode."""
    return {
        "tickers": DEMO_TICKERS,
        "count": len(DEMO_TICKERS),
        "note": "These tickers have pre-computed realistic data available without API keys.",
    }


@router.get("/analyze/{ticker}")
async def demo_analyze(ticker: str):
    """
    Returns a complete pre-built analysis payload for the given ticker.
    No authentication, no live API calls.
    Designed for demos, evaluators, and hackathon presenters.
    """
    if not settings.DEMO_MODE:
        raise HTTPException(
            status_code=403,
            detail="Demo mode is disabled. Set DEMO_MODE=true in .env to enable.",
        )

    ticker = ticker.strip().upper()
    logger.info(f"Demo analysis requested for {ticker}")
    payload = get_demo_data(ticker)
    return payload
