"""
schemas/market.py — Pydantic models for Market Data and Analytics.

Defines:
  - MarketSnapshotResponse (returned by GET /market/{ticker})
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class PerformanceMetrics(BaseModel):
    one_month: Optional[float]
    three_month: Optional[float]
    six_month: Optional[float]
    one_year: Optional[float]
    ytd: Optional[float]


class MovingAverages(BaseModel):
    sma_20: Optional[float]
    sma_50: Optional[float]
    sma_200: Optional[float]


class MarketSnapshotResponse(BaseModel):
    """
    Structured snapshot containing historical prices, moving averages,
    trend signals, and performance returns.
    """
    ticker: str
    last_price: float
    price_change_percent: float  # Latest daily price change %
    trend_direction: str         # "bullish", "bearish", or "neutral"
    volatility_percent: float    # Annualised volatility (e.g. 0.18 for 18%)
    volatility_level: str        # "low", "moderate", "high"
    
    performance: PerformanceMetrics
    moving_averages: MovingAverages
    
    data_points: int             # Number of historical days fetched
    last_updated: datetime       # Timestamp of the data freshness

    model_config = ConfigDict(from_attributes=True)
