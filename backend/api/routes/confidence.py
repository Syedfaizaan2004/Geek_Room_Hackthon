"""
api/routes/confidence.py — Standalone Confidence & Transparency endpoint (Phase 11).

GET /api/v1/confidence/{ticker}

Runs all analytical engines, then generates the full confidence transparency report.
No LangGraph needed — runs synchronously against the same engine layer.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException

from api.routes.auth import get_current_user
from memory.models import User
from schemas.confidence import ConfidenceResponse
from utils.confidence_engine import generate_confidence_report

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/confidence/{ticker}", response_model=ConfidenceResponse)
async def get_confidence_report(
    ticker: str,
    current_user: User = Depends(get_current_user),
):
    """
    Generate a full Confidence & Transparency report for a given ticker.

    Returns:
    - Overall confidence score (0–100)
    - Confidence level (low / moderate / high)
    - Data completeness score
    - Detected contradictions between engine outputs
    - Uncertainty level and driving factors
    - Full assumption disclosure
    """
    ticker = ticker.upper().strip()
    logger.info(f"Confidence report request: {ticker} (user: {current_user.unique_user_id})")

    try:
        # Fetch all available components — failures are non-fatal
        market, forecast, fundamentals, risk, scenario, comparison = {}, {}, {}, {}, {}, {}

        try:
            from analytics.service import get_market_snapshot
            snap = get_market_snapshot(ticker, period="1y")
            market = snap.model_dump()
        except Exception as e:
            logger.warning(f"Market data failed for {ticker}: {e}")

        try:
            from analytics.forecast_engine import generate_forecast
            if market:
                fc = generate_forecast(
                    current_price=market["last_price"],
                    volatility_percent=market["volatility_percent"],
                    trend_direction=market["trend_direction"],
                    time_horizon_pref="medium_term"
                )
                forecast = fc.model_dump() if hasattr(fc, "model_dump") else fc
        except Exception as e:
            logger.warning(f"Forecast failed for {ticker}: {e}")

        try:
            from analytics.fundamentals_engine import get_fundamental_snapshot
            f = get_fundamental_snapshot(ticker)
            fundamentals = f.model_dump()
        except Exception as e:
            logger.warning(f"Fundamentals failed for {ticker}: {e}")

        try:
            from risk.risk_engine import generate_risk_profile
            r = generate_risk_profile(ticker)
            risk = r.model_dump()
        except Exception as e:
            logger.warning(f"Risk profile failed for {ticker}: {e}")

        try:
            from risk.scenario_engine import run_sync_scenario_analysis
            s = run_sync_scenario_analysis(ticker, "medium_term", scenario_type="recession")
            scenario = s.model_dump()
        except Exception as e:
            logger.warning(f"Scenario failed for {ticker}: {e}")

        try:
            from comparison.comparison_engine import run_peer_comparison
            c = run_peer_comparison(ticker)
            comparison = c.model_dump()
        except Exception as e:
            logger.warning(f"Peer comparison failed for {ticker}: {e}")

        return generate_confidence_report(
            ticker=ticker,
            market=market,
            forecast=forecast,
            fundamentals=fundamentals,
            risk=risk,
            scenario=scenario,
            comparison=comparison,
        )

    except Exception as e:
        logger.error(f"Confidence report failed for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=f"Confidence report failed: {str(e)}")
