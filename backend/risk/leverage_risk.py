"""
risk/leverage_risk.py — Leverage Risk Component.

High Risk (100 pts): Debt/Equity > 2 OR Interest Coverage < 2
Moderate Risk (50 pts): Debt/Equity between 1 and 2
Low Risk (0 pts): DB < 1 and Coverage >= 2
"""

from typing import Optional, Dict, Any

def assess_leverage_risk(fundamentals: Dict[str, Any]) -> Dict[str, Any]:
    """Assess risk based on Leverage Metrics from Phase 5 Fundamental Engine."""
    
    lev = fundamentals.get("leverage", {})
    dte = lev.get("debt_to_equity")
    icr = lev.get("interest_coverage_ratio")
    
    # Missing data logic - err on the side of moderate/unknown
    if dte is None:
        return {
            "score": 50.0,
            "level": "moderate",
            "explanation": "Insufficient data to accurately assess leverage risk."
        }
        
    score = 0.0
    level = "low"
    explanation = "Leverage levels appear manageable."
    
    # Evaluate high risk conditions
    is_high_dte = (dte > 2.0)
    is_low_icr = (icr is not None and icr < 2.0)
    
    if is_high_dte or is_low_icr:
        score = 100.0
        level = "high"
        reasons = []
        if is_high_dte:
            reasons.append(f"Debt-to-Equity is elevated at {dte:.2f}x")
        if is_low_icr:
            reasons.append(f"Interest Coverage is weak at {icr:.2f}x")
        explanation = "High risk: " + " and ".join(reasons) + "."
        
    elif 1.0 <= dte <= 2.0:
        score = 50.0
        level = "moderate"
        explanation = f"Moderate risk: Debt-to-Equity is notable at {dte:.2f}x, but interest coverage remains adequate."
        
    else:
        score = 10.0
        level = "low"
        explanation = f"Low risk: Conservative Debt-to-Equity profile ({dte:.2f}x)."
        
    return {
        "score": score,
        "level": level,
        "explanation": explanation
    }
