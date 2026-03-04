"""
risk/earnings_risk.py — Earnings Volatility Risk Component.

Requires raw financial metrics (not just the FundamentalResponse).
High risk (100 pts): Negative earnings in 2+ years OR std dev of YoY growth > 30%
Moderate (50 pts): Std dev between 15% and 30%
Low (0 pts): Std dev < 15%
"""

import numpy as np
from typing import Dict, Any

def assess_earnings_risk(raw_financials: Dict[str, list]) -> Dict[str, Any]:
    incomes = raw_financials.get("net_income", [])
    
    # Clean data
    valid_incomes = [i for i in incomes if i is not None]
    
    if len(valid_incomes) < 3:
        return {
            "score": 50.0,
            "level": "moderate",
            "explanation": "Insufficient historical earnings data to measure volatility accurately."
        }
        
    # Count negative years
    negative_years = sum(1 for i in valid_incomes if i < 0)
    
    # Calculate YoY growth array
    # list is recent to oldest, so reverse for chronological growth
    chron_incomes = valid_incomes[::-1]
    growths = []
    for i in range(1, len(chron_incomes)):
        prev = chron_incomes[i-1]
        curr = chron_incomes[i]
        if prev != 0:
            growths.append((curr - prev) / abs(prev))
            
    volatility = 0.0
    if len(growths) > 1:
        volatility = float(np.std(growths))
        
    if negative_years >= 2 or volatility > 0.30:
        reasons = []
        if negative_years >= 2:
            reasons.append(f"{negative_years} years of negative net income")
        if volatility > 0.30:
            reasons.append(f"high earnings volatility ({(volatility*100):.1f}%)")
            
        return {
            "score": 90.0 if negative_years < 2 else 100.0,
            "level": "high",
            "explanation": "High risk: " + " and ".join(reasons) + "."
        }
    elif volatility > 0.15:
        return {
            "score": 50.0,
            "level": "moderate",
            "explanation": f"Moderate risk: Earnings volatility is notable at {(volatility*100):.1f}%."
        }
    else:
        return {
            "score": 15.0,
            "level": "low",
            "explanation": f"Low risk: Earnings history shows stable growth with low volatility ({(volatility*100):.1f}%)."
        }
