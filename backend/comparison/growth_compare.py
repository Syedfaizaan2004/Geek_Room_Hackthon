"""
comparison/growth_compare.py — Growth benchmarking.

Compares Revenue and Earnings growth vs peers.
Returns above_average, in_line, below_average.
"""

from typing import List, Dict, Any

def compare_growth(
    target_ticker: str,
    target_fundamentals: Dict[str, Any],
    peer_fundamentals: Dict[str, Dict[str, Any]]
) -> Dict[str, Any]:
    
    target_rev_growth = target_fundamentals.get("growth", {}).get("revenue_growth_yoy")
    target_earn_growth = target_fundamentals.get("growth", {}).get("earnings_growth_yoy")
    
    peer_rev_growths = []
    peer_earn_growths = []
    
    for pt, pf in peer_fundamentals.items():
        rg = pf.get("growth", {}).get("revenue_growth_yoy")
        eg = pf.get("growth", {}).get("earnings_growth_yoy")
        if rg is not None: peer_rev_growths.append(rg)
        if eg is not None: peer_earn_growths.append(eg)
        
    def eval_position(target_val: float, peer_vals: List[float]) -> str:
        if target_val is None or not peer_vals:
            return "unknown"
            
        avg = sum(peer_vals) / len(peer_vals)
        # Using a flat absolute threshold for growth (+/- 2% absolute or 10% relative)
        # We will use 10% relative diff
        if target_val > avg + 0.02: # +2% absolute growth edge is significant
            return "above_average"
        elif target_val < avg - 0.02:
            return "below_average"
        return "in_line"
        
    return {
        "revenue_growth_position": eval_position(target_rev_growth, peer_rev_growths),
        "earnings_growth_position": eval_position(target_earn_growth, peer_earn_growths)
    }
