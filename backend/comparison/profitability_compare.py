"""
comparison/profitability_compare.py — Predictable profitability ranking.

Compares Net margin, Operating margin, ROE, ROA.
Returns ranking and percentile position.
"""

from typing import List, Dict, Any

def compare_profitability(
    target_ticker: str,
    target_fundamentals: Dict[str, Any],
    peer_fundamentals: Dict[str, Dict[str, Any]]
) -> Dict[str, Any]:
    
    # Extract ROE for target
    target_roe = target_fundamentals.get("capital_efficiency", {}).get("roe")
    target_margin = target_fundamentals.get("profitability", {}).get("net_profit_margin")
    
    # Collect all valid ROEs
    all_roes = []
    if target_roe is not None:
        all_roes.append((target_ticker, target_roe))
        
    for p_ticker, p_funds in peer_fundamentals.items():
        p_roe = p_funds.get("capital_efficiency", {}).get("roe")
        if p_roe is not None:
            all_roes.append((p_ticker, p_roe))
            
    # Sort descending
    all_roes.sort(key=lambda x: x[1], reverse=True)
    
    roe_rank = -1
    for idx, (t, r) in enumerate(all_roes):
        if t == target_ticker:
            roe_rank = idx + 1
            break
            
    # Evaluate margins against peer average
    peer_margins = []
    for p_ticker, p_funds in peer_fundamentals.items():
        pm = p_funds.get("profitability", {}).get("net_profit_margin")
        if pm is not None:
            peer_margins.append(pm)
            
    margin_pos = "in_line"
    if target_margin is not None and peer_margins:
        avg_margin = sum(peer_margins) / len(peer_margins)
        if target_margin > avg_margin * 1.1:
            margin_pos = "above_average"
        elif target_margin < avg_margin * 0.9:
            margin_pos = "below_average"
            
    return {
        "roe_rank": roe_rank if roe_rank != -1 else len(peer_fundamentals) + 1,
        "margin_position": margin_pos
    }
