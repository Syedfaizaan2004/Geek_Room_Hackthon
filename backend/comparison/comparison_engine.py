"""
comparison/comparison_engine.py — Orchestrator combining peer metrics.

Calls Phase 5 and Phase 6 data for the target AND its peers.
Routes them through the benchmarking modules and generates a unified insight payload.
"""

from datetime import datetime, timezone
import logging
from typing import List, Optional

from analytics.fundamentals_engine import get_fundamental_snapshot, FundamentalsFetchError, InsufficientFundamentalsError
from risk.risk_engine import generate_risk_profile
from comparison.peer_lookup import get_peer_companies
from comparison.valuation_compare import compare_valuation
from comparison.profitability_compare import compare_profitability
from comparison.growth_compare import compare_growth
from comparison.risk_compare import compare_risk
from comparison.summary_generator import generate_strategic_summary
from schemas.comparison import ComparisonResponse, ValuationComparison, ProfitabilityComparison, GrowthComparison, RiskComparison
from utils.caching import market_cache

logger = logging.getLogger(__name__)


def run_peer_comparison(ticker: str, explicit_peers: str = None) -> ComparisonResponse:
    """
    Fetch target fundamentals and risk. Find peers. Fetch peer fundamentals and risk.
    Execute benchmarking algorithms.
    """
    ticker = ticker.upper().strip()
    
    cache_key = f"{ticker}:comparison:{explicit_peers or 'default'}"
    cached = market_cache.get(cache_key)
    if cached:
        return cached

    # 1. Resolve Peers
    peers = get_peer_companies(ticker, explicit_peers)
    
    # 2. Fetch Target Baseline
    target_funds = get_fundamental_snapshot(ticker).model_dump()
    target_risk = generate_risk_profile(ticker).model_dump()
    
    # 3. Fetch Peer Baselines safely
    peer_funds = {}
    peer_risks = {}
    
    for p in peers:
        try:
            # We don't want the whole analysis to fail if 1 peer is missing data
            f = get_fundamental_snapshot(p).model_dump()
            r = generate_risk_profile(p).model_dump()
            peer_funds[p] = f
            peer_risks[p] = r
        except Exception as e:
            logger.warning(f"Failed to fetch peer baseline for {p}: {str(e)}")
            continue
            
    # Filter peers to only those that succeeded
    valid_peers = list(peer_funds.keys())

    # 4. Execute Benchmark Modules
    val_comp = compare_valuation(ticker, valid_peers)
    prof_comp = compare_profitability(ticker, target_funds, peer_funds)
    grow_comp = compare_growth(ticker, target_funds, peer_funds)
    risk_comp = compare_risk(ticker, target_risk, peer_risks)
    
    # 5. Generate Qualitative Summary
    target_health = target_funds.get("classification", "moderate")
    summary = generate_strategic_summary(ticker, val_comp, prof_comp, grow_comp, risk_comp, target_health)
    
    # 6. Build Payload
    resp = ComparisonResponse(
        ticker=ticker,
        peers=valid_peers,
        valuation_comparison=ValuationComparison(**val_comp),
        profitability_comparison=ProfitabilityComparison(**prof_comp),
        growth_comparison=GrowthComparison(**grow_comp),
        risk_comparison=RiskComparison(**risk_comp),
        financial_health_position=target_health,
        strengths=summary["strengths"],
        weaknesses=summary["weaknesses"],
        strategic_summary=summary["strategic_summary"],
        generated_at=datetime.now(timezone.utc)
    )
    
    market_cache.set(cache_key, resp, ttl=3600*12)  # Benchmark data shifts slowly
    return resp
