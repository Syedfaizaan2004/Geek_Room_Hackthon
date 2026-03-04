"""
api/routes/fundamentals.py — Fundamentals Engine Endpoints (Phase 5).

Provides fundamental analysis ratios and health scoring.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from analytics.fundamentals_engine import (
    get_fundamental_snapshot, FundamentalsFetchError, InsufficientFundamentalsError
)
from api.routes.auth import get_current_user
from memory.models import User
from schemas.fundamentals import FundamentalResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/fundamentals", tags=["Fundamentals Engine"])


@router.get(
    "/{ticker}",
    response_model=FundamentalResponse,
    summary="Get comprehensive fundamental analysis and ratios",
    responses={
        401: {"description": "Missing or invalid token"},
        404: {"description": "Ticker not found or no financial statements available"},
        503: {"description": "Upstream data provider failed"},
    },
)
async def get_fundamentals(
    ticker: str,
    current_user: Annotated[User, Depends(get_current_user)],
) -> FundamentalResponse:
    """
    Fetch core financial ratios (profitability, growth, leverage, liquidity) 
    and a unified Financial Health Score for a given ticker.
    
    Requires: `Authorization: Bearer <token>`
    """
    try:
        # Service layer orchestrates fetch, calculation, and cache
        snapshot = get_fundamental_snapshot(ticker)
        return snapshot
        
    except InsufficientFundamentalsError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": "No fundamental data available",
                "detail": str(exc),
            },
        ) from exc
    except FundamentalsFetchError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "success": False,
                "error": "Data fetch failed",
                "detail": str(exc),
            },
        ) from exc
