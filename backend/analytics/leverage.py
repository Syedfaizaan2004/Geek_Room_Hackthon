"""
analytics/leverage.py — Financial Leverage & Solvency Metrics.

Calculates:
  1. Debt to Equity: Total Debt / Shareholder Equity
  2. Debt to Assets: Total Debt / Total Assets
  3. Interest Coverage Ratio: EBIT / Interest Expense

Classification:
  - Low leverage:  D/E < 0.5
  - Moderate:      0.5 <= D/E <= 1.5
  - High:          D/E > 1.5
"""

from typing import Optional, Tuple

def compute_leverage_metrics(financials: dict) -> dict:
    total_debt = financials.get("total_debt", [None])[0]
    equity = financials.get("stockholders_equity", [None])[0]
    assets = financials.get("total_assets", [None])[0]
    ebit = financials.get("ebit", [None])[0]
    # yfinance often records interest expense as negative or positive randomly; usually positive in 'interest_expense'
    int_exp = financials.get("interest_expense", [None])[0]
    
    # Debt to Equity
    dte = None
    if total_debt is not None and equity is not None and equity > 0:
        dte = total_debt / equity
        
    # Debt to Assets
    dta = None
    if total_debt is not None and assets is not None and assets > 0:
        dta = total_debt / assets
        
    # Interest Coverage
    icr = None
    if ebit is not None and int_exp is not None and int_exp != 0:
        icr = ebit / abs(int_exp)
        
    # Classification based on D/E
    classification = "unknown"
    if dte is not None:
        if dte < 0.5:
            classification = "low"
        elif dte <= 1.5:
            classification = "moderate"
        else:
            classification = "high"
            
    return {
        "debt_to_equity": round(dte, 4) if dte is not None else None,
        "debt_to_assets": round(dta, 4) if dta is not None else None,
        "interest_coverage_ratio": round(icr, 4) if icr is not None else None,
        "classification": classification,
    }
