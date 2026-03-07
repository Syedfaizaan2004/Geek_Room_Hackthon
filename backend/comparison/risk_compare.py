"""
comparison/risk_compare.py - Risk benchmarking.

Compares composite risk score among peers.
Lower score is better.
"""

from typing import Any, Dict, List, Optional
import math


def _to_float(value: Any) -> Optional[float]:
    try:
        if value is None:
            return None
        numeric = float(value)
        if not math.isfinite(numeric):
            return None
        return numeric
    except (TypeError, ValueError):
        return None


def _avg(values: List[float]) -> Optional[float]:
    return sum(values) / len(values) if values else None


def _round_or_none(value: Optional[float], digits: int = 2) -> Optional[float]:
    if value is None:
        return None
    return round(value, digits)


def compare_risk(
    target_ticker: str,
    target_risk: Dict[str, Any],
    peer_risks: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    target_score = _to_float(target_risk.get("composite_risk_score"))

    all_scores: List[tuple[str, float]] = []
    if target_score is not None:
        all_scores.append((target_ticker, target_score))

    peer_scores: List[float] = []
    for peer_ticker, peer_risk in peer_risks.items():
        score = _to_float(peer_risk.get("composite_risk_score"))
        if score is not None:
            all_scores.append((peer_ticker, score))
            peer_scores.append(score)

    # Lower risk is better.
    all_scores.sort(key=lambda item: item[1])

    rank = -1
    for index, (ticker, _) in enumerate(all_scores):
        if ticker == target_ticker:
            rank = index + 1
            break

    safety = "average"
    if rank == 1 and len(all_scores) > 1:
        safety = "safest_in_class"
    elif rank > 0 and rank == len(all_scores):
        safety = "highest_risk"

    return {
        "relative_risk_rank": rank if rank != -1 else len(peer_risks) + 1,
        "safety_position": safety,
        "target_risk_score": _round_or_none(target_score),
        "peer_avg_risk_score": _round_or_none(_avg(peer_scores)),
        "universe_size": len(all_scores),
    }
