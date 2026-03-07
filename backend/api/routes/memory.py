"""
api/routes/memory.py — Semantic Memory API endpoints (Phase 12).

All routes require authentication.

Endpoints:
  POST /memory/search                → Semantic insight search (user-scoped)
  GET  /memory/similar/{ticker}      → Find similar companies globally
  GET  /memory/risk-pattern          → Tickers above risk threshold
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Query

from api.routes.auth import get_current_user
from memory.models import User
from schemas.memory import (
    MemorySearchRequest,
    MemorySearchResponse,
    MemorySimilarResult,
    MemoryRecentResult,
    RiskPatternResult,
)

router = APIRouter()
logger = logging.getLogger(__name__)


def _get_qdrant_client():
    """Get the Qdrant client, raise 503 if unavailable."""
    from vector_store.qdrant_client import qdrant_wrapper
    if not qdrant_wrapper.is_healthy or qdrant_wrapper.client is None:
        raise HTTPException(
            status_code=503,
            detail="Vector memory service is currently unavailable. "
                   "Ensure Qdrant cloud credentials are valid in .env"
        )
    return qdrant_wrapper.client


# ── POST /memory/search ───────────────────────────────────────────────────────

@router.post("/memory/search", response_model=MemorySearchResponse)
async def search_memory(
    body: MemorySearchRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Semantic search through your past research sessions.

    Embeds the query text and finds the most similar stored insights
    using cosine similarity. Results are scoped to your user account.

    Example queries:
    - "tech companies with high growth but elevated risk"
    - "bullish outlook with strong cash flow"
    - "similar to my AAPL analysis"
    """
    client = _get_qdrant_client()
    logger.info(f"Memory search: '{body.query[:60]}' for user={current_user.unique_user_id}")

    try:
        from vector_store.memory_service import retrieve_similar_insights
        # Prefer stable UUID-based key; fallback to legacy unique_user_id key.
        user_keys = [str(current_user.id), current_user.unique_user_id]
        results = []
        for key in user_keys:
            results = await retrieve_similar_insights(
                client=client,
                query_text=body.query,
                user_id=key,
                top_k=body.top_k,
            )
            if results:
                break
        return MemorySearchResponse(
            query=body.query,
            similar_results=results,
            total_found=len(results),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Memory search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Memory search failed: {str(e)}")


# ── GET /memory/similar/{ticker} ──────────────────────────────────────────────

@router.get("/memory/similar/{ticker}", response_model=MemorySearchResponse)
async def find_similar_companies(
    ticker: str,
    top_k: int = Query(default=5, ge=1, le=10),
    current_user: User = Depends(get_current_user),
):
    """
    Discover companies that are semantically similar to the given ticker
    based on stored research embeddings.

    Searches across ALL users' stored insights (not scoped by user_id)
    to maximise the discovery pool.
    """
    ticker = ticker.upper().strip()
    client = _get_qdrant_client()
    logger.info(f"Similar company search for {ticker} by user={current_user.unique_user_id}")

    try:
        # First generate a query text for this ticker using a live insight fetch
        from analytics.service import get_market_snapshot
        from vector_store.embeddings import build_insight_text

        query_text = f"Financial analysis of {ticker} stock"
        try:
            snap = get_market_snapshot(ticker, period="1y")
            query_text = build_insight_text(
                ticker=ticker,
                executive_summary=f"{ticker} is a company trading at ${snap.last_price:.2f} with {snap.trend_direction} momentum."
            )
        except Exception:
            pass  # Fall back to generic query text

        from vector_store.memory_service import find_similar_companies as _find
        results = await _find(
            client=client,
            ticker=ticker,
            insight_text=query_text,
            top_k=top_k,
        )
        return MemorySearchResponse(
            query=f"Companies similar to {ticker}",
            similar_results=results,
            total_found=len(results),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Similar company search failed for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── GET /memory/risk-pattern ──────────────────────────────────────────────────

@router.get("/memory/risk-pattern", response_model=list)
async def get_risk_pattern(
    threshold: float = Query(default=70.0, ge=0.0, le=100.0, description="Minimum risk score"),
    current_user: User = Depends(get_current_user),
):
    """
    Return all previously-researched tickers whose composite risk score
    exceeds the specified threshold.

    Uses Qdrant metadata filtering — no embedding needed.
    Useful for portfolio-level risk monitoring.

    Example: GET /memory/risk-pattern?threshold=70
    Returns all tickers you or anyone has analysed with risk > 70/100.
    """
    client = _get_qdrant_client()
    logger.info(f"Risk pattern search: threshold={threshold}")

    try:
        from vector_store.memory_service import search_by_risk_pattern
        results = await search_by_risk_pattern(
            client=client,
            risk_threshold=threshold,
            limit=50,
        )
        return [r.model_dump() for r in results]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Risk pattern search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# —— GET /memory/recent ————————————————————————————————————————————————————————————————

@router.get("/memory/recent", response_model=list[MemoryRecentResult])
async def get_recent_memory(
    limit: int = Query(default=20, ge=1, le=100, description="Max recent analyses"),
    current_user: User = Depends(get_current_user),
):
    """
    Return recently stored analyses for the authenticated user.
    """
    client = _get_qdrant_client()
    logger.info("Recent memory requested by user=%s (limit=%s)", current_user.unique_user_id, limit)

    try:
        from vector_store.memory_service import retrieve_recent_insights

        results = []
        for key in (str(current_user.id), current_user.unique_user_id):
            results = await retrieve_recent_insights(
                client=client,
                user_id=key,
                limit=limit,
            )
            if results:
                break
        return results
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Recent memory retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
