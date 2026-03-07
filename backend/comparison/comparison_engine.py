"""
comparison/comparison_engine.py - Orchestrator combining peer metrics.

Calls fundamentals and risk engines for target and peers, then produces a
unified comparison payload.
"""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, Optional

from analytics.fundamentals_engine import get_fundamental_snapshot
from comparison.growth_compare import compare_growth
from comparison.peer_lookup import get_peer_companies
from comparison.profitability_compare import compare_profitability
from comparison.risk_compare import compare_risk
from comparison.summary_generator import generate_strategic_summary
from comparison.valuation_compare import compare_valuation
from risk.risk_engine import generate_risk_profile
from schemas.comparison import (
    ComparisonResponse,
    GrowthComparison,
    PeerSnapshot,
    ProfitabilityComparison,
    RiskComparison,
    ValuationComparison,
)
from utils.caching import market_cache

logger = logging.getLogger(__name__)


def _to_float(value: Any, digits: int = 4) -> Optional[float]:
    try:
        if value is None:
            return None
        return round(float(value), digits)
    except (TypeError, ValueError):
        return None


def _build_snapshot(ticker: str, funds: Dict[str, Any], risk: Dict[str, Any]) -> PeerSnapshot:
    growth = funds.get("growth", {}) or {}
    profitability = funds.get("profitability", {}) or {}
    capital_efficiency = funds.get("capital_efficiency", {}) or {}

    return PeerSnapshot(
        ticker=ticker,
        financial_health_score=_to_float(funds.get("financial_health_score"), 2),
        financial_health_classification=str(funds.get("classification", "unknown")),
        composite_risk_score=_to_float(risk.get("composite_risk_score"), 2),
        roe=_to_float(capital_efficiency.get("roe")),
        net_profit_margin=_to_float(profitability.get("net_profit_margin")),
        revenue_growth_yoy=_to_float(growth.get("revenue_growth_yoy")),
        earnings_growth_yoy=_to_float(growth.get("earnings_growth_yoy")),
    )


def run_peer_comparison(ticker: str, explicit_peers: str = None) -> ComparisonResponse:
    """
    Fetch target fundamentals and risk. Resolve peers. Fetch peer baselines.
    Execute valuation/profitability/growth/risk benchmarking.
    """
    ticker = ticker.upper().strip()

    cache_key = f"{ticker}:comparison:{explicit_peers or 'default'}"
    cached = market_cache.get(cache_key)
    if cached:
        return cached

    peers = get_peer_companies(ticker, explicit_peers)

    target_funds = get_fundamental_snapshot(ticker).model_dump()
    target_risk = generate_risk_profile(ticker).model_dump()

    peer_funds: Dict[str, Dict[str, Any]] = {}
    peer_risks: Dict[str, Dict[str, Any]] = {}
    for peer in peers:
        try:
            peer_funds[peer] = get_fundamental_snapshot(peer).model_dump()
            peer_risks[peer] = generate_risk_profile(peer).model_dump()
        except Exception as exc:
            logger.warning("Failed to fetch peer baseline for %s: %s", peer, exc)

    valid_peers = list(peer_funds.keys())

    valuation = compare_valuation(ticker, valid_peers)
    profitability = compare_profitability(ticker, target_funds, peer_funds)
    growth = compare_growth(ticker, target_funds, peer_funds)
    risk = compare_risk(ticker, target_risk, peer_risks)

    target_health = target_funds.get("classification", "moderate")
    summary = generate_strategic_summary(
        ticker=ticker,
        valuation=valuation,
        profitability=profitability,
        growth=growth,
        risk=risk,
        target_health=target_health,
    )

    target_snapshot = _build_snapshot(ticker, target_funds, target_risk)
    peer_snapshots = [_build_snapshot(peer, peer_funds[peer], peer_risks[peer]) for peer in valid_peers]
    peer_snapshots.sort(
        key=lambda item: item.composite_risk_score if item.composite_risk_score is not None else 10_000.0
    )

    response = ComparisonResponse(
        ticker=ticker,
        peers=valid_peers,
        valuation_comparison=ValuationComparison(**valuation),
        profitability_comparison=ProfitabilityComparison(**profitability),
        growth_comparison=GrowthComparison(**growth),
        risk_comparison=RiskComparison(**risk),
        financial_health_position=target_health,
        strengths=summary["strengths"],
        weaknesses=summary["weaknesses"],
        strategic_summary=summary["strategic_summary"],
        comparison_universe_size=len(valid_peers) + 1,
        target_snapshot=target_snapshot,
        peer_snapshots=peer_snapshots,
        generated_at=datetime.now(timezone.utc),
    )

    market_cache.set(cache_key, response, ttl=3600 * 12)
    return response
