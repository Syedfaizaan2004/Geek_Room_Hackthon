"""
analytics/fundamentals_engine.py — Financial Fundamentals Orchestrator.

Fetches data from `yfinance` (Income Statement, Balance Sheet, Cash Flow),
cleans and aligns it, passes it to the ratio modules, and aggregates a
final Financial Health Score.

Data Normalization:
yfinance structures financial statements as DataFrames where columns are dates.
This engine extracts the raw series, handles NaNs by coercing them to None,
and aligns them into lists where index 0 is TTM/Latest Year, index 1 is T-1, etc.
"""

from datetime import datetime, timezone
import logging
from typing import Dict, List, Optional, Tuple
import pandas as pd
import yfinance as yf

from analytics.cashflow import compute_cashflow_metrics
from analytics.growth import compute_growth_metrics
from analytics.leverage import compute_leverage_metrics
from analytics.liquidity import compute_liquidity_metrics
from analytics.profitability import compute_profitability_metrics
from schemas.fundamentals import (
    FundamentalResponse, ProfitabilityMetrics, GrowthMetrics,
    CapitalEfficiencyMetrics, CashFlowMetrics, LeverageMetrics, LiquidityMetrics
)
from utils.caching import market_cache

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------
class FundamentalsFetchError(Exception):
    pass


class InsufficientFundamentalsError(Exception):
    pass


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _extract_series(df: pd.DataFrame, possible_names: List[str], required_len: int = 1) -> List[Optional[float]]:
    """
    Look for a row in the dataframe matching one of the possible_names.
    Returns a list of floats (latest year first). Padded with None if missing.
    """
    if df is None or df.empty:
        return [None] * required_len

    # Standardize string matching (yfinance row indexes can vary slightly)
    df_lower = df.copy()
    df_lower.index = df_lower.index.astype(str).str.lower().str.strip()
    
    for name in possible_names:
        if name.lower() in df_lower.index:
            row = df_lower.loc[name.lower()]
            # If multiple rows match, take the first
            if isinstance(row, pd.DataFrame):
                row = row.iloc[0]
                
            # Convert to list, replace NaN with None
            vals = [float(v) if pd.notna(v) else None for v in row.values]
            # Ensure we return at least required_len elements
            while len(vals) < required_len:
                vals.append(None)
            return vals
            
    return [None] * required_len


def _fetch_clean_financials(ticker: str) -> Dict[str, List[Optional[float]]]:
    """
    Fetch IS, BS, and CF from yfinance and extract the essential line items.
    """
    tkr = yf.Ticker(ticker)
    
    try:
        # standard financials
        inc = tkr.financials
        bs = tkr.balance_sheet
        cf = tkr.cashflow
    except Exception as exc:
        raise FundamentalsFetchError(f"Failed to fetch financials for {ticker}: {exc}") from exc

    if inc.empty and bs.empty:
        raise InsufficientFundamentalsError(f"No fundamental data available for {ticker}.")

    # Required length for CAGR is 4
    n = max(len(inc.columns) if not inc.empty else 0, 4)

    # Dictionary of normalized lists (Index 0 = latest year)
    data = {
        "total_revenue": _extract_series(inc, ["Total Revenue", "Operating Revenue"], n),
        "gross_profit": _extract_series(inc, ["Gross Profit"], n),
        "operating_income": _extract_series(inc, ["Operating Income"], n),
        "net_income": _extract_series(inc, ["Net Income", "Net Income Common Stockholders"], n),
        "ebitda": _extract_series(inc, ["EBITDA", "Normalized EBITDA"], n),
        "ebit": _extract_series(inc, ["EBIT"], n),
        "interest_expense": _extract_series(inc, ["Interest Expense", "Interest Expense Non Operating", "Total Interest Expense"], n),
        
        "total_assets": _extract_series(bs, ["Total Assets"], n),
        "total_debt": _extract_series(bs, ["Total Debt"], n),
        "stockholders_equity": _extract_series(bs, ["Stockholders Equity"], n),
        "current_assets": _extract_series(bs, ["Current Assets"], n),
        "current_liabilities": _extract_series(bs, ["Current Liabilities"], n),
        "inventory": _extract_series(bs, ["Inventory"], n),
        
        "operating_cash_flow": _extract_series(cf, ["Operating Cash Flow", "Cash Flow From Continuing Operating Activities"], n),
        "capital_expenditure": _extract_series(cf, ["Capital Expenditure", "Purchase Of PPE"], n),
    }
    
    return data


# ---------------------------------------------------------------------------
# Scoring Model
# ---------------------------------------------------------------------------
def _score_metric(val: Optional[float], weak: float, strong: float, invert: bool = False) -> float:
    """
    Interpolate a value between weak (0 points) and strong (100 points).
    If invert is True, lower is better (e.g. Debt/Equity).
    """
    if val is None:
        return 50.0  # Missing data -> neutral score
        
    if invert:
        # e.g., D/E: weak=2.0, strong=0.5. If val=3.0 -> 0. If val=0.1 -> 100.
        if val >= weak: return 0.0
        if val <= strong: return 100.0
        return 100.0 * (weak - val) / (weak - strong)
    else:
        # e.g., ROE: weak=0.0, strong=0.2. If val=-0.1 -> 0. If val=0.3 -> 100.
        if val <= weak: return 0.0
        if val >= strong: return 100.0
        return 100.0 * (val - weak) / (strong - weak)


def _compute_health_score(prof: dict, gro: dict, cap: dict, lev: dict, liq: dict, cf: dict) -> Tuple[float, str]:
    """
    Calculate an aggregate 0-100 financial health score.
    Weights: Profitability (25%), Growth (20%), Leverage (20%), CashFlow (20%), Liquidity (15%)
    """
    s_prof = (
        _score_metric(prof["net_profit_margin"], 0.0, 0.20) * 0.5 + 
        _score_metric(prof["operating_margin"], 0.05, 0.25) * 0.5
    )
    
    s_gro = (
        _score_metric(gro["revenue_growth_yoy"], 0.0, 0.20) * 0.5 +
        _score_metric(gro["earnings_growth_yoy"], 0.0, 0.20) * 0.5
    )
    
    s_cap = _score_metric(cap["roe"], 0.05, 0.20)
    
    s_lev = (
        _score_metric(lev["debt_to_equity"], 1.5, 0.5, invert=True) * 0.6 +
        _score_metric(lev["interest_coverage_ratio"], 1.5, 5.0) * 0.4
    )
    
    s_liq = _score_metric(liq["current_ratio"], 1.0, 2.0)
    
    s_cf = _score_metric(cf["fcf_margin"], 0.0, 0.15)
    
    # Aggregate
    final_score = (
        (s_prof * 0.25) +
        (s_gro * 0.20) +
        (s_lev * 0.20) +
        ((s_cf * 0.7 + s_cap * 0.3) * 0.20) + # Split cashflow bucket
        (s_liq * 0.15)
    )
    
    classification = "unknown"
    if final_score < 40:
        classification = "weak"
    elif final_score <= 70:
        classification = "moderate"
    else:
        classification = "strong"
        
    return round(final_score, 1), classification


# ---------------------------------------------------------------------------
# Public Service API
# ---------------------------------------------------------------------------
def get_fundamental_snapshot(ticker: str) -> FundamentalResponse:
    """
    Fetch financials, normalize, calculate metrics, build Pydantic schema.
    """
    ticker = ticker.upper().strip()
    cache_key = f"{ticker}:fundamentals"
    
    cached = market_cache.get(cache_key)
    if cached:
        return cached

    financials = _fetch_clean_financials(ticker)
    
    # Execute modules
    prof = compute_profitability_metrics(financials)
    gro = compute_growth_metrics(financials)
    lev = compute_leverage_metrics(financials)
    liq = compute_liquidity_metrics(financials)
    cf, cap = compute_cashflow_metrics(financials)
    
    # Calculate overarching score
    score, cls = _compute_health_score(prof, gro, cap, lev, liq, cf)
    
    # Determine how many years of valid revenue data we actually had
    revs = financials.get("total_revenue", [])
    valid_years = sum(1 for r in revs if r is not None)
    
    resp = FundamentalResponse(
        ticker=ticker,
        profitability=ProfitabilityMetrics(**prof),
        growth=GrowthMetrics(**gro),
        capital_efficiency=CapitalEfficiencyMetrics(**cap),
        cash_flow=CashFlowMetrics(**cf),
        leverage=LeverageMetrics(**lev),
        liquidity=LiquidityMetrics(**liq),
        financial_health_score=score,
        classification=cls,
        data_years_used=valid_years,
        generated_at=datetime.now(timezone.utc)
    )
    
    market_cache.set(cache_key, resp, ttl=3600)  # Cache longer (1 hour) since filings update quarterly
    return resp
