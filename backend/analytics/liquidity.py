"""
analytics/liquidity.py — Short-term Liquidity Metrics.

Calculates:
  1. Current Ratio: Current Assets / Current Liabilities
  2. Quick Ratio: (Current Assets - Inventory) / Current Liabilities

Classification:
  - Weak:     Current Ratio < 1.0
  - Adequate: 1.0 <= Current Ratio <= 2.0
  - Strong:   Current Ratio > 2.0
"""

from typing import Optional

def compute_liquidity_metrics(financials: dict) -> dict:
    curr_assets = financials.get("current_assets", [None])[0]
    curr_liab = financials.get("current_liabilities", [None])[0]
    inventory = financials.get("inventory", [None])[0]
    
    # Defaults
    cr = None
    qr = None
    classification = "unknown"
    
    if curr_liab is not None and curr_liab > 0:
        if curr_assets is not None:
            cr = curr_assets / curr_liab
            
            # Quick Ratio needs inventory (or assumes 0 if missing but assets exist)
            inv_val = inventory if inventory is not None else 0.0
            qr = (curr_assets - inv_val) / curr_liab

    if cr is not None:
        if cr < 1.0:
            classification = "weak"
        elif cr <= 2.0:
            classification = "adequate"
        else:
            classification = "strong"
            
    return {
        "current_ratio": round(cr, 4) if cr is not None else None,
        "quick_ratio": round(qr, 4) if qr is not None else None,
        "classification": classification,
    }
