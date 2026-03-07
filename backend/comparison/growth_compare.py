"""
comparison/growth_compare.py - Growth benchmarking.

Compares revenue and earnings growth vs peers.
Returns above_average, in_line, below_average plus target/peer-average values.
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


def _round_or_none(value: Optional[float], digits: int = 4) -> Optional[float]:
    if value is None:
        return None
    return round(value, digits)


def compare_growth(
    target_ticker: str,
    target_fundamentals: Dict[str, Any],
    peer_fundamentals: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    del target_ticker  # kept for function signature parity

    target_rev_growth = _to_float(target_fundamentals.get("growth", {}).get("revenue_growth_yoy"))
    target_earn_growth = _to_float(target_fundamentals.get("growth", {}).get("earnings_growth_yoy"))

    peer_rev_growths: List[float] = []
    peer_earn_growths: List[float] = []

    for _, peer_fund in peer_fundamentals.items():
        rev_growth = _to_float(peer_fund.get("growth", {}).get("revenue_growth_yoy"))
        earn_growth = _to_float(peer_fund.get("growth", {}).get("earnings_growth_yoy"))
        if rev_growth is not None:
            peer_rev_growths.append(rev_growth)
        if earn_growth is not None:
            peer_earn_growths.append(earn_growth)

    def eval_position(target_val: Optional[float], peer_vals: List[float]) -> str:
        if target_val is None or not peer_vals:
            return "unknown"

        peer_avg = sum(peer_vals) / len(peer_vals)
        if target_val > peer_avg + 0.02:
            return "above_average"
        if target_val < peer_avg - 0.02:
            return "below_average"
        return "in_line"

    avg_rev_growth = _avg(peer_rev_growths)
    avg_earn_growth = _avg(peer_earn_growths)

    return {
        "revenue_growth_position": eval_position(target_rev_growth, peer_rev_growths),
        "earnings_growth_position": eval_position(target_earn_growth, peer_earn_growths),
        "target_revenue_growth": _round_or_none(target_rev_growth),
        "peer_avg_revenue_growth": _round_or_none(avg_rev_growth),
        "target_earnings_growth": _round_or_none(target_earn_growth),
        "peer_avg_earnings_growth": _round_or_none(avg_earn_growth),
    }
