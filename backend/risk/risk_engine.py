"""
risk/risk_engine.py — Risk Intelligence Orchestrator.

Fetches data from Phase 5 (Fundamentals) and Phase 3 (Market Data),
then executes the risk assessment modules to blend a Composite Risk Score.
"""

from datetime import datetime, timezone
import logging
from typing import Tuple

from analytics.fundamentals_engine import _fetch_clean_financials, get_fundamental_snapshot, FundamentalsFetchError, InsufficientFundamentalsError
from analytics.service import get_market_snapshot, MarketDataFetchError, TickerNotFoundError, InsufficientDataError
from risk.cashflow_risk import assess_cashflow_risk
from risk.earnings_risk import assess_earnings_risk
from risk.hidden_risks import detect_hidden_risks
from risk.leverage_risk import assess_leverage_risk
from risk.liquidity_risk import assess_liquidity_risk
from risk.macro_sensitivity import estimate_macro_sensitivity
from schemas.risk import RiskResponse, RiskComponent, HiddenRisk
from utils.caching import market_cache

logger = logging.getLogger(__name__)


def generate_risk_profile(ticker: str) -> RiskResponse:
    """
    Generate a full Risk Intelligence profile by orchestrating Phase 3 and Phase 5
    data into the risk scoring modules.
    """
    ticker = ticker.upper().strip()
    cache_key = f"{ticker}:risk_profile"
    
    cached = market_cache.get(cache_key)
    if cached:
        return cached

    # 1. Fetch cross-phase dependencies
    # We let these raise their respective Exceptions up to the route if they fail
    market_stats = get_market_snapshot(ticker, period="1y")
    fundamentals_snap = get_fundamental_snapshot(ticker)
    
    # We also need raw arrays for volatility checks (earnings/cashflow)
    raw_financials = _fetch_clean_financials(ticker)

    # 2. Execute Risk Modules
    lev_risk = assess_leverage_risk(fundamentals_snap.model_dump())
    liq_risk = assess_liquidity_risk(fundamentals_snap.model_dump())
    ear_risk = assess_earnings_risk(raw_financials)
    cf_risk = assess_cashflow_risk(raw_financials)
    
    hidden = detect_hidden_risks(raw_financials)
    macro = estimate_macro_sensitivity(fundamentals_snap.model_dump(), market_stats.model_dump())
    
    # 3. Compute Composite Score
    # Base weights
    score = (
        (lev_risk["score"] * 0.25) +
        (liq_risk["score"] * 0.20) +
        (ear_risk["score"] * 0.20) +
        (cf_risk["score"] * 0.20)
    )
    
    # Hidden risks penalty (up to 15% of the total 100 base)
    if not hidden:
        # If no hidden risks, they get 0 penalty for the remaining 15%
        pass
    else:
        # Add a flat penalty per hidden risk, cap at 15
        penalty = min(15.0, len(hidden) * 7.5)
        score += penalty
        
    score = min(100.0, max(0.0, round(score, 1)))
    
    # Level
    if score < 35:
        level = "low"
    elif score <= 65:
        level = "moderate"
    else:
        level = "high"

    # Count years of data used globally
    revs = raw_financials.get("total_revenue", [])
    years_used = sum(1 for r in revs if r is not None)

    # 4. Build Response
    resp = RiskResponse(
        ticker=ticker,
        composite_risk_score=score,
        risk_level=level,
        leverage_risk=RiskComponent(**lev_risk),
        liquidity_risk=RiskComponent(**liq_risk),
        earnings_risk=RiskComponent(**ear_risk),
        cashflow_risk=RiskComponent(**cf_risk),
        hidden_risks=[HiddenRisk(**h) for h in hidden],
        macro_sensitivity_notes=macro,
        based_on_years=years_used,
        generated_at=datetime.now(timezone.utc)
    )
    
    market_cache.set(cache_key, resp, ttl=3600)
    return resp
