"""
memory/personalization_service.py — Phase 15 Personalization Service.

Adapts narrative emphasis based on user's risk tolerance (Conservative / Moderate / Aggressive).
All rules are deterministic — no LLM required.
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Risk tolerance thresholds
# ─────────────────────────────────────────────────────────────────────────────
RISK_THRESHOLD = {
    "conservative": {"high_risk_cutoff": 40, "emphasize": "downside"},
    "moderate":     {"high_risk_cutoff": 60, "emphasize": "balanced"},
    "aggressive":   {"high_risk_cutoff": 80, "emphasize": "upside"},
}


def adapt_insights_to_preferences(
    insights: Dict[str, Any],
    risk: Dict[str, Any],
    preferences: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Takes deterministic insight dict and surfaces / suppresses elements
    based on the user's risk profile.

    Returns the same structure with an added `personalization_notes` list.
    """
    if not insights or not preferences:
        return insights

    risk_profile = (preferences.get("risk_profile") or "moderate").lower()
    config = RISK_THRESHOLD.get(risk_profile, RISK_THRESHOLD["moderate"])
    composite_risk = risk.get("composite_risk_score", 0) if risk else 0
    notes: list[str] = []

    if risk_profile == "conservative":
        # Emphasise downsides
        if composite_risk > config["high_risk_cutoff"]:
            notes.append(
                f"⚠ CONSERVATIVE ALERT: Risk score {composite_risk:.0f}/100 exceeds your tolerance threshold of {config['high_risk_cutoff']}."
            )
        leverage_score = (risk or {}).get("leverage_risk", {}).get("score", 0)
        if leverage_score and leverage_score > 50:
            notes.append(f"High leverage detected (score {leverage_score:.0f}). As a conservative investor this warrants caution.")
        notes.append("Conservative framing: Downside risks highlighted above bullish signals.")

    elif risk_profile == "aggressive":
        # Emphasise growth upside
        notes.append("Aggressive framing: Growth opportunity is the primary investment thesis.")
        if composite_risk < config["high_risk_cutoff"]:
            notes.append(f"Risk score {composite_risk:.0f}/100 — within your aggressive risk tolerance. Growth-first lens applied.")

    else:
        # Moderate: balanced
        notes.append("Moderate framing: Balanced view across risk and growth factors.")

    # Preferred KPI callout
    preferred_kpis = preferences.get("preferred_kpis") or []
    if preferred_kpis:
        notes.append(f"Your preferred KPIs ({', '.join(preferred_kpis[:3])}) are highlighted in the fundamentals section.")

    # Preferred sector callout
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
    Generates plain-text reminders from Qdrant memory recall results.
    These are deterministic renderings of past research metadata.
    """
    if not memory_recall:
        return []

    reminders = []
    for item in memory_recall[:3]:
        past_ticker = item.get("ticker", "")
        risk_score = item.get("risk_score", 0)
        summary = item.get("summary_excerpt", "")

        if past_ticker and past_ticker.upper() != ticker.upper():
            reminders.append(
                f"Earlier you analyzed {past_ticker} — Risk score: {risk_score:.0f}. "
                f"Summary: {summary[:120]}..."
            )

    return reminders
