"""
schemas/fundamentals.py — Pydantic models for Financial Fundamentals (Phase 5).

Defines the structured output for fundamental analysis, returning clean,
nullable ratios and a top-level financial health score.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class ProfitabilityMetrics(BaseModel):
    net_profit_margin: Optional[float]
    operating_margin: Optional[float]
    gross_margin: Optional[float]
    ebitda_margin: Optional[float]


class GrowthMetrics(BaseModel):
    revenue_growth_yoy: Optional[float]
    revenue_cagr_3y: Optional[float]
    earnings_growth_yoy: Optional[float]


class CapitalEfficiencyMetrics(BaseModel):
    roe: Optional[float]    # Return on Equity
    roa: Optional[float]    # Return on Assets
    roic: Optional[float]   # Return on Invested Capital


class CashFlowMetrics(BaseModel):
    free_cash_flow: Optional[float]       # Absolute value (currency)
    fcf_margin: Optional[float]           # FCF / Revenue
    fcf_growth_yoy: Optional[float]


class LeverageMetrics(BaseModel):
    debt_to_equity: Optional[float]
    debt_to_assets: Optional[float]
    interest_coverage_ratio: Optional[float]
    classification: str     # "low", "moderate", "high", or "unknown"


class LiquidityMetrics(BaseModel):
    current_ratio: Optional[float]
    quick_ratio: Optional[float]
    classification: str     # "weak", "adequate", "strong", or "unknown"


class FundamentalResponse(BaseModel):
    """
    Comprehensive financial health snapshot based on recent SEC filings
    (via yfinance). All constituent ratios handle missing data gracefully.
    """
    ticker: str
    
    profitability: ProfitabilityMetrics
    growth: GrowthMetrics
    capital_efficiency: CapitalEfficiencyMetrics
    cash_flow: CashFlowMetrics
    leverage: LeverageMetrics
    liquidity: LiquidityMetrics
    
    financial_health_score: Optional[float]  # 0 to 100
    classification: str                      # "strong" | "moderate" | "weak" | "unknown"
    data_years_used: int                     # How many annual reports went into the calculation
    
    generated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
