"""
risk/recession.py — Recession Stress Scenario.

Shock Assumptions:
- Broad economic contraction.
- Lowers forecast midpoint by 10% (from baseline).
- Widens uncertainty band by 20%.
- Shifts probability outlook: -20 bullish pts.
- Increases generic risk score by 15 pts.
"""

from typing import Dict, Any
from risk.stress_utils import (
    apply_percentage_shock,
    adjust_probability_distribution,
    widen_uncertainty_band,
    risk_score_adjustment
)

def apply_recession_scenario(
    base_projection: float,
    base_risk: float,
    base_uncertainty: float,
    base_bullish: float,
    base_bearish: float
) -> Dict[str, Any]:
    
    # Math Shocks
    adj_proj = apply_percentage_shock(base_projection, -0.10)
    adj_uncert = widen_uncertainty_band(base_uncertainty, 0.20)
    adj_prob = adjust_probability_distribution(base_bullish, base_bearish, -20.0)
    adj_risk = risk_score_adjustment(base_risk, 15.0)

    # Explainability
    assumptions = [
        "Base projection discounted by 10% due to demand contraction.",
        "Uncertainty band widened by 20% to account for unpredictable earning misses.",
        "Bullish probability penalized heavily (-20 pts).",
        "Composite Risk Score increased by a flat 15 pts to reflect macro fragility."
    ]
    
    impact = "A recession scenario significantly degrades near-term visibility. The forecast midpoint is pulled down sharply while the risk profile becomes elevated, shifting the balance heavily toward bearish outcomes."
    
    return {
        "adjusted_projection": adj_proj,
        "adjusted_risk_score": adj_risk,
        "adjusted_uncertainty_percent": adj_uncert,
        "probability_shift": adj_prob,
        "impact_analysis": impact,
        "assumptions": assumptions
    }
