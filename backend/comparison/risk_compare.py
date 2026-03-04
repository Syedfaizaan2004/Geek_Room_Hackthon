"""
comparison/risk_compare.py — Risk benchmarking.

Compares Composite Risk score amongst peers.
Lower score is better.
"""

from typing import List, Dict, Any

def compare_risk(
    target_ticker: str,
    target_risk: Dict[str, Any],
    peer_risks: Dict[str, Dict[str, Any]]
) -> Dict[str, Any]:
    
    target_score = target_risk.get("composite_risk_score")
    
    all_scores = []
    if target_score is not None:
        all_scores.append((target_ticker, target_score))
        
    for pt, pr in peer_risks.items():
        s = pr.get("composite_risk_score")
        if s is not None:
            all_scores.append((pt, s))
            
    # Sort ascending (lower risk = rank 1)
    all_scores.sort(key=lambda x: x[1])
    
    rank = -1
    for idx, (t, s) in enumerate(all_scores):
        if t == target_ticker:
            rank = idx + 1
            break
            
    # Safety position
    safety = "average"
    if rank == 1 and len(all_scores) > 1:
        safety = "safest_in_class"
    elif rank > 0 and rank == len(all_scores):
        safety = "highest_risk"
        
    return {
        "relative_risk_rank": rank if rank != -1 else len(peer_risks) + 1,
        "safety_position": safety
    }
