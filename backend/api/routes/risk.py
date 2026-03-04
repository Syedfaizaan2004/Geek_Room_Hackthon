"""
api/routes/risk.py — Risk Engine Endpoints (Phase 6).
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from analytics.fundamentals_engine import FundamentalsFetchError, InsufficientFundamentalsError
from analytics.service import MarketDataFetchError, TickerNotFoundError, InsufficientDataError
from api.routes.auth import get_current_user
from memory.models import User
from risk.risk_engine import generate_risk_profile
from schemas.risk import RiskResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/risk", tags=["Risk Engine"])


@router.get(
    "/{ticker}",
    response_model=RiskResponse,
    summary="Get unified risk intelligence profile",
    responses={
        401: {"description": "Missing or invalid token"},
        404: {"description": "Ticker not found or missing foundational data"},
        422: {"description": "Insufficient history to calculate risk"},
        503: {"description": "External data provider unavailable"},
    },
)
async def get_risk_profile(
    ticker: str,
    current_user: Annotated[User, Depends(get_current_user)],
) -> RiskResponse:
    """
    Generate a granular Risk Intelligence report for a given ticker.
    Synthesizes leverage, liquidity, cash flow stability, and earnings volatility.
    
    Requires: `Authorization: Bearer <token>`
    """
    try:
        # Cross-phase service layer orchestrator
        profile = generate_risk_profile(ticker)
        return profile
        
    except (TickerNotFoundError, InsufficientFundamentalsError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": "Data missing or ticker not found",
                "detail": str(exc),
            },
        ) from exc
    except InsufficientDataError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "success": False,
                "error": "Insufficient history for volatility math",
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
