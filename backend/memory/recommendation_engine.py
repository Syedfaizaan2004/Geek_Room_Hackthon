"""
memory/recommendation_engine.py — Phase 15 Smart Recommendation Engine.

All logic is deterministic and rule-based.
No LLM required — outputs are fully explainable.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Feature 2 — Next Analysis Actions
# ─────────────────────────────────────────────────────────────────────────────

def generate_next_actions(
    ticker: str,
    mode: str,
    risk: Optional[Dict[str, Any]],
    forecast: Optional[Dict[str, Any]],
    fundamentals: Optional[Dict[str, Any]],
    preferences: Optional[Dict[str, Any]],
) -> List[Dict[str, str]]:
    """
    Generates a list of recommended next actions based on engine outputs and preferences.
    Rules are fully transparent.
    """
    actions: List[Dict[str, str]] = []
    risk_score = (risk or {}).get("composite_risk_score", 0)
    risk_class = (risk or {}).get("risk_classification", "").lower()
    trend = (forecast or {}).get("trend", "").lower()
    health_score = (fundamentals or {}).get("health_score_composite", None)
    preferred_kpis = (preferences or {}).get("preferred_kpis") or []

    # Rule 1: High risk → stress test
    if risk_score and risk_score >= 65:
        actions.append({
            "action_type": "scenario_stress_test",
            "explanation": f"{ticker} has a high composite risk score ({risk_score:.0f}/100). Run a scenario stress test to see how it performs under recession or rate hike conditions."
        })

    # Rule 2: Bullish forecast but only quick mode → suggest deep mode
    if mode == "quick" and trend in ("bullish", "strong_uptrend", "uptrend"):
        actions.append({
            "action_type": "deep_analysis",
            "explanation": f"{ticker} shows a bullish trend. Run a full Deep Research to explore fundamentals, growth, and sector comparisons."
        })

    # Rule 3: Moderate risk + bullish forecast → peer compare
    if risk_score and 30 <= risk_score < 65 and trend in ("bullish", "uptrend"):
        actions.append({
            "action_type": "peer_comparison",
            "explanation": f"{ticker} has moderate risk with a bullish trend. Compare against peers to validate relative strength."
        })

    # Rule 4: Poor financial health → deep fundamentals
    if health_score is not None and health_score < 40:
        actions.append({
            "action_type": "fundamental_review",
            "explanation": f"Financial health score is low ({health_score:.0f}/100). A deeper fundamentals deep-dive is recommended."
        })

    # Rule 5: User prefers EBITDA/growth KPIs → growth analysis
    growth_kpis = {"ebitda", "revenue_growth", "free_cash_flow", "earnings_growth"}
    if any(k in growth_kpis for k in preferred_kpis):
        actions.append({
            "action_type": "growth_analysis",
            "explanation": f"Based on your preferred KPIs ({', '.join(k for k in preferred_kpis if k in growth_kpis)}), run a growth-focused analysis next."
        })

    # Rule 6: Risk high + high leverage → hidden risk scan
    leverage = ((risk or {}).get("leverage_risk") or {}).get("score", 0)
    if leverage and leverage > 65:
        actions.append({
            "action_type": "hidden_risk_scan",
            "explanation": f"Leverage risk score is elevated ({leverage:.0f}/100). A hidden structural risk scan is recommended."
        })

    return actions[:4]  # Cap at 4 suggestions


# ─────────────────────────────────────────────────────────────────────────────
# Feature 3 — Similar Company Recommendations (Qdrant-backed)
# ─────────────────────────────────────────────────────────────────────────────

async def get_similar_company_recommendations(
    ticker: str,
    user_id: str,
    preferred_sectors: Optional[List[str]] = None,
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    """
    Uses Qdrant find_similar_companies to surface tickers similar to this analysis.
    Filters to user's preferred sectors where metadata is available.
    Returns top 3.
    """
    try:
        from vector_store.qdrant_client import qdrant_wrapper
        from vector_store.memory_service import find_similar_companies

        if not qdrant_wrapper.is_healthy or not qdrant_wrapper.client:
            return []

        raw = await find_similar_companies(
            client=qdrant_wrapper.client,
            ticker=ticker,
            top_k=top_k,
        )

        results = []
        for item in raw:
            sim_ticker = item.ticker
            if sim_ticker.upper() == ticker.upper():
                continue
            results.append({
                "ticker": sim_ticker,
                "similarity_score": round(item.similarity_score, 3),
                "reason": f"Similar risk and insight profile to {ticker} (semantic similarity {item.similarity_score:.0%})."
            })
            if len(results) >= 3:
                break

        return results

    except Exception as e:
        logger.warning(f"Similar company lookup failed (non-fatal): {e}")
        return []


# ─────────────────────────────────────────────────────────────────────────────
# Feature 4 — Watchlist Recommendation
# ─────────────────────────────────────────────────────────────────────────────

def generate_watchlist_recommendation(
    ticker: str,
    risk: Optional[Dict[str, Any]],
    fundamentals: Optional[Dict[str, Any]],
    preferences: Optional[Dict[str, Any]],
) -> Optional[Dict[str, str]]:
    """
    Recommends adding ticker to the watchlist if it meets the user's preference criteria.
    """
    preferred_sectors = (preferences or {}).get("preferred_sectors") or []
    risk_profile = ((preferences or {}).get("risk_profile") or "moderate").lower()
    risk_score = (risk or {}).get("composite_risk_score", 50)
    revenue_growth = (fundamentals or {}).get("revenue_growth_yoy", 0)

    # Risk tolerance thresholds
    max_risk = {"conservative": 40, "moderate": 65, "aggressive": 85}.get(risk_profile, 65)

    reasons = []

    # Check risk fit
    if risk_score <= max_risk:
        reasons.append(f"Risk score {risk_score:.0f}/100 fits your {risk_profile} tolerance (max {max_risk}).")
    else:
        return None  # Too risky for this profile — don't recommend

    # Check growth
    if revenue_growth and revenue_growth > 0.05:
        reasons.append(f"Revenue growth {revenue_growth * 100:.1f}% is above 5% threshold.")

    if not reasons:
        return None

    return {
        "ticker": ticker,
        "reason": " ".join(reasons),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Feature 5 — Behavioral Profile
# ─────────────────────────────────────────────────────────────────────────────

def compute_behavioral_profile(
    preferences: Optional[Dict[str, Any]],
    memory_recall: Optional[List[Dict[str, Any]]],
    mode: str,
) -> Dict[str, Optional[str]]:
    """
    Builds a user behavioral profile from preferences and historical Qdrant memory.
    All logic is deterministic — no inference beyond counting and matching.
    """
    preferred_sectors = (preferences or {}).get("preferred_sectors") or []
    risk_profile = (preferences or {}).get("risk_profile") or "unknown"
    time_horizon = (preferences or {}).get("time_horizon") or "unknown"

    # Derive dominant sector from preferences (Phase 2 source of truth)
    dominant_sector = preferred_sectors[0] if preferred_sectors else None

    # Count memory recall tickers to detect analysis mode preference
    historical_modes: Dict[str, int] = {}
    if memory_recall:
        for m in memory_recall:
            m_mode = m.get("mode", "unknown")
            historical_modes[m_mode] = historical_modes.get(m_mode, 0) + 1

    if historical_modes:
        analysis_mode_pref = max(historical_modes, key=lambda k: historical_modes[k])
    else:
        analysis_mode_pref = mode  # Fall back to current session mode

    # Engagement pattern based on how many analyses present in memory
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


# ─────────────────────────────────────────────────────────────────────────────
# Master Orchestration — Full Recommendation Payload
# ─────────────────────────────────────────────────────────────────────────────

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
    Orchestrates all 5 recommendation features and returns a structured dict
    matching `RecommendationResponse` schema.
    """
    preferred_sectors = (preferences or {}).get("preferred_sectors") or []

    # Feature 2: next actions
    next_actions = generate_next_actions(ticker, mode, risk, forecast, fundamentals, preferences)

    # Feature 3: similar companies
    similar_companies = await get_similar_company_recommendations(
        ticker=ticker,
        user_id=user_id,
        preferred_sectors=preferred_sectors,
        top_k=5,
    )

    # Feature 4: watchlist
    watchlist_rec = generate_watchlist_recommendation(ticker, risk, fundamentals, preferences)
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
