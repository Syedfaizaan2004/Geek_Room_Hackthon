"""
schemas/comparison.py — Pydantic models for Peer Comparison Engine (Phase 8).
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class ValuationComparison(BaseModel):
    pe_status: str
    pb_status: str
    ev_ebitda_status: str


class ProfitabilityComparison(BaseModel):
    roe_rank: int
    margin_position: str


class GrowthComparison(BaseModel):
    revenue_growth_position: str
    earnings_growth_position: str


class RiskComparison(BaseModel):
    relative_risk_rank: int
    safety_position: str


class ComparisonResponse(BaseModel):
    """
    Structured outcome of benchmarking a target company against its sector peers.
    Combines valuation, profitability, growth, and aggregate risk into a cohesive strategic profile.
    """
    ticker: str
    peers: List[str]
    
    valuation_comparison: ValuationComparison
    profitability_comparison: ProfitabilityComparison
    growth_comparison: GrowthComparison
    risk_comparison: RiskComparison
    
    financial_health_position: str
    
    strengths: List[str]
    weaknesses: List[str]
    strategic_summary: str
    
    generated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
