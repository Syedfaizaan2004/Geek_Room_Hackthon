"""
api/routes/metrics.py — Phase 16 Performance Metrics Endpoint.

GET /metrics  — returns accumulated performance metrics
GET /metrics/cache — cache layer stats only
GET /metrics/reset — reset counters (admin use)
"""

import logging
from fastapi import APIRouter, Depends

from api.routes.auth import get_current_user
from memory.models import User

router = APIRouter(prefix="/metrics", tags=["Performance Metrics"])
logger = logging.getLogger(__name__)


@router.get("")
async def get_metrics(current_user: User = Depends(get_current_user)):
    """
    Returns accumulated performance metrics for the entire server process.

    Example response:
    {
      "uptime_seconds": 3820.5,
      "total_requests": 142,
      "cache_hits": 89,
      "cache_misses": 53,
      "cache_hit_rate_pct": 62.7,
      "per_mode_latency": {
        "quick": {"avg_ms": 1820.3, "p95_ms": 3400.0, "total_calls": 90},
        "deep":  {"avg_ms": 41200.0, "p95_ms": 58000.0, "total_calls": 52}
      },
      "average_quick_mode_ms": 1820.3,
      "average_deep_mode_ms": 41200.0,
      "llm": {
        "total_calls": 22,
        "total_tokens": 44300,
        "total_cost_usd": 0.000443,
        "avg_cost_per_call": 0.0000201
      },
      "external_apis": {
        "qdrant_avg_ms": 85.2,
        "yfinance_avg_ms": 1240.5,
        "db_avg_ms": 3.1
      }
    }
    """
    from utils.performance_logger import perf_logger
    return perf_logger.get_metrics_snapshot()


@router.get("/cache")
async def get_cache_stats(current_user: User = Depends(get_current_user)):
    """Returns cache layer stats for both L1 (in-memory) and L2 (SQLite)."""
    from utils.cache_manager import cache_manager
    from utils.performance import get_cache_stats
    return {
        "multi_layer": cache_manager.stats(),
        "result_cache": get_cache_stats(),
    }


@router.get("/demo")
async def get_demo_status():
    """Public endpoint — returns demo mode status and preloaded tickers. No auth required."""
    from app.config import settings
    from utils.demo_mode import PRELOAD_TICKERS
    return {
        "demo_mode": settings.DEMO_MODE,
        "preloaded_tickers": PRELOAD_TICKERS,
        "llm_provider": settings.LLM_PROVIDER,
        "cache_ttl_seconds": settings.CACHE_TTL,
    }
