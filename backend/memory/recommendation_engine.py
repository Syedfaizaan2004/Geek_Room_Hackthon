"""
memory/recommendation_engine.py - Phase 15 Smart Recommendation Engine.

All logic is deterministic and rule-based.
No LLM required - outputs are fully explainable.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def _extract_forecast_trend(forecast: Optional[Dict[str, Any]]) -> str:
    """
    Resolve trend direction across legacy and current forecast schemas.
    """
    payload = forecast or {}

    direct = payload.get("trend")
    if isinstance(direct, str) and direct.strip():
        return direct.strip().lower()

    based_on = payload.get("based_on")
    if isinstance(based_on, dict):
        trend_direction = based_on.get("trend_direction")
        if isinstance(trend_direction, str) and trend_direction.strip():
            return trend_direction.strip().lower()

    return ""


def _extract_health_score(fundamentals: Optional[Dict[str, Any]]) -> Optional[float]:
    """
    Resolve health score across legacy and current fundamentals schemas.
    """
    payload = fundamentals or {}

    for key in ("health_score_composite", "financial_health_score"):
        value = payload.get(key)
        if isinstance(value, (int, float)):
            return float(value)

    return None


def _extract_revenue_growth_yoy(fundamentals: Optional[Dict[str, Any]]) -> Optional[float]:
    """
    Resolve YoY revenue growth from either root-level or nested growth object.
    """
    payload = fundamentals or {}

    direct = payload.get("revenue_growth_yoy")
    if isinstance(direct, (int, float)):
        return float(direct)

    growth = payload.get("growth")
    if isinstance(growth, dict):
        nested = growth.get("revenue_growth_yoy")
        if isinstance(nested, (int, float)):
            return float(nested)

    return None


def _static_similar_companies_fallback(ticker: str, limit: int = 3) -> List[Dict[str, Any]]:
    """
    Last-resort deterministic fallback so the UI never stays empty.
    """
    universe = [
        "AAPL",
        "MSFT",
        "GOOGL",
        "AMZN",
        "NVDA",
        "META",
        "TSLA",
        "JPM",
        "BRK-B",
        "UNH",
    ]

    output: List[Dict[str, Any]] = []
    for candidate in universe:
        if candidate.upper() == ticker.upper():
            continue
        output.append(
            {
                "ticker": candidate,
                "similarity_score": 0.45,
                "reason": f"Large-cap market peer fallback for {ticker} when live similarity data is limited.",
            }
        )
        if len(output) >= limit:
            break

    return output


def _fallback_similar_companies_from_peers(ticker: str, limit: int = 3) -> List[Dict[str, Any]]:
    """
    Deterministic fallback when vector memory is unavailable or sparse.
    Uses peer comparison engine to suggest sector-adjacent companies.
    """
    try:
        from comparison.comparison_engine import run_peer_comparison

        comp = run_peer_comparison(ticker)
        peer_list = comp.peers if hasattr(comp, "peers") else []
        if not isinstance(peer_list, list) or len(peer_list) == 0:
            return _static_similar_companies_fallback(ticker, limit=limit)

        fallback: List[Dict[str, Any]] = []
        for peer in peer_list:
            if not isinstance(peer, str):
                continue
            if peer.upper() == ticker.upper():
                continue
            fallback.append(
                {
                    "ticker": peer.upper(),
                    "similarity_score": 0.55,
                    "reason": f"Sector peer fallback for {ticker} based on deterministic peer benchmarking.",
                }
            )
            if len(fallback) >= limit:
                break
        return fallback or _static_similar_companies_fallback(ticker, limit=limit)
    except Exception as e:
        logger.warning(f"Peer-based fallback failed (non-fatal): {e}")
        return _static_similar_companies_fallback(ticker, limit=limit)


def generate_next_actions(
    ticker: str,
    mode: str,
    risk: Optional[Dict[str, Any]],
    forecast: Optional[Dict[str, Any]],
    fundamentals: Optional[Dict[str, Any]],
    preferences: Optional[Dict[str, Any]],
) -> List[Dict[str, str]]:
    """
    Generate recommended next actions based on engine outputs and preferences.
    Rules are fully transparent.
    """
    actions: List[Dict[str, str]] = []
    risk_score = (risk or {}).get("composite_risk_score", 0)
    trend = _extract_forecast_trend(forecast)
    health_score = _extract_health_score(fundamentals)
    preferred_kpis = [
        str(k).strip().lower()
        for k in ((preferences or {}).get("preferred_kpis") or [])
        if isinstance(k, str) and str(k).strip()
    ]

    # Rule 1: High risk -> stress test
    if risk_score and risk_score >= 65:
        actions.append(
            {
                "action_type": "scenario_stress_test",
                "explanation": (
                    f"{ticker} has a high composite risk score ({risk_score:.0f}/100). "
                    "Run a scenario stress test to see how it performs under recession or "
                    "rate hike conditions."
                ),
            }
        )

    # Rule 2: Bullish forecast but only quick mode -> suggest deep mode
    if mode == "quick" and trend in ("bullish", "strong_uptrend", "uptrend"):
        actions.append(
            {
                "action_type": "deep_analysis",
                "explanation": (
                    f"{ticker} shows a bullish trend. Run a full Deep Research to explore "
                    "fundamentals, growth, and sector comparisons."
                ),
            }
        )

    # Rule 3: Moderate risk + bullish forecast -> peer compare
    if risk_score and 30 <= risk_score < 65 and trend in ("bullish", "uptrend"):
        actions.append(
            {
                "action_type": "peer_comparison",
                "explanation": (
                    f"{ticker} has moderate risk with a bullish trend. Compare against peers "
                    "to validate relative strength."
                ),
            }
        )

    # Rule 4: Poor financial health -> deep fundamentals
    if health_score is not None and health_score < 40:
        actions.append(
            {
                "action_type": "fundamental_review",
                "explanation": (
                    f"Financial health score is low ({health_score:.0f}/100). "
                    "A deeper fundamentals deep-dive is recommended."
                ),
            }
        )

    # Rule 5: User prefers EBITDA/growth KPIs -> growth analysis
    growth_kpis = {
        "ebitda",
        "revenue_growth",
        "revenue_growth_yoy",
        "free_cash_flow",
        "earnings_growth",
        "earnings_growth_yoy",
    }
    if any(k in growth_kpis for k in preferred_kpis):
        matched = ", ".join(k for k in preferred_kpis if k in growth_kpis)
        actions.append(
            {
                "action_type": "growth_analysis",
                "explanation": (
                    f"Based on your preferred KPIs ({matched}), run a growth-focused "
                    "analysis next."
                ),
            }
        )

    # Rule 6: High leverage risk -> hidden risk scan
    leverage = ((risk or {}).get("leverage_risk") or {}).get("score", 0)
    if leverage and leverage > 65:
        actions.append(
            {
                "action_type": "hidden_risk_scan",
                "explanation": (
                    f"Leverage risk score is elevated ({leverage:.0f}/100). "
                    "A hidden structural risk scan is recommended."
                ),
            }
        )

    return actions[:4]  # Cap at 4 suggestions


async def get_similar_company_recommendations(
    ticker: str,
    user_id: str,
    insight_text: Optional[str] = None,
    preferred_sectors: Optional[List[str]] = None,
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    """
    Use Qdrant find_similar_companies to surface semantically similar tickers.
    Returns top 3.
    """
    try:
        from vector_store.qdrant_client import qdrant_wrapper
        from vector_store.memory_service import find_similar_companies

        if not qdrant_wrapper.is_healthy or not qdrant_wrapper.client:
            return _fallback_similar_companies_from_peers(ticker, limit=min(top_k, 3))

        query_text = (insight_text or "").strip()
        if not query_text:
            query_text = (
                f"{ticker} stock investment thesis risk profile growth outlook "
                "financial analysis"
            )

        raw = await find_similar_companies(
            client=qdrant_wrapper.client,
            ticker=ticker,
            insight_text=query_text,
            top_k=top_k,
        )

        results = []
        for item in raw:
            sim_ticker = item.ticker
            if sim_ticker.upper() == ticker.upper():
                continue
            results.append(
                {
                    "ticker": sim_ticker,
                    "similarity_score": round(item.similarity_score, 3),
                    "reason": (
                        f"Similar risk and insight profile to {ticker} "
                        f"(semantic similarity {item.similarity_score:.0%})."
                    ),
                }
            )
            if len(results) >= 3:
                break

        target_len = min(top_k, 3)
        if len(results) < target_len:
            fallback = _fallback_similar_companies_from_peers(ticker, limit=target_len)
            seen = {r["ticker"].upper() for r in results if isinstance(r.get("ticker"), str)}
            for row in fallback:
                row_ticker = str(row.get("ticker", "")).upper()
                if not row_ticker or row_ticker in seen:
                    continue
                results.append(row)
                seen.add(row_ticker)
                if len(results) >= target_len:
                    break

        return results[:target_len]

    except Exception as e:
        logger.warning(f"Similar company lookup failed (non-fatal): {e}")
        return _fallback_similar_companies_from_peers(ticker, limit=min(top_k, 3))


def generate_watchlist_recommendation(
    ticker: str,
    risk: Optional[Dict[str, Any]],
    fundamentals: Optional[Dict[str, Any]],
    preferences: Optional[Dict[str, Any]],
) -> Optional[Dict[str, str]]:
    """
    Recommend adding ticker to watchlist if it fits user criteria.
    """
    risk_profile = ((preferences or {}).get("risk_profile") or "moderate").lower()
    risk_score = (risk or {}).get("composite_risk_score", 50)
    revenue_growth = _extract_revenue_growth_yoy(fundamentals)

    # Risk tolerance thresholds
    max_risk = {"conservative": 40, "moderate": 65, "aggressive": 85}.get(
        risk_profile, 65
    )

    reasons = []

    # Check risk fit
    if risk_score <= max_risk:
        reasons.append(
            f"Risk score {risk_score:.0f}/100 fits your {risk_profile} tolerance "
            f"(max {max_risk})."
        )
    else:
        return None  # Too risky for this profile

    # Check growth
    if revenue_growth is not None and revenue_growth > 0.05:
        reasons.append(
            f"Revenue growth {revenue_growth * 100:.1f}% is above 5% threshold."
        )

    if not reasons:
        return None

    return {
        "ticker": ticker,
        "reason": " ".join(reasons),
    }


def compute_behavioral_profile(
    preferences: Optional[Dict[str, Any]],
    memory_recall: Optional[List[Dict[str, Any]]],
    mode: str,
) -> Dict[str, Optional[str]]:
    """
    Build user behavioral profile from preferences and historical memory.
    """
    preferred_sectors = (preferences or {}).get("preferred_sectors") or []
    risk_profile = (preferences or {}).get("risk_profile") or "unknown"

    dominant_sector = preferred_sectors[0] if preferred_sectors else None

    # Count memory recall modes to detect mode preference
    historical_modes: Dict[str, int] = {}
    if memory_recall:
        for m in memory_recall:
            m_mode = m.get("mode", "unknown")
            historical_modes[m_mode] = historical_modes.get(m_mode, 0) + 1

    if historical_modes:
        analysis_mode_pref = max(historical_modes, key=lambda k: historical_modes[k])
    else:
        analysis_mode_pref = mode

    # Engagement pattern from recall volume
    recall_count = len(memory_recall or [])
    if recall_count >= 10:
        engagement = "heavy_user"
    elif recall_count >= 3:
        engagement = "regular_user"
    elif recall_count >= 1:
        engagement = "occasional_user"
    else:
        engagement = "new_user"

    return {
        "dominant_sector": dominant_sector,
        "typical_risk_profile": risk_profile,
        "analysis_mode_preference": analysis_mode_pref,
        "engagement_pattern": engagement,
    }


async def build_recommendation_payload(
    ticker: str,
    mode: str,
    user_id: str,
    preferences: Optional[Dict[str, Any]],
    risk: Optional[Dict[str, Any]],
    forecast: Optional[Dict[str, Any]],
    fundamentals: Optional[Dict[str, Any]],
    memory_recall: Optional[List[Dict[str, Any]]],
) -> Dict[str, Any]:
    """
    Orchestrate recommendation features and return a structured payload.
    """
    preferred_sectors = (preferences or {}).get("preferred_sectors") or []
    memory_recall = memory_recall or []

    # Build a stable query text for similar-company lookup.
    first_memory_summary = ""
    if memory_recall and isinstance(memory_recall[0], dict):
        first_memory_summary = str(memory_recall[0].get("summary_excerpt") or "").strip()

    insight_text = (
        first_memory_summary
        or f"{ticker} stock investment thesis risk profile growth outlook financial analysis"
    )

    # Feature 2: next actions
    next_actions = generate_next_actions(
        ticker, mode, risk, forecast, fundamentals, preferences
    )
    if not next_actions:
        next_actions = [
            {
                "action_type": "deep_analysis",
                "explanation": f"Run a deep analysis on {ticker} to build a complete fundamentals, risk, and scenario view.",
            },
            {
                "action_type": "peer_comparison",
                "explanation": f"Compare {ticker} with sector peers for relative strength and valuation context.",
            },
        ]

    # Feature 3: similar companies
    similar_companies = await get_similar_company_recommendations(
        ticker=ticker,
        user_id=user_id,
        insight_text=insight_text,
        preferred_sectors=preferred_sectors,
        top_k=5,
    )

    # Feature 4: watchlist
    watchlist_rec = generate_watchlist_recommendation(
        ticker, risk, fundamentals, preferences
    )
    watchlist_recommendations = [watchlist_rec] if watchlist_rec else []

    # Feature 5: behavioral profile
    behavioral_profile = compute_behavioral_profile(preferences, memory_recall, mode)

    # Feature 6: memory reminders
    from memory.personalization_service import build_memory_reminders

    memory_reminders = build_memory_reminders(memory_recall, ticker)

    return {
        "ticker": ticker,
        "next_actions": next_actions,
        "similar_companies": similar_companies,
        "watchlist_recommendations": watchlist_recommendations,
        "behavioral_profile": behavioral_profile,
        "memory_reminders": memory_reminders,
        "generated_at": datetime.utcnow().isoformat(),
    }
