"""
risk/inflation.py — High Inflation Stress Scenario.

Shock Assumptions:
- Margin compression and rising input costs.
- Lowers forecast midpoint by 5% (less severe than strict recession).
- Widens uncertainty band by 10%.
- Shifts probability outlook: -10 bullish pts.
- Increases generic risk score by 10 pts.
"""

from typing import Dict, Any
from risk.stress_utils import (
    apply_percentage_shock,
    adjust_probability_distribution,
    widen_uncertainty_band,
    risk_score_adjustment
)

def apply_inflation_scenario(
    base_projection: float,
    base_risk: float,
    base_uncertainty: float,
    base_bullish: float,
    base_bearish: float
) -> Dict[str, Any]:
    
    # Math Shocks
    adj_proj = apply_percentage_shock(base_projection, -0.05)
    adj_uncert = widen_uncertainty_band(base_uncertainty, 0.10)
    adj_prob = adjust_probability_distribution(base_bullish, base_bearish, -10.0)
    adj_risk = risk_score_adjustment(base_risk, 10.0)

    # Explainability
    assumptions = [
        "Base projection discounted by 5% reflecting margin compression.",
        "Uncertainty band widened by 10% due to input cost volatility.",
        "Bullish probability penalized moderately (-10 pts).",
        "Composite Risk Score increased by 10 pts to reflect rising operating costs."
    ]
    
    impact = "High inflation compresses profit margins, slightly dampening the upside of the asset. The primary impact is increased volatility and a moderate drag on projected price appreciation."
    
    return {
        "adjusted_projection": adj_proj,
        "adjusted_risk_score": adj_risk,
        "adjusted_uncertainty_percent": adj_uncert,
        "probability_shift": adj_prob,
        "impact_analysis": impact,
        "assumptions": assumptions
    }
