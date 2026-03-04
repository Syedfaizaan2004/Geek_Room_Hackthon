"""
schemas/forecast.py — Pydantic models for the Forecast & Outlook Engine (Phase 4).
"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ProbabilityOutlook(BaseModel):
    probability_bullish: float
    probability_bearish: float
    confidence_level: str


class UncertaintyBand(BaseModel):
    uncertainty_percent: float
    classification: str


class ForecastBaseInputs(BaseModel):
    volatility_percent: float
    trend_direction: str
    time_horizon: str


class ForecastResponse(BaseModel):
    """
    Structured response containing deterministic price projections,
    directional probabilities, and uncertainty bands scaled to
    the user's preferred time horizon.
    """
    ticker: str
    forecast_horizon_days: int
    current_price: float
    mid_projection: float
    projected_upper_bound: float
    projected_lower_bound: float
    expected_move_percent: float
    
    probability_outlook: ProbabilityOutlook
    uncertainty: UncertaintyBand
    based_on: ForecastBaseInputs
    generated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
