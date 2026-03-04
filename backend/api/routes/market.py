"""
api/routes/market.py — Market data endpoints (Phase 3).

Endpoints:
  GET /market/{ticker} — fetch historical data and analytics snapshot

Architecture:
  - Validates ticker and period inputs
  - Defers all business logic to analytics.service
  - Maps domain exceptions to standard HTTP status codes
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from analytics.market_data import MarketDataFetchError, TickerNotFoundError, InsufficientDataError
from analytics.service import get_market_snapshot
from schemas.market import MarketSnapshotResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/market", tags=["Market Data"])


# ---------------------------------------------------------------------------
# GET /market/{ticker}
# ---------------------------------------------------------------------------
@router.get(
    "/{ticker}",
    response_model=MarketSnapshotResponse,
    summary="Get market snapshot and analytics",
    responses={
        404: {"description": "Ticker not found or delisted"},
        422: {"description": "Insufficient historical data"},
        503: {"description": "External data provider unavailable"},
    },
)
async def get_market_data(
    ticker: str,
    period: Annotated[
        str,
        Query(
            description="Time horizon (1mo, 3mo, 6mo, 1y, 2y, 5y, max)", 
            examples=["1y", "6mo"]
        )
    ] = "1y",
) -> MarketSnapshotResponse:
    """
    Fetch comprehensive market intelligence for a specific ticker.
    
    Returns:
    - Latest closing price & daily change
    - Volatility metrics (annualised)
    - Moving averages (20, 50, 200)
    - Trend direction (bullish/bearish/neutral)
    - Performance returns (1mo, 3mo, 6mo, 1y, YTD)
    """
    ticker = ticker.upper().strip()
    
    # We defer the actual execution to the service layer.
    # Note: get_market_snapshot is synchronous (yfinance is blocking). 
    # For a high-load production API, we would run this in a threadpool 
    # via fastapi.concurrency.run_in_threadpool. For this phase, direct call 
    # is acceptable since we have in-memory caching.
    
    try:
        # Service orchestrates fetch, computation, and caching
        snapshot = get_market_snapshot(ticker, period=period)
        return snapshot
        
    except TickerNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": "Ticker not found",
                "detail": str(exc),
            },
        ) from exc
        
    except InsufficientDataError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "success": False,
                "error": "Insufficient data",
                "detail": str(exc),
            },
        ) from exc
        
    except MarketDataFetchError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "success": False,
                "error": "Data provider unavailable",
                "detail": str(exc),
            },
        ) from exc
