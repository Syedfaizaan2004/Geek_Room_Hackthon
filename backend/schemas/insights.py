"""
schemas/insights.py — Pydantic models for Insight Synthesis (Phase 10).
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict

class KeyMetricsSnapshot(BaseModel):
    financial_health_score: float
    risk_score: float
    probability_bullish: float
    probability_bearish: float

class InsightResponse(BaseModel):
    """
    Structured, deterministic, plain-language insights generated from raw engine outputs.
    """
    ticker: str
    
    executive_summary: str
    strengths: List[str]
    risks: List[str]
    bull_thesis: List[str]
    bear_thesis: List[str]
    
    plain_language_summary: str
    
    key_metrics_snapshot: Optional[KeyMetricsSnapshot] = None
    
    generated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
