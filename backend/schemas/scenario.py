"""
schemas/scenario.py — Pydantic models for the Scenario & Stress Engine (Phase 7).
"""

from datetime import datetime
from typing import List
from pydantic import BaseModel, ConfigDict
from schemas.forecast import ProbabilityOutlook


class ScenarioResponse(BaseModel):
    """
    Structured outcome of applying deterministic stress logic to 
    baseline fundamental, forecast, and risk data.
    """
    ticker: str
    scenario_type: str
    
    # Projection Shifts
    baseline_projection: float
    adjusted_projection: float
    
    # Risk Shifts
    baseline_risk_score: float
    adjusted_risk_score: float
    
    # Volatility / Uncertainty Shifts
    baseline_uncertainty_percent: float
    adjusted_uncertainty_percent: float
    
    # Probability Shifts
    probability_shift: ProbabilityOutlook
    
    # Explainability
    impact_analysis: str
    assumptions: List[str]
    
    generated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
