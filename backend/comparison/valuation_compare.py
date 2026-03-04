"""
comparison/valuation_compare.py — Valuation benchmarking.

Compares P/E, P/B, and EV/EBITDA against a peer group average.
Labels as undervalued, fairly_valued, or overvalued.
"""

from typing import List, Dict, Any
from analytics.fundamentals_engine import get_fundamental_snapshot
from analytics.service import get_market_snapshot

def compare_valuation(target_ticker: str, peer_tickers: List[str]) -> Dict[str, str]:
    """
    Returns valuation status compared to peer average.
    Values > 15% above peer avg = overvalued
    Values < 15% below peer avg = undervalued
    Else = fairly_valued
    """
    import yfinance as yf
    
    # helper
    def fetch_val_metrics(t: str) -> Dict[str, float]:
        info = yf.Ticker(t).info
        return {
            "pe": info.get("trailingPE"),
            "pb": info.get("priceToBook"),
            "ev_ebitda": info.get("enterpriseToEbitda")
        }
        
    target_val = fetch_val_metrics(target_ticker)
    
    peer_pes = []
    peer_pbs = []
    peer_evs = []
    
    for pt in peer_tickers:
        v = fetch_val_metrics(pt)
        if v["pe"] is not None: peer_pes.append(v["pe"])
        if v["pb"] is not None: peer_pbs.append(v["pb"])
        if v["ev_ebitda"] is not None: peer_evs.append(v["ev_ebitda"])
        
    def avg(lst: List[float]) -> float:
        return sum(lst) / len(lst) if lst else None
        
    def determine_status(target: float, peer_avg: float) -> str:
        if target is None or peer_avg is None:
            return "unknown"
        if target > (peer_avg * 1.15):
            return "overvalued"
        elif target < (peer_avg * 0.85):
            return "undervalued"
        return "fairly_valued"
        
    avg_pe = avg(peer_pes)
    avg_pb = avg(peer_pbs)
    avg_ev = avg(peer_evs)
    
    return {
        "pe_status": determine_status(target_val["pe"], avg_pe),
        "pb_status": determine_status(target_val["pb"], avg_pb),
        "ev_ebitda_status": determine_status(target_val["ev_ebitda"], avg_ev),
    }
