"""
risk/growth_slowdown.py — Growth Slowdown Scenario.

Shock Assumptions:
- Topline growth stalls, slashing future revenue.
- Probability outlook shifts heavily toward neutral/bearish.
- Lowers forecast midpoint by 8%.
- Widens uncertainty band by 5% (less chaotic than a shock event, but still uncertain).
- Increases generic risk score by 10 pts.
"""

from typing import Dict, Any
from risk.stress_utils import (
    apply_percentage_shock,
    adjust_probability_distribution,
    widen_uncertainty_band,
    risk_score_adjustment
)

def apply_growth_slowdown_scenario(
    base_projection: float,
    base_risk: float,
    base_uncertainty: float,
    base_bullish: float,
    base_bearish: float
) -> Dict[str, Any]:
    
    # Math Shocks
    adj_proj = apply_percentage_shock(base_projection, -0.08)
    adj_uncert = widen_uncertainty_band(base_uncertainty, 0.05)
    adj_prob = adjust_probability_distribution(base_bullish, base_bearish, -15.0)
    adj_risk = risk_score_adjustment(base_risk, 10.0)

    # Explainability
    assumptions = [
        "Base projection discounted by 8% reflecting halved baseline revenue growth assumptions.",
        "Uncertainty band widened by 5% as growth models fail to meet consensus.",
        "Bullish probability penalized (-15 pts).",
        "Composite Risk Score increased by 10 pts due to stagnation vulnerability."
    ]
    
    impact = "A secular growth slowdown compresses valuation multiples as the company transitions from growth to maturity or decline. Forward return prospects are downgraded."
    
    return {
        "adjusted_projection": adj_proj,
        "adjusted_risk_score": adj_risk,
        "adjusted_uncertainty_percent": adj_uncert,
        "probability_shift": adj_prob,
        "impact_analysis": impact,
        "assumptions": assumptions
    }
