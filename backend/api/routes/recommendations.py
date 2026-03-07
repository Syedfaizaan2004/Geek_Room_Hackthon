"""
api/routes/recommendations.py - Phase 15 Personalization API.

GET /recommendations/{ticker}
Requires authentication.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.routes.auth import get_current_user
from db.session import get_db
from memory import crud
from memory.models import User
from memory.recommendation_engine import build_recommendation_payload
from schemas.recommendations import RecommendationResponse

router = APIRouter(prefix="/recommendations", tags=["Personalization"])
logger = logging.getLogger(__name__)


@router.get("/{ticker}", response_model=RecommendationResponse)
async def get_recommendations(
    ticker: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate personalized smart recommendations for a given ticker.

    Recommendations include:
    - Next analysis actions (deterministic rule-based)
    - Similar companies (vector search + deterministic fallback)
    - Watchlist suggestion (preference-matched)
    - Behavioral profile (pattern analysis)
    - Memory reminders (prior research recap)
    """
    ticker = ticker.strip().upper()

    # Load user preferences from DB
    prefs_obj = await crud.get_preferences_by_user_id(db, current_user.id)
    preferences = {}
    if prefs_obj:
        preferences = {
            # Recommendation engine expects `risk_profile`; preferences model stores `risk_tolerance`.
            "risk_profile": prefs_obj.risk_tolerance,
            "time_horizon": prefs_obj.time_horizon,
            "preferred_kpis": prefs_obj.preferred_kpis or [],
            "preferred_sectors": prefs_obj.preferred_sectors or [],
        }

    # Retrieve prior vector memory for this user
    memory_recall = []
    try:
        from vector_store.qdrant_client import qdrant_wrapper
        from vector_store.memory_service import retrieve_similar_insights

        if qdrant_wrapper.is_healthy and qdrant_wrapper.client:
            results = []
            for key in (str(current_user.id), current_user.unique_user_id):
                results = await retrieve_similar_insights(
                    client=qdrant_wrapper.client,
                    query_text=ticker,
                    user_id=key,
                    top_k=10,
                )
                if results:
                    break
            memory_recall = [
                r.model_dump() if hasattr(r, "model_dump") else r.__dict__
                for r in results
            ]
    except Exception as e:
        logger.warning("Memory recall failed for recommendations (non-fatal): %s", e)

    # Optional live engine context for stronger action quality.
    # Every step is non-fatal so endpoint behavior remains stable.
    market: dict = {}
    forecast: dict = {}
    fundamentals: dict = {}
    risk: dict = {}

    try:
        from analytics.service import get_market_snapshot

        snap = get_market_snapshot(ticker, period="1y")
        market = snap.model_dump() if hasattr(snap, "model_dump") else {}
    except Exception as e:
        logger.warning("Market snapshot unavailable for recommendations (%s): %s", ticker, e)

    try:
        from analytics.forecast_engine import generate_forecast

        if market:
            forecast = generate_forecast(
                current_price=float(market.get("last_price", 0.0)),
                volatility_percent=float(market.get("volatility_percent", 0.0)),
                trend_direction=str(market.get("trend_direction", "neutral")),
                time_horizon_pref=str(preferences.get("time_horizon", "medium_term")),
            )
    except Exception as e:
        logger.warning("Forecast unavailable for recommendations (%s): %s", ticker, e)

    try:
        from analytics.fundamentals_engine import get_fundamental_snapshot

        f = get_fundamental_snapshot(ticker)
        fundamentals = f.model_dump() if hasattr(f, "model_dump") else {}
    except Exception as e:
        logger.warning("Fundamentals unavailable for recommendations (%s): %s", ticker, e)

    try:
        from risk.risk_engine import generate_risk_profile

        r = generate_risk_profile(ticker)
        risk = r.model_dump() if hasattr(r, "model_dump") else {}
    except Exception as e:
        logger.warning("Risk profile unavailable for recommendations (%s): %s", ticker, e)

    try:
        payload = await build_recommendation_payload(
            ticker=ticker,
            mode="on_demand",
            user_id=str(current_user.id),
            preferences=preferences,
            risk=risk or None,
            forecast=forecast or None,
            fundamentals=fundamentals or None,
            memory_recall=memory_recall,
        )
        return RecommendationResponse(**payload)
    except Exception as e:
        logger.error("Recommendation generation failed: %s", e)
        raise HTTPException(
            status_code=500, detail="Failed to generate recommendations."
        )
