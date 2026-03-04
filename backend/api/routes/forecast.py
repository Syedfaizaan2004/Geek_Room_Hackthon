"""
api/routes/forecast.py — Forecast Engine Endpoints (Phase 4).

Endpoints:
  GET /forecast/{ticker} — fetch deterministic forecast based on user prefs

Architecture:
  - Auth required via get_current_user
  - Loads user preferences (for time horizon) via crud layer
  - Fetches market snapshot (for prices, math, and volatility) via analytics.service
  - Calls forecast engine methods
  - Returns structured Response
"""

import logging
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from analytics.forecast_engine import generate_forecast
from analytics.market_data import MarketDataFetchError, TickerNotFoundError, InsufficientDataError
from analytics.probability import compute_directional_probability
from analytics.service import get_market_snapshot
from analytics.uncertainty import compute_uncertainty_band
from api.routes.auth import get_current_user
from db.session import get_db
from memory import crud
from memory.models import User
from schemas.forecast import ForecastResponse, ProbabilityOutlook, UncertaintyBand, ForecastBaseInputs

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/forecast", tags=["Forecast Engine"])


@router.get(
    "/{ticker}",
    response_model=ForecastResponse,
    summary="Get personalized forecast projection",
    responses={
        401: {"description": "Missing or invalid token"},
        404: {"description": "Ticker not found or delisted"},
        422: {"description": "Insufficient historical data"},
        503: {"description": "External data provider unavailable"},
    },
)
async def get_forecast(
    ticker: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> ForecastResponse:
    """
    Generate a personalised price forecast using deterministic volatility models.
    
    The forecast horizon is determined by the authenticated user's `time_horizon`
    preference (e.g. short_term -> 30 days, medium_term -> 90 days, 
    long_term -> 180 days).
    """
    ticker = ticker.upper().strip()
    
    try:
        # 1. Load User Preferences
        prefs = await crud.get_preferences_by_user_id(db, current_user.id)
        if not prefs:
            prefs = await crud.create_default_preferences(db, current_user.id)
            
        time_horizon = prefs.time_horizon
        
        # 2. Fetch Market Snapshot & Analytics
        # We request 1y period to ensure we have enough data for a stable 
        # annualised volatility metric.
        market_stats = get_market_snapshot(ticker, period="1y")
        
        volatility_percent = market_stats.volatility_percent
        volatility_level = market_stats.volatility_level
        trend_direction = market_stats.trend_direction
        current_price = market_stats.last_price
        
        # 3. Generate Core Projection (Bounds, Mid, Expected Move)
        proj = generate_forecast(
            current_price=current_price,
            volatility_percent=volatility_percent,
            trend_direction=trend_direction,
            time_horizon_pref=time_horizon
        )
        
        # 4. Generate Directional Probabilities
        prob = compute_directional_probability(
            trend_direction=trend_direction,
            volatility_level=volatility_level
        )
        
        # 5. Generate Uncertainty Bands
        uncert = compute_uncertainty_band(volatility_percent=volatility_percent)
        
        # 6. Build the Pydantic Response
        response = ForecastResponse(
            ticker=ticker,
            forecast_horizon_days=proj["forecast_horizon_days"],
            current_price=proj["current_price"],
            mid_projection=proj["mid_projection"],
            projected_upper_bound=proj["projected_upper_bound"],
            projected_lower_bound=proj["projected_lower_bound"],
            expected_move_percent=proj["expected_move_percent"],
            probability_outlook=ProbabilityOutlook(**prob),
            uncertainty=UncertaintyBand(**uncert),
            based_on=ForecastBaseInputs(
                volatility_percent=volatility_percent,
                trend_direction=trend_direction,
                time_horizon=time_horizon
            ),
            generated_at=datetime.now(timezone.utc)
        )
        
        return response
        
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
