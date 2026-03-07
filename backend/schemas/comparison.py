"""
schemas/comparison.py — Pydantic models for Peer Comparison Engine (Phase 8).
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ValuationComparison(BaseModel):
    pe_status: str
    pb_status: str
    ev_ebitda_status: str
    target_pe: Optional[float] = None
    peer_avg_pe: Optional[float] = None
    target_pb: Optional[float] = None
    peer_avg_pb: Optional[float] = None
    target_ev_ebitda: Optional[float] = None
    peer_avg_ev_ebitda: Optional[float] = None


class ProfitabilityComparison(BaseModel):
    roe_rank: int
    margin_position: str
    target_roe: Optional[float] = None
    peer_avg_roe: Optional[float] = None
    target_net_margin: Optional[float] = None
    peer_avg_net_margin: Optional[float] = None
    peer_count: int = 0


class GrowthComparison(BaseModel):
    revenue_growth_position: str
    earnings_growth_position: str
    target_revenue_growth: Optional[float] = None
    peer_avg_revenue_growth: Optional[float] = None
    target_earnings_growth: Optional[float] = None
    peer_avg_earnings_growth: Optional[float] = None


class RiskComparison(BaseModel):
    relative_risk_rank: int
    safety_position: str
    target_risk_score: Optional[float] = None
    peer_avg_risk_score: Optional[float] = None
    universe_size: int = 0


class PeerSnapshot(BaseModel):
    ticker: str
    financial_health_score: Optional[float] = None
    financial_health_classification: str = "unknown"
    composite_risk_score: Optional[float] = None
    roe: Optional[float] = None
    net_profit_margin: Optional[float] = None
    revenue_growth_yoy: Optional[float] = None
    earnings_growth_yoy: Optional[float] = None


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
    comparison_universe_size: int = 0
    target_snapshot: Optional[PeerSnapshot] = None
    peer_snapshots: List[PeerSnapshot] = Field(default_factory=list)
    
    generated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
