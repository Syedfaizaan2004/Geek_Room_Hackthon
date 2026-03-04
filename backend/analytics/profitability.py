"""
analytics/profitability.py — Profitability Margin Metrics.

Calculates:
  1. Net Profit Margin: Net Income / Total Revenue
  2. Operating Margin: Operating Income / Total Revenue
  3. Gross Margin: Gross Profit / Total Revenue
  4. EBITDA Margin: EBITDA / Total Revenue

Handles missing data and strictly checks for zero revenue to prevent ZeroDivisionError.
"""

from typing import Optional

def compute_profitability_metrics(financials: dict) -> dict:
    """
    Args:
        financials: Dict with 'total_revenue', 'net_income', 'operating_income', 
                    'gross_profit', 'ebitda'. (Index 0 is latest year).
    """
    revs = financials.get("total_revenue", [])
    
    # Needs valid latest revenue
    if not revs or revs[0] in (None, 0):
        return {
            "net_profit_margin": None,
            "operating_margin": None,
            "gross_margin": None,
            "ebitda_margin": None
        }
        
    rev_t = revs[0]
    
    # Safe extracts
    net_inc = financials.get("net_income", [None])[0]
    op_inc = financials.get("operating_income", [None])[0]
    gross_prof = financials.get("gross_profit", [None])[0]
    ebitda = financials.get("ebitda", [None])[0]
    
    npm = (net_inc / rev_t) if net_inc is not None else None
    opm = (op_inc / rev_t) if op_inc is not None else None
    gm  = (gross_prof / rev_t) if gross_prof is not None else None
    ebm = (ebitda / rev_t) if ebitda is not None else None
    
    return {
        "net_profit_margin": round(npm, 4) if npm is not None else None,
        "operating_margin": round(opm, 4) if opm is not None else None,
        "gross_margin": round(gm, 4) if gm is not None else None,
        "ebitda_margin": round(ebm, 4) if ebm is not None else None,
    }
