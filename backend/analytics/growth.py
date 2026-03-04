"""
analytics/growth.py — Financial Growth Metrics.

Calculates:
  1. YoY Revenue Growth: (Rev_t - Rev_t-1) / |Rev_t-1|
  2. 3-Year Revenue CAGR: (Rev_t / Rev_t-3)^(1/3) - 1
  3. YoY Earnings Growth: (NetInc_t - NetInc_t-1) / |NetInc_t-1|

Rule: Denominators use absolute values to handle negative earnings properly
(e.g., going from -100 to +50 is a +150% growth).
"""

import math
from typing import Optional

def compute_growth_metrics(financials: dict) -> dict:
    """
    Args:
        financials: Dictionary containing organized financial data arrays
                    (index 0 is newest, index 1 is previous year, etc.)
    """
    # Defensive extraction
    revs = financials.get("total_revenue", [])
    incomes = financials.get("net_income", [])
    
    # 1. YoY Revenue Growth
    rev_yoy = None
    if len(revs) >= 2 and revs[1] and revs[1] != 0:
        rev_yoy = (revs[0] - revs[1]) / abs(revs[1])
        
    # 2. 3-Year Revenue CAGR (requires at least 4 years of data: t, t-1, t-2, t-3)
    cagr_3y = None
    if len(revs) >= 4 and revs[3] and revs[3] > 0 and revs[0] is not None and revs[0] > 0:
        cagr_3y = math.pow(revs[0] / revs[3], 1.0 / 3.0) - 1.0
        
    # 3. YoY Earnings Growth
    earn_yoy = None
    if len(incomes) >= 2 and incomes[1] and incomes[1] != 0:
        earn_yoy = (incomes[0] - incomes[1]) / abs(incomes[1])
        
    return {
        "revenue_growth_yoy": round(rev_yoy, 4) if rev_yoy is not None else None,
        "revenue_cagr_3y": round(cagr_3y, 4) if cagr_3y is not None else None,
        "earnings_growth_yoy": round(earn_yoy, 4) if earn_yoy is not None else None,
    }
