"""
risk/cashflow_risk.py — Cash Flow Instability Risk.

Calculates FCF historically.
High risk: 2+ negative FCF years or extreme volatility.
Moderate: Fluctuation but mostly positive.
Low: Stable positive FCF.
"""

import numpy as np
from typing import Dict, Any

def assess_cashflow_risk(raw_financials: Dict[str, list]) -> Dict[str, Any]:
    ocf = raw_financials.get("operating_cash_flow", [])
    capex = raw_financials.get("capital_expenditure", [])
    
    fcfs = []
    # yfinance structures most recent first [T, T-1, T-2, ...]
    for i in range(min(len(ocf), len(capex))):
        o = ocf[i]
        c = capex[i]
        if o is not None and c is not None:
            # yfinance capex is often negative
            f = o - abs(c)
            fcfs.append(f)
            
    if len(fcfs) < 3:
        return {
            "score": 50.0,
            "level": "moderate",
            "explanation": "Insufficient cash flow history to assess risk."
        }
        
    negative_fcf_years = sum(1 for f in fcfs if f < 0)
    
    chron_fcfs = fcfs[::-1]
    # Volatility of purely positive/negative absolutes is tricky, better to use coefficient of variation
    mean_fcf = np.mean(chron_fcfs)
    std_fcf = np.std(chron_fcfs)
    
    cv = 0.0
    if mean_fcf != 0:
        cv = abs(std_fcf / mean_fcf)
        
    if negative_fcf_years >= 2 or mean_fcf < 0:
        return {
            "score": 100.0,
            "level": "high",
            "explanation": f"High risk: Generated negative Free Cash Flow in {negative_fcf_years} of the last {len(fcfs)} years."
        }
    elif cv > 1.0 or negative_fcf_years == 1:
        return {
            "score": 60.0,
            "level": "moderate",
            "explanation": "Moderate risk: Free Cash Flow is positive on average but historically volatile or had a negative year."
        }
    else:
        return {
            "score": 10.0,
            "level": "low",
            "explanation": "Low risk: Company generates consistent and stable positive Free Cash Flow."
        }
