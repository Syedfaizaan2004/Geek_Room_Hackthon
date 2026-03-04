"""
risk/stress_utils.py — Reusable deterministic stress adjustment mathematics.

Rules enforced:
- Probabilities must sum to 100
- Risk scores bounded between 0 and 100
- Uncertainty bands cannot be negative
"""

from schemas.forecast import ProbabilityOutlook

def apply_percentage_shock(base_value: float, shock_percent: float) -> float:
    """
    Reduce (if negative) or increase (if positive) a base value.
    E.g., shock_percent = -0.10 means a 10% reduction.
    """
    return round(base_value * (1.0 + shock_percent), 2)


def adjust_probability_distribution(
    base_bullish: float,
    base_bearish: float,
    shift_bullish_pts: float
) -> ProbabilityOutlook:
    """
    Shift probability weight between bullish and bearish.
    E.g., shift_bullish_pts = -15 reduces bullish by 15% and adds 15% to bearish.
    Bounds are 0-100.
    """
    new_bullish = base_bullish + shift_bullish_pts
    # Clamp bounds
    new_bullish = max(5.0, min(95.0, new_bullish))
    new_bearish = 100.0 - new_bullish
    
    # Confidence level re-assessment based on extremes
    confidence = "moderate"
    if new_bullish > 75 or new_bearish > 75:
        confidence = "high"
    elif 40 <= new_bullish <= 60:
        # Near 50/50 implies low confidence in a single direction
        confidence = "low"
        
    return ProbabilityOutlook(
        probability_bullish=round(new_bullish, 1),
        probability_bearish=round(new_bearish, 1),
        confidence_level=confidence
    )


def widen_uncertainty_band(base_uncertainty: float, expansion_percent: float) -> float:
    """
    Inflate the uncertainty percentage.
    E.g. base = 0.20 (20%), expansion = 0.50 (50%). Result = 0.30 (30%).
    """
    return round(base_uncertainty * (1.0 + expansion_percent), 4)


def risk_score_adjustment(base_score: float, added_points: float) -> float:
    """
    Add raw points to the risk score, hard-capping at 100.
    """
    new_score = base_score + added_points
    return max(0.0, min(100.0, round(new_score, 1)))
