"""
analytics/probability.py — Directional Probability Model for Forecasts.

Deterministic logic (no ML):
  Base probability: 50%
  Trend bias:      +15% (bullish) / -15% (bearish) / 0% (neutral)
  Volatility bias: -10% (high) / +5% (low) / 0% (moderate)

Returns:
  - probability_bullish: float
  - probability_bearish: float
  - confidence_level: str ("low", "moderate", "high")
"""

import logging

logger = logging.getLogger(__name__)


def compute_directional_probability(trend_direction: str, volatility_level: str) -> dict:
    """
    Compute bullish and bearish probabilities based on trend and volatility.
    
    Args:
        trend_direction: "bullish", "bearish", or "neutral"
        volatility_level: "low", "moderate", or "high"
        
    Returns:
        {
          "probability_bullish": float,
          "probability_bearish": float,
          "confidence_level": str
        }
    """
    
    # Base
    prob_bullish = 50.0
    
    # 1. Trend Adjustment
    if trend_direction == "bullish":
        prob_bullish += 15.0
    elif trend_direction == "bearish":
        prob_bullish -= 15.0
        
    # 2. Volatility Adjustment (confidence vs extreme moves)
    # High volatility reduces deterministic confidence (pulls toward 50/50).
    # Low volatility rewards the base trend.
    confidence_level = "moderate"
    
    if volatility_level == "high":
        confidence_level = "low"
        # Pull towards 50
        if prob_bullish > 50:
            prob_bullish -= 10.0
        elif prob_bullish < 50:
            prob_bullish += 10.0
            
    elif volatility_level == "low":
        confidence_level = "high"
        # Push further in trend direction
        if prob_bullish > 50:
            prob_bullish += 5.0
        elif prob_bullish < 50:
            prob_bullish -= 5.0

    # Ensure boundaries
    prob_bullish = max(10.0, min(90.0, prob_bullish))
    prob_bearish = 100.0 - prob_bullish
    
    return {
        "probability_bullish": round(prob_bullish, 1),
        "probability_bearish": round(prob_bearish, 1),
        "confidence_level": confidence_level
    }
