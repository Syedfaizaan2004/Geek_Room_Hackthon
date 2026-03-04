"""
api/routes/insights.py — Standalone Insight Synthesis endpoint (Phase 10).

Calls the deterministic synthesizer directly using the lighter-weight engine
calls, so it doesn't require a full LangGraph invocation.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException

from api.routes.auth import get_current_user
from memory.models import User
from schemas.insights import InsightResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/insights/{ticker}", response_model=InsightResponse)
async def get_insights(ticker: str, current_user: User = Depends(get_current_user)):
    """
    Generate a deterministic investment memo for a ticker.
    Synthesizes: executive summary, strengths, risks, bull/bear theses,
    plain-language summary. All rule-based, no LLM.
    """
    ticker = ticker.upper().strip()
    logger.info(f"Synthesizing insights for {ticker} (user: {current_user.unique_user_id})")

    try:
        # Build a minimal AgentState-compatible dict from direct engine calls
        from analytics.service import get_market_snapshot
        from analytics.forecast_engine import generate_forecast
        from analytics.fundamentals_engine import get_fundamental_snapshot
        from risk.risk_engine import generate_risk_profile
        from memory.crud import get_preferences_by_user_id
        from db.session import get_db

        market_snap = None
        forecast_data = None
        funds_data = None
        risk_data = None
        prefs_data = {"risk_tolerance": "moderate", "time_horizon": "medium_term"}

        try:
            market_snap = get_market_snapshot(ticker, period="1y")
        except Exception as e:
            logger.warning(f"Market data unavailable for {ticker}: {e}")

        if market_snap:
            try:
                fc = generate_forecast(
                    current_price=market_snap.last_price,
                    volatility_percent=market_snap.volatility_percent,
                    trend_direction=market_snap.trend_direction,
                    time_horizon_pref="medium_term"
                )
                forecast_data = fc
            except Exception as e:
                logger.warning(f"Forecast unavailable: {e}")

        try:
            funds_data = get_fundamental_snapshot(ticker)
        except Exception as e:
            logger.warning(f"Fundamentals unavailable: {e}")

        try:
            risk_data = generate_risk_profile(ticker)
        except Exception as e:
            logger.warning(f"Risk profile unavailable: {e}")

        # Build a mock AgentState for the synthesizer
        state = {
            "ticker": ticker,
            "market_snapshot": market_snap.model_dump() if market_snap else {},
            "forecast": forecast_data if isinstance(forecast_data, dict) else (forecast_data.model_dump() if forecast_data else {}),
            "fundamentals": funds_data.model_dump() if funds_data else {},
            "risk": risk_data.model_dump() if risk_data else {},
            "comparison": {},
            "scenario": {},
            "preferences": prefs_data,
            "errors": [],
            "result": None,
        }

        from agents.synthesizer import synthesize_insights
        insight = synthesize_insights(state)
        return insight

    except Exception as e:
        logger.error(f"Insight synthesis failed for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=f"Insight synthesis failed: {str(e)}")
