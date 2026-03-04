"""
analytics/uncertainty.py — Uncertainty Band Classification.

Formula:
  uncertainty_range_percent = volatility_percent * 1.25

Classification:
  - Tight (<20%)
  - Moderate (20–40%)
  - Wide (>40%)
"""

import logging

logger = logging.getLogger(__name__)


def compute_uncertainty_band(volatility_percent: float) -> dict:
    """
    Calculate the uncertainty percentage and classify the band.
    
    Args:
        volatility_percent: Annualised volatility (e.g. 0.185 for 18.5%)
        
    Returns:
        {
          "uncertainty_percent": float,
          "classification": str
        }
    """
    # 1.25 expansion factor of base volatility
    uncertainty_percent = volatility_percent * 1.25
    uncertainty_percent = round(uncertainty_percent, 4)
    
    # Classify
    classification = "moderate"
    if uncertainty_percent < 0.20:
        classification = "tight"
    elif uncertainty_percent > 0.40:
        classification = "wide"
        
    return {
        "uncertainty_percent": uncertainty_percent,
        "classification": classification
    }
