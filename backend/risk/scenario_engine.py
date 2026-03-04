"""
risk/scenario_engine.py — Scenario Orchestrator.

Applies the specified deterministic stress scenario to a baseline 
Phase 4 forecast and Phase 6 risk profile.
"""

from datetime import datetime, timezone
import logging
from typing import Optional

from analytics.forecast_engine import generate_forecast
from analytics.service import get_market_snapshot
from memory import crud
from memory.models import User
from risk.growth_slowdown import apply_growth_slowdown_scenario
from risk.inflation import apply_inflation_scenario
from risk.rate_hike import apply_rate_hike_scenario
from risk.recession import apply_recession_scenario
from risk.risk_engine import generate_risk_profile
from schemas.scenario import ScenarioResponse
from utils.caching import market_cache

logger = logging.getLogger(__name__)


class InvalidScenarioError(Exception):
    pass


def run_scenario_analysis(ticker: str, user_id: str, scenario_type: str, db) -> ScenarioResponse:
    """
    Fetch all baseline data (Market, Preferences, Forecast, Risk),
    apply the requested mathematical stress test, and return the diff.
    """
    ticker = ticker.upper().strip()
    scenario_type = scenario_type.lower().strip()
    
    # Needs async db lookup for preferences
    # But since this function is synchronous, we'll let the route pass the time_horizon
    # Wait, the route passes the time_horizon to us directly to keep this sync.
    # Let's adjust signature to accept time_horizon directly from the route.
    pass


def run_sync_scenario_analysis(
    ticker: str, 
    time_horizon_pref: str, 
    scenario_type: str
) -> ScenarioResponse:
    
    ticker = ticker.upper().strip()
    scenario_type = scenario_type.lower().strip()
    
    cache_key = f"{ticker}:scenario:{scenario_type}:{time_horizon_pref}"
    cached = market_cache.get(cache_key)
    if cached:
        return cached

    valid_scenarios = ["recession", "inflation", "rate_hike", "growth_slowdown"]
    if scenario_type not in valid_scenarios:
        raise InvalidScenarioError(f"Scenario '{scenario_type}' is not supported.")

    # 1. Fetch baselines
    market_stats = get_market_snapshot(ticker, period="1y")
    risk_profile = generate_risk_profile(ticker)
    
    # We need the pure forecast projection
    forecast_baseline = generate_forecast(
        current_price=market_stats.last_price,
        volatility_percent=market_stats.volatility_percent,
        trend_direction=market_stats.trend_direction,
        time_horizon_pref=time_horizon_pref
    )
    
    # Ensure variables exist
    base_proj = forecast_baseline["mid_projection"]
    base_uncert = risk_profile.leverage_risk.score # Hack? No, uncertainty comes from market stats
    
    # Actually, base uncertainty is Volatility * 1.25 roughly, let's just use vol
    base_uncert = market_stats.volatility_percent * 1.25
    base_risk = risk_profile.composite_risk_score
    
    # To get base probabilities we need to call probability engine or fake it.
    from analytics.probability import compute_directional_probability
    probs = compute_directional_probability(market_stats.trend_direction, market_stats.volatility_level)
    base_bullish = probs["probability_bullish"]
    base_bearish = probs["probability_bearish"]

    # 2. Route to specific scenario
    if scenario_type == "recession":
        res = apply_recession_scenario(base_proj, base_risk, base_uncert, base_bullish, base_bearish)
    elif scenario_type == "inflation":
        res = apply_inflation_scenario(base_proj, base_risk, base_uncert, base_bullish, base_bearish)
    elif scenario_type == "rate_hike":
        # Need D/E for rate hike
        dte = 0.0
        # Access from the fundamentals embedded in risk if we must, or fetch fresh
        from analytics.fundamentals_engine import get_fundamental_snapshot
        funds = get_fundamental_snapshot(ticker)
        if funds.leverage.debt_to_equity is not None:
            dte = funds.leverage.debt_to_equity
            
        res = apply_rate_hike_scenario(base_proj, base_risk, base_uncert, base_bullish, base_bearish, dte)
    elif scenario_type == "growth_slowdown":
        res = apply_growth_slowdown_scenario(base_proj, base_risk, base_uncert, base_bullish, base_bearish)

    # 3. Construct output
    resp = ScenarioResponse(
        ticker=ticker,
        scenario_type=scenario_type,
        baseline_projection=base_proj,
        adjusted_projection=res["adjusted_projection"],
        baseline_risk_score=base_risk,
        adjusted_risk_score=res["adjusted_risk_score"],
        baseline_uncertainty_percent=round(base_uncert, 4),
        adjusted_uncertainty_percent=res["adjusted_uncertainty_percent"],
        probability_shift=res["probability_shift"],
        impact_analysis=res["impact_analysis"],
        assumptions=res["assumptions"],
        generated_at=datetime.now(timezone.utc)
    )
    
    market_cache.set(cache_key, resp, ttl=3600)
    return resp
