"""
analytics/cashflow.py — Cash Flow and Capital Efficiency Metrics.

Calculates Cash Flow:
  1. Free Cash Flow (FCF) = Operating Cash Flow - Capital Expenditure
  2. FCF Margin = FCF / Total Revenue
  3. FCF Growth YoY = (FCF_t - FCF_{t-1}) / |FCF_{t-1}|

Calculates Capital Efficiency:
  1. ROE = Net Income / Shareholder Equity
  2. ROA = Net Income / Total Assets
  3. ROIC = NOPAT / Invested Capital (Simplified: EBIT*(1-0.21) / (Debt + Equity))
"""

from typing import Tuple

def compute_cashflow_metrics(financials: dict) -> Tuple[dict, dict]:
    """
    Returns (cash_flow_dict, capital_efficiency_dict).
    """
    # ── Cash Flow ──
    ocf = financials.get("operating_cash_flow", [])
    capex = financials.get("capital_expenditure", [])
    revs = financials.get("total_revenue", [None])
    
    fcf_t0 = None
    fcf_t1 = None
    
    # yfinance capex is often negative (cash outflow), so we ADD it if it's negative, 
    # or subtract if it's positive. Safest is: OCF - abs(CapEx)
    if len(ocf) > 0 and ocf[0] is not None and len(capex) > 0 and capex[0] is not None:
        fcf_t0 = ocf[0] - abs(capex[0])
        
    if len(ocf) > 1 and ocf[1] is not None and len(capex) > 1 and capex[1] is not None:
        fcf_t1 = ocf[1] - abs(capex[1])
        
    fcf_margin = None
    if fcf_t0 is not None and revs and revs[0] and revs[0] > 0:
        fcf_margin = fcf_t0 / revs[0]
        
    fcf_growth = None
    if fcf_t0 is not None and fcf_t1 is not None and fcf_t1 != 0:
        fcf_growth = (fcf_t0 - fcf_t1) / abs(fcf_t1)
        
    cash_flow = {
        "free_cash_flow": round(fcf_t0, 2) if fcf_t0 is not None else None,
        "fcf_margin": round(fcf_margin, 4) if fcf_margin is not None else None,
        "fcf_growth_yoy": round(fcf_growth, 4) if fcf_growth is not None else None,
    }
    
    # ── Capital Efficiency ──
    net_inc = financials.get("net_income", [None])[0]
    equity = financials.get("stockholders_equity", [None])[0]
    assets = financials.get("total_assets", [None])[0]
    ebit = financials.get("ebit", [None])[0]
    debt = financials.get("total_debt", [None])[0]
    
    roe = None
    if net_inc is not None and equity is not None and equity > 0:
        roe = net_inc / equity
        
    roa = None
    if net_inc is not None and assets is not None and assets > 0:
        roa = net_inc / assets
        
    roic = None
    if ebit is not None and debt is not None and equity is not None:
        invested_capital = debt + equity
        if invested_capital > 0:
            # Assumed 21% corp tax rate for NOPAT
            nopat = ebit * (1 - 0.21)
            roic = nopat / invested_capital
            
    capital_eff = {
        "roe": round(roe, 4) if roe is not None else None,
        "roa": round(roa, 4) if roa is not None else None,
        "roic": round(roic, 4) if roic is not None else None,
    }
    
    return cash_flow, capital_eff
