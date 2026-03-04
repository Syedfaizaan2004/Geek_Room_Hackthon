"""
risk/rate_hike.py — Interest Rate Hike Scenario.

Shock Assumptions:
- Higher debt servicing costs.
- Leverage-sensitive companies (D/E > 1.5) are impacted heavily.
- Low-leverage companies see minimal direct impact.
"""

from typing import Dict, Any
from risk.stress_utils import (
    apply_percentage_shock,
    adjust_probability_distribution,
    widen_uncertainty_band,
    risk_score_adjustment
)

def apply_rate_hike_scenario(
    base_projection: float,
    base_risk: float,
    base_uncertainty: float,
    base_bullish: float,
    base_bearish: float,
    debt_to_equity: float
) -> Dict[str, Any]:
    
    # Dynamic penalty based on leverage
    is_highly_levered = (debt_to_equity > 1.5)
    
    if is_highly_levered:
        proj_shock = -0.15
        risk_shock = 25.0
        prob_shock = -15.0
        uncert_shock = 0.15
        impact = "With a high Debt-to-Equity ratio, the company is highly sensitive to borrowing costs. Refinancing risk dominates the outlook, severely cutting the forecast and inflating the composite risk profile."
    else:
        proj_shock = -0.02
        risk_shock = 5.0
        prob_shock = -2.0
        uncert_shock = 0.05
        impact = "Due to a conservative balance sheet (low leverage), the direct fundamental impact of a rate hike is subdued. The asset represents a relative safe haven against yield curve shifts."

    # Math Shocks
    adj_proj = apply_percentage_shock(base_projection, proj_shock)
    adj_uncert = widen_uncertainty_band(base_uncertainty, uncert_shock)
    adj_prob = adjust_probability_distribution(base_bullish, base_bearish, prob_shock)
    adj_risk = risk_score_adjustment(base_risk, risk_shock)

    # Explainability
    assumptions = [
        f"Leverage factor checked (D/E = {debt_to_equity:.2f}x).",
        f"Base projection discounted by {abs(proj_shock*100):.1f}%.",
        f"Uncertainty band widened by {uncert_shock*100:.1f}%.",
        f"Bullish probability penalized ({prob_shock} pts).",
        f"Composite Risk Score increased by {risk_shock} pts to reflect debt servicing strain."
    ]
    
    return {
        "adjusted_projection": adj_proj,
        "adjusted_risk_score": adj_risk,
        "adjusted_uncertainty_percent": adj_uncert,
        "probability_shift": adj_prob,
        "impact_analysis": impact,
        "assumptions": assumptions
    }
