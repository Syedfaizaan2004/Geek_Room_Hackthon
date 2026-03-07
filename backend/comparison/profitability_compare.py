"""
comparison/profitability_compare.py - Predictable profitability ranking.

Compares net margin and ROE vs peers.
Returns relative rank and target vs peer-average context.
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


def compare_profitability(
    target_ticker: str,
    target_fundamentals: Dict[str, Any],
    peer_fundamentals: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    target_roe = _to_float(target_fundamentals.get("capital_efficiency", {}).get("roe"))
    target_margin = _to_float(target_fundamentals.get("profitability", {}).get("net_profit_margin"))

    all_roes: List[tuple[str, float]] = []
    if target_roe is not None:
        all_roes.append((target_ticker, target_roe))

    peer_roes: List[float] = []
    peer_margins: List[float] = []

    for peer_ticker, peer_fund in peer_fundamentals.items():
        peer_roe = _to_float(peer_fund.get("capital_efficiency", {}).get("roe"))
        if peer_roe is not None:
            all_roes.append((peer_ticker, peer_roe))
            peer_roes.append(peer_roe)

        peer_margin = _to_float(peer_fund.get("profitability", {}).get("net_profit_margin"))
        if peer_margin is not None:
            peer_margins.append(peer_margin)

    all_roes.sort(key=lambda item: item[1], reverse=True)

    roe_rank = -1
    for index, (ticker, _) in enumerate(all_roes):
        if ticker == target_ticker:
            roe_rank = index + 1
            break

    margin_pos = "in_line"
    avg_margin = _avg(peer_margins)
    if target_margin is not None and avg_margin is not None:
        if target_margin > avg_margin * 1.1:
            margin_pos = "above_average"
        elif target_margin < avg_margin * 0.9:
            margin_pos = "below_average"

    return {
        "roe_rank": roe_rank if roe_rank != -1 else len(peer_fundamentals) + 1,
        "margin_position": margin_pos,
        "target_roe": _round_or_none(target_roe),
        "peer_avg_roe": _round_or_none(_avg(peer_roes)),
        "target_net_margin": _round_or_none(target_margin),
        "peer_avg_net_margin": _round_or_none(avg_margin),
        "peer_count": len(peer_fundamentals),
    }
