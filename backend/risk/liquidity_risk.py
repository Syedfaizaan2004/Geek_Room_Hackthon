"""
risk/liquidity_risk.py — Liquidity Risk Component.

High Risk (100 pts): Current Ratio < 1
Moderate Risk (50 pts): Current Ratio between 1 and 1.5
Low Risk (0 pts): Current Ratio > 1.5
"""

from typing import Dict, Any

def assess_liquidity_risk(fundamentals: Dict[str, Any]) -> Dict[str, Any]:
    liqty = fundamentals.get("liquidity", {})
    cr = liqty.get("current_ratio")

    if cr is None:
        return {
            "score": 50.0,
            "level": "moderate",
            "explanation": "Insufficient data to accurately assess short-term liquidity risk."
        }

    if cr < 1.0:
        return {
            "score": 100.0,
            "level": "high",
            "explanation": f"High risk: Current ratio of {cr:.2f}x indicates current liabilities exceed current assets, signaling potential short-term solvency issues."
        }
    elif cr <= 1.5:
        return {
            "score": 50.0,
            "level": "moderate",
            "explanation": f"Moderate risk: Current ratio of {cr:.2f}x shows adequate but lean short-term liquidity."
        }
    else:
        return {
            "score": 10.0,
            "level": "low",
            "explanation": f"Low risk: Strong current ratio of {cr:.2f}x covering short-term obligations comfortably."
        }
