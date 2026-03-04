"""
api/routes/compare.py — Peer Comparison Endpoint (Phase 8).
"""

import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query, HTTPException, status

from comparison.comparison_engine import run_peer_comparison
from analytics.fundamentals_engine import FundamentalsFetchError, InsufficientFundamentalsError
from analytics.service import MarketDataFetchError, TickerNotFoundError
from api.routes.auth import get_current_user
from memory.models import User
from schemas.comparison import ComparisonResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/compare", tags=["Comparison Engine"])

@router.get(
    "/{ticker}",
    response_model=ComparisonResponse,
    summary="Benchmark a company against peers",
    responses={
        401: {"description": "Missing or invalid token"},
        404: {"description": "Ticker not found or missing foundational data"},
        503: {"description": "External data provider unavailable for target"},
    },
)
async def get_peer_comparison(
    ticker: str,
    current_user: Annotated[User, Depends(get_current_user)],
    peers: Optional[str] = Query(None, description="Comma-separated optional peers (e.g. MSFT,GOOG)")
) -> ComparisonResponse:
    """
    Generate a comprehensive peer-group comparison analysis.
    Evaluates Valuation, Profitability, Growth, and Risk relative to sector peers.
    
    Optionally pass `?peers=TICKER1,TICKER2` to override the auto-lookup defaults.
    
    Requires: `Authorization: Bearer <token>`
    """
    try:
        # Cross-phase service layer orchestrator
        return run_peer_comparison(ticker, explicit_peers=peers)
        
    except (TickerNotFoundError, InsufficientFundamentalsError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": "Data missing or target ticker not found",
                "detail": str(exc),
            },
        ) from exc
    except (MarketDataFetchError, FundamentalsFetchError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "success": False,
                "error": "Upstream data provider failed",
                "detail": str(exc),
            },
        ) from exc
