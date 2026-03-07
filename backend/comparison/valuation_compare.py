"""
comparison/valuation_compare.py - Valuation benchmarking.

Compares P/E, P/B, and EV/EBITDA against a peer-group average.
Labels as undervalued, fairly_valued, or overvalued.
"""

from typing import Dict, List, Optional
import math


def _to_float(value: object) -> Optional[float]:
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


def _round_or_none(value: Optional[float], digits: int = 3) -> Optional[float]:
    if value is None:
        return None
    return round(value, digits)


def compare_valuation(target_ticker: str, peer_tickers: List[str]) -> Dict[str, Optional[float] | str]:
    """
    Returns valuation status compared to peer average.
    Values > 15% above peer avg = overvalued
    Values < 15% below peer avg = undervalued
    Else = fairly_valued
    """
    import yfinance as yf

    def fetch_val_metrics(ticker: str) -> Dict[str, Optional[float]]:
        try:
            info = yf.Ticker(ticker).info
        except Exception:
            info = {}
        return {
            "pe": _to_float(info.get("trailingPE")),
            "pb": _to_float(info.get("priceToBook")),
            "ev_ebitda": _to_float(info.get("enterpriseToEbitda")),
        }

    def determine_status(target: Optional[float], peer_avg: Optional[float]) -> str:
        if target is None or peer_avg is None:
            return "unknown"
        if target > (peer_avg * 1.15):
            return "overvalued"
        if target < (peer_avg * 0.85):
            return "undervalued"
        return "fairly_valued"

    target_val = fetch_val_metrics(target_ticker)

    peer_pes: List[float] = []
    peer_pbs: List[float] = []
    peer_evs: List[float] = []
    for peer in peer_tickers:
        values = fetch_val_metrics(peer)
        if values["pe"] is not None:
            peer_pes.append(values["pe"])
        if values["pb"] is not None:
            peer_pbs.append(values["pb"])
        if values["ev_ebitda"] is not None:
            peer_evs.append(values["ev_ebitda"])

    avg_pe = _avg(peer_pes)
    avg_pb = _avg(peer_pbs)
    avg_ev = _avg(peer_evs)

    return {
        "pe_status": determine_status(target_val["pe"], avg_pe),
        "pb_status": determine_status(target_val["pb"], avg_pb),
        "ev_ebitda_status": determine_status(target_val["ev_ebitda"], avg_ev),
        "target_pe": _round_or_none(target_val["pe"]),
        "peer_avg_pe": _round_or_none(avg_pe),
        "target_pb": _round_or_none(target_val["pb"]),
        "peer_avg_pb": _round_or_none(avg_pb),
        "target_ev_ebitda": _round_or_none(target_val["ev_ebitda"]),
        "peer_avg_ev_ebitda": _round_or_none(avg_ev),
    }
