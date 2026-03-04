"""
risk/hidden_risks.py — Hidden Structural Risk Detector.

Detects hidden structural risks:
- Revenue declining 3 years in a row
- Profit margin compression 2+ years
- Exploding debt profile (Debt soaring while equity remains flat/declining)
"""

from typing import Dict, Any, List

def detect_hidden_risks(raw_financials: Dict[str, list]) -> List[Dict[str, str]]:
    hidden_risks = []
    
    # 1. Revenue Declines
    revs = raw_financials.get("total_revenue", [])
    valid_revs = [r for r in revs if r is not None]
    if len(valid_revs) >= 4:
        # Array is [T, T-1, T-2, T-3]
        if valid_revs[0] < valid_revs[1] < valid_revs[2] < valid_revs[3]:
            hidden_risks.append({
                "risk_name": "Structural Growth Decline",
                "severity": "critical",
                "explanation": "Revenues have contracted for 3 consecutive years, heavily implying an evaporating core business."
            })
            
    # 2. Margin Compression
    op_inc = raw_financials.get("operating_income", [])
    if len(valid_revs) >= 3 and len(op_inc) >= 3:
        margins = []
        for i in range(3):
            if valid_revs[i] and op_inc[i] is not None:
                margins.append(op_inc[i] / valid_revs[i])
        
        # Array is [T, T-1, T-2]
        if len(margins) == 3 and margins[0] < margins[1] < margins[2]:
            hidden_risks.append({
                "risk_name": "Margin Compression",
                "severity": "high",
                "explanation": "Operating margins have continuously compressed over the past 3 cycles, suggesting loss of pricing power or rising structural costs."
            })
            
    # 3. Exploding Debt Trend
    debt = raw_financials.get("total_debt", [])
    if len(debt) >= 3 and debt[0] is not None and debt[1] is not None and debt[2] is not None:
        if debt[2] > 0 and debt[0] > (debt[2] * 1.5) and debt[0] > debt[1] > debt[2]:
            hidden_risks.append({
                "risk_name": "Rapid Debt Accumulation",
                "severity": "high",
                "explanation": f"Total debt has grown rapidly (>50%) over the last 3 years, increasing financial fragility."
            })
            
    return hidden_risks
