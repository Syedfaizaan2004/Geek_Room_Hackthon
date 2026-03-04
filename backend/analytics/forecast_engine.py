"""
analytics/forecast_engine.py — Volatility-based Forecasting Engine.

Deterministic Projection Logic:
  1. Horizon Mapping:
     short_term  -> 30 trading days
     medium_term -> 90 trading days
     long_term   -> 180 trading days
     (defaults to 90 if no preference provided)

  2. Expected Move (Volatility Scaling):
     expected_move = current_price * volatility * sqrt(horizon / 252)

  3. Trend Bias:
     Bullish trend shifts the midpoint UP by 0.5 * expected_move.
     Bearish trend shifts the midpoint DOWN by 0.5 * expected_move.
     Neutral leaves midpoint at current_price.

  4. Projection Bounds:
     Upper Bound = Mid + expected_move
     Lower Bound = Mid - expected_move
"""

import logging
from typing import Tuple

logger = logging.getLogger(__name__)

# Constants
_TRADING_DAYS_PER_YEAR = 252


def get_horizon_days(time_horizon: str) -> int:
    """Map the user's string preference to discrete trading days."""
    if time_horizon == "short_term":
        return 30
    if time_horizon == "long_term":
        return 180
    
    # default / medium_term
    return 90


def compute_expected_move(
    current_price: float,
    volatility_percent: float,
    horizon_days: int
) -> float:
    """
    Calculate the statistical expected move over a timeframe using the
    square root of time rule.
    """
    if current_price <= 0 or horizon_days <= 0:
        return 0.0
        
    import math
    time_factor = math.sqrt(horizon_days / _TRADING_DAYS_PER_YEAR)
    expected_move = current_price * volatility_percent * time_factor
    return expected_move


def apply_directional_bias(
    current_price: float,
    expected_move: float,
    trend_direction: str
) -> float:
    """
    Shift the projection centerpoint (mid) based on the current market trend.
    Shift amplitude is 50% of the statistical expected move.
    """
    bias_factor = 0.0
    
    if trend_direction == "bullish":
        bias_factor = 0.5 * expected_move
    elif trend_direction == "bearish":
        bias_factor = -0.5 * expected_move
        
    mid_projection = current_price + bias_factor
    return mid_projection


def generate_forecast(
    current_price: float,
    volatility_percent: float,
    trend_direction: str,
    time_horizon_pref: str
) -> dict:
    """
    Orchestrate the projection bounds calculation.
    
    Returns:
      {
        "forecast_horizon_days": int,
        "current_price": float,
        "mid_projection": float,
        "projected_upper_bound": float,
        "projected_lower_bound": float,
        "expected_move_percent": float
      }
    """
    horizon_days = get_horizon_days(time_horizon_pref)
    
    # 1. Scale Volatility
    expected_move = compute_expected_move(
        current_price, 
        volatility_percent, 
        horizon_days
    )
    
    # 2. Bias to Trend
    mid_projection = apply_directional_bias(
        current_price, 
        expected_move, 
        trend_direction
    )
    
    # 3. Create Bounds
    upper = mid_projection + expected_move
    lower = mid_projection - expected_move
    
    # 4. Compute percentage
    # (expected_move / current_price)
    expected_move_percent = (expected_move / current_price) if current_price > 0 else 0.0
    
    return {
        "forecast_horizon_days": horizon_days,
        "current_price": round(current_price, 2),
        "mid_projection": round(mid_projection, 2),
        "projected_upper_bound": round(upper, 2),
        "projected_lower_bound": max(0.0, round(lower, 2)), # price floor is 0
        "expected_move_percent": round(expected_move_percent, 4)
    }
