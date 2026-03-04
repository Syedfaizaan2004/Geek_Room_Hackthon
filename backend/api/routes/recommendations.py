"""
api/routes/recommendations.py — Phase 15 Personalization API.

GET /recommendations/{ticker}
Requires authentication.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException

from api.routes.auth import get_current_user
from memory.models import User
from db.session import get_db
from memory import crud
from memory.recommendation_engine import build_recommendation_payload
from schemas.recommendations import RecommendationResponse
from sqlalchemy.ext.asyncio import AsyncSession

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
    - Similar companies (Qdrant semantic search)
    - Watchlist suggestion (preference-matched)
    - Behavioral profile (pattern analysis)
    - Memory reminders (prior research recap)

    All logic is deterministic and explainable.
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

    # Retrieve prior Qdrant memory for this user
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
            memory_recall = [r.__dict__ for r in results]
    except Exception as e:
        logger.warning(f"Memory recall failed for recommendations (non-fatal): {e}")

    try:
        payload = await build_recommendation_payload(
            ticker=ticker,
            mode="on_demand",
            user_id=str(current_user.id),
            preferences=preferences,
            risk=None,         # No live engine data — relies on memory + prefs
            forecast=None,
            fundamentals=None,
            memory_recall=memory_recall,
        )
        return RecommendationResponse(**payload)

    except Exception as e:
        logger.error(f"Recommendation generation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate recommendations.")
