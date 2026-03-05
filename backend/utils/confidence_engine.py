"""
utils/confidence_engine.py — Master Confidence & Transparency Orchestrator (Phase 11).

Consumes structured outputs from Phases 3–10 and produces a ConfidenceResponse
with a 0–100 score, completeness rating, contradiction list, uncertainty classification,
and a fully-disclosed list of modelling assumptions.

All logic is deterministic — no LLM, no external calls.

==================================================
SCORING MODEL
==================================================

Base confidence: 80

Adjustments (additive, applied in order):
  +5   volatility_percent < 15%        (low volatility = higher certainty)
  -10  volatility_percent >= 30%       (high volatility = lower certainty)
  -10  any contradictions detected     (logical inconsistency penalty)
  -5   additional per contradiction beyond the first (up to -20 total)
  -15  completeness_score  < 60%       (missing data penalty)
  -5   completeness_score 60–79%       (partial data penalty)
  -10  composite_risk_score > 70       (high risk amplifies uncertainty)
  -5   scenario impact extreme (>15%)  (macro sensitivity penalty)
  +5   uncertainty_level == "low"      (tight, well-supported analysis)
  -5   uncertainty_level == "high"     (many uncertainty drivers)

Clamp: max(0, min(100, score))

Classification:
  > 75 → "high"
  50–75 → "moderate"
  < 50 → "low"
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, List

from schemas.confidence import ConfidenceResponse, ContradictionItem, UncertaintyDetail
from utils.contradiction_detector import detect_contradictions
from utils.uncertainty_analyzer import analyze_uncertainty

logger = logging.getLogger(__name__)


# ── Static Assumption Catalogue ───────────────────────────────────────────────
# These are always disclosed regardless of which engines ran.
BASE_ASSUMPTIONS: List[str] = [
    "Forecast direction is derived from historical volatility scaling and momentum indicators (Phase 4).",
    "Risk scoring is threshold-based using leverage ratios, current ratio, and FCF stability (Phase 6).",
    "Scenario stress impacts are deterministic approximations, not Monte Carlo simulations (Phase 7).",
    "Peer comparison uses equally-weighted sector averages from yfinance metadata (Phase 8).",
    "Financial health score is a composite of profitability, leverage, liquidity, and cash flow ratios (Phase 5).",
    "All probabilities are statistical estimates based on recent price history — not forward guidance.",
    "Missing financial fields are treated as neutral (0.0) rather than penalised, to avoid false negatives.",
]


def _extract_scenarios(scenario: Any) -> List[Dict[str, Any]]:
    """
    Normalize scenario payload shape across workflows.

    Supported forms:
    - Deep workflow list: [ {...}, {...} ]
    - Legacy dict: {"scenarios": [ {...}, {...} ]}
    """
    if not scenario:
        return []

    if isinstance(scenario, list):
        return [sc for sc in scenario if isinstance(sc, dict)]

    if isinstance(scenario, dict):
        maybe_list = scenario.get("scenarios", [])
        if isinstance(maybe_list, list):
            return [sc for sc in maybe_list if isinstance(sc, dict)]

    return []


def _scenario_impact_pct(scenario_row: Dict[str, Any]) -> float:
    """
    Return scenario impact in percentage points.

    Uses explicit `forecast_adjustment_pct` when present.
    Falls back to (adjusted_projection - baseline_projection) / baseline_projection.
    """
    explicit = scenario_row.get("forecast_adjustment_pct")
    if isinstance(explicit, (int, float)):
        return float(explicit)

    adjusted = scenario_row.get("adjusted_projection")
    baseline = scenario_row.get("baseline_projection")
    if isinstance(adjusted, (int, float)) and isinstance(baseline, (int, float)) and baseline != 0:
        return ((adjusted - baseline) / baseline) * 100.0

    return 0.0


def _compute_completeness(
    market: Dict[str, Any],
    forecast: Dict[str, Any],
    fundamentals: Dict[str, Any],
    risk: Dict[str, Any],
    scenario: Any,
    comparison: Dict[str, Any],
) -> float:
    """
    Score data completeness on a 0–100 scale.

    Each component has a weighted contribution:
      Market snapshot     20pts
      Forecast            20pts
      Fundamentals        25pts
      Risk profile        20pts
      Scenario analysis   10pts
      Peer comparison      5pts
    Total: 100pts
    """
    score = 0.0

    if market:
        score += 20.0
    if forecast:
        score += 20.0
    if fundamentals:
        base = 15.0
        # Bonus if multi-year data present
        yrs = fundamentals.get("years_of_data", 0)
        if isinstance(yrs, (int, float)) and yrs >= 3:
            base += 10.0
        else:
            base += min(yrs * 3.0, 10.0) if isinstance(yrs, (int, float)) else 0.0
        score += base
    if risk:
        score += 20.0
    if scenario:
        score += 10.0
    if comparison:
        score += 5.0

    return round(min(score, 100.0), 1)


def _compute_confidence_score(
    market: Dict[str, Any],
    forecast: Dict[str, Any],
    risk: Dict[str, Any],
    scenario: Any,
    completeness: float,
    contradictions: List[ContradictionItem],
    uncertainty: UncertaintyDetail,
) -> float:
    """
    Apply the scoring model described in the module docstring.
    Returns a float in [0, 100].
    """
    score = 80.0  # Base

    # ── Volatility adjustment ──────────────────────────────────────────────
    vol = market.get("volatility_percent", 0.0) if market else 0.0
    if vol < 15.0:
        score += 5.0
    elif vol >= 30.0:
        score -= 10.0

    # ── Contradiction penalty ──────────────────────────────────────────────
    n_contra = len(contradictions)
    if n_contra > 0:
        score -= 10.0                              # flat first-contradiction penalty
        score -= min((n_contra - 1) * 5.0, 20.0)  # up to -20 for additional

    # ── Data completeness penalty ──────────────────────────────────────────
    if completeness < 60.0:
        score -= 15.0
    elif completeness < 80.0:
        score -= 5.0

    # ── Risk score amplifier ───────────────────────────────────────────────
    risk_score = risk.get("composite_risk_score", 50.0) if risk else 50.0
    if risk_score > 70.0:
        score -= 10.0

    # ── Scenario sensitivity ───────────────────────────────────────────────
    for sc in _extract_scenarios(scenario):
        if abs(_scenario_impact_pct(sc)) > 15.0:
            score -= 5.0
            break  # only penalise once

    # ── Uncertainty level adjustment ───────────────────────────────────────
    if uncertainty.level == "low":
        score += 5.0
    elif uncertainty.level == "high":
        score -= 5.0

    return round(max(0.0, min(100.0, score)), 1)


def _classify_confidence(score: float) -> str:
    if score > 75.0:
        return "high"
    elif score >= 50.0:
        return "moderate"
    return "low"


def _build_assumptions(
    market: Dict, forecast: Dict, fundamentals: Dict,
    risk: Dict, scenario: Any, comparison: Dict,
) -> List[str]:
    """Combine base assumptions with context-specific disclosures."""
    assumptions = list(BASE_ASSUMPTIONS)

    if not comparison:
        assumptions.append(
            "Peer comparison data was unavailable — relative valuation context is missing."
        )
    if not scenario:
        assumptions.append(
            "Scenario stress testing was not run — macro sensitivity is unquantified."
        )
    if fundamentals:
        yrs = fundamentals.get("years_of_data", None)
        if isinstance(yrs, (int, float)) and yrs < 3:
            assumptions.append(
                f"Financial history spans only {yrs} year(s). "
                "Ratio analysis is based on limited data and may not reflect cyclical patterns."
            )

    return assumptions


# ── Public entry point ────────────────────────────────────────────────────────

def generate_confidence_report(
    ticker: str,
    market: Dict[str, Any],
    forecast: Dict[str, Any],
    fundamentals: Dict[str, Any],
    risk: Dict[str, Any],
    scenario: Any,
    comparison: Dict[str, Any],
) -> ConfidenceResponse:
    """
    Orchestrate all transparency sub-engines and return a ConfidenceResponse.

    Args:
        ticker:       The stock symbol being analysed.
        market:       Dict from market_node (Phase 3).
        forecast:     Dict from forecast_node (Phase 4).
        fundamentals: Dict from fundamentals_node (Phase 5).
        risk:         Dict from risk_node (Phase 6).
        scenario:     Dict from scenario_node (Phase 7).
        comparison:   Dict from comparison_node (Phase 8).

    Returns:
        ConfidenceResponse — fully populated transparency object.
    """
    logger.info(f"Generating confidence report for {ticker}")

    # 1. Completeness
    completeness = _compute_completeness(
        market, forecast, fundamentals, risk, scenario, comparison
    )

    # 2. Contradictions
    contradictions = detect_contradictions(market, forecast, fundamentals, risk)

    # 3. Uncertainty
    uncertainty = analyze_uncertainty(market, forecast, fundamentals, scenario)

    # 4. Score
    confidence_score = _compute_confidence_score(
        market, forecast, risk, scenario,
        completeness, contradictions, uncertainty
    )

    # 5. Level
    confidence_level = _classify_confidence(confidence_score)

    # 6. Assumptions
    assumptions = _build_assumptions(
        market, forecast, fundamentals, risk, scenario, comparison
    )

    logger.info(
        f"Confidence report for {ticker}: score={confidence_score}, "
        f"level={confidence_level}, completeness={completeness}, "
        f"contradictions={len(contradictions)}, uncertainty={uncertainty.level}"
    )

    return ConfidenceResponse(
        ticker=ticker,
        confidence_score=confidence_score,
        confidence_level=confidence_level,
        completeness_score=completeness,
        contradictions=contradictions,
        uncertainty=uncertainty,
        assumptions=assumptions,
        generated_at=datetime.now(timezone.utc),
    )
