"""
memory/personalization_service.py - Phase 15 Personalization Service.

Adapts narrative emphasis based on user's risk tolerance.
All rules are deterministic - no LLM required.
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


RISK_THRESHOLD = {
    "conservative": {"high_risk_cutoff": 40, "emphasize": "downside"},
    "moderate": {"high_risk_cutoff": 60, "emphasize": "balanced"},
    "aggressive": {"high_risk_cutoff": 80, "emphasize": "upside"},
}


def adapt_insights_to_preferences(
    insights: Dict[str, Any],
    risk: Dict[str, Any],
    preferences: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Surface/suppress deterministic insight emphasis by user risk profile.
    """
    if not insights or not preferences:
        return insights

    risk_profile = (preferences.get("risk_profile") or "moderate").lower()
    config = RISK_THRESHOLD.get(risk_profile, RISK_THRESHOLD["moderate"])
    composite_risk = risk.get("composite_risk_score", 0) if risk else 0
    notes: list[str] = []

    if risk_profile == "conservative":
        if composite_risk > config["high_risk_cutoff"]:
            notes.append(
                f"Conservative alert: Risk score {composite_risk:.0f}/100 exceeds your "
                f"tolerance threshold of {config['high_risk_cutoff']}."
            )
        leverage_score = (risk or {}).get("leverage_risk", {}).get("score", 0)
        if leverage_score and leverage_score > 50:
            notes.append(
                f"High leverage detected (score {leverage_score:.0f}). "
                "As a conservative investor this warrants caution."
            )
        notes.append(
            "Conservative framing: downside risks highlighted above bullish signals."
        )

    elif risk_profile == "aggressive":
        notes.append(
            "Aggressive framing: growth opportunity is the primary investment thesis."
        )
        if composite_risk < config["high_risk_cutoff"]:
            notes.append(
                f"Risk score {composite_risk:.0f}/100 is within your aggressive "
                "risk tolerance. Growth-first lens applied."
            )

    else:
        notes.append("Moderate framing: balanced view across risk and growth factors.")

    preferred_kpis = preferences.get("preferred_kpis") or []
    if preferred_kpis:
        notes.append(
            f"Your preferred KPIs ({', '.join(preferred_kpis[:3])}) are highlighted "
            "in the fundamentals section."
        )

    preferred_sectors = preferences.get("preferred_sectors") or []
    if preferred_sectors:
        notes.append(f"You have sector interest in: {', '.join(preferred_sectors[:3])}.")

    adapted = dict(insights)
    adapted["personalization_notes"] = notes
    adapted["applied_risk_profile"] = risk_profile
    return adapted


def build_memory_reminders(
    memory_recall: Optional[list],
    ticker: str,
) -> list:
    """
    Generate plain-text reminders from recalled memory results.
    """
    if not memory_recall:
        return []

    reminders = []
    for item in memory_recall[:3]:
        if not isinstance(item, dict):
            continue

        past_ticker = str(item.get("ticker", "")).strip()
        if not past_ticker:
            continue

        risk_score_raw = item.get("risk_score", 0)
        risk_score = float(risk_score_raw) if isinstance(risk_score_raw, (int, float)) else 0.0
        summary = str(item.get("summary_excerpt", "")).strip()
        summary_snippet = (summary[:120] + "...") if summary else "No summary excerpt available."

        if past_ticker.upper() == ticker.upper():
            reminders.append(
                f"You analyzed {past_ticker} before - Risk score: {risk_score:.0f}. "
                f"Summary: {summary_snippet}"
            )
        else:
            reminders.append(
                f"Earlier you analyzed {past_ticker} - Risk score: {risk_score:.0f}. "
                f"Summary: {summary_snippet}"
            )

    return reminders
