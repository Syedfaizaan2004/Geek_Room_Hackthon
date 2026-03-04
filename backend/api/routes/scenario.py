"""
api/routes/scenario.py — Scenario Stress Testing Endpoints (Phase 7).
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from analytics.fundamentals_engine import FundamentalsFetchError, InsufficientFundamentalsError
from analytics.service import MarketDataFetchError, TickerNotFoundError, InsufficientDataError
from api.routes.auth import get_current_user
from db.session import get_db
from memory import crud
from memory.models import User
from risk.scenario_engine import run_sync_scenario_analysis, InvalidScenarioError
from schemas.scenario import ScenarioResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scenario", tags=["Scenario Engine"])


@router.get(
    "/{ticker}",
    response_model=ScenarioResponse,
    summary="Get stress-tested forecast and risk metrics",
    responses={
        400: {"description": "Invalid scenario type"},
        401: {"description": "Missing or invalid token"},
        404: {"description": "Ticker not found or missing foundational data"},
        422: {"description": "Insufficient history to calculate risk"},
        503: {"description": "External data provider unavailable"},
    },
)
async def get_scenario_analysis(
    ticker: str,
    current_user: Annotated[User, Depends(get_current_user)],
    type: Annotated[str, Query(description="recession | inflation | rate_hike | growth_slowdown")],
    db: AsyncSession = Depends(get_db),
) -> ScenarioResponse:
    """
    Run a deterministic macroeconomic stress test against a stock's baseline forecast and risk profile.
    
    Available scenarios:
    - `recession`
    - `inflation`
    - `rate_hike`
    - `growth_slowdown`
    
    Requires: `Authorization: Bearer <token>`
    """
    try:
        # Load Preferences for forecast horizon baseline
        prefs = await crud.get_preferences_by_user_id(db, current_user.id)
        if not prefs:
            prefs = await crud.create_default_preferences(db, current_user.id)
            
        time_horizon = prefs.time_horizon
        
        # Execute Stress Test
        response = run_sync_scenario_analysis(ticker, time_horizon, type)
        return response
        
    except InvalidScenarioError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": "Invalid Scenario Type",
                "detail": str(exc),
            },
        ) from exc
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
