"""
utils/uncertainty_analyzer.py — Uncertainty level classification (Phase 11).

Identifies factors that increase analytical uncertainty and classifies
the overall uncertainty level as low / moderate / high.

All logic is deterministic — threshold-based, no LLM.
"""

import logging
from typing import Dict, Any, List

from schemas.confidence import UncertaintyDetail

logger = logging.getLogger(__name__)

# Thresholds (all configurable in one place)
HIGH_VOLATILITY_PCT = 30.0          # annualised volatility > 30%
WIDE_UNCERTAINTY_BAND_PCT = 40.0    # forecast uncertainty band > 40%
SHORT_HISTORY_YEARS = 3             # fewer than 3 years of financial data
HIGH_EARNINGS_VARIABILITY = 0.30    # earnings margin swung > 30 ppts between years
HIGH_SCENARIO_IMPACT = 15.0         # stress test shifts forecast by > 15%


def _extract_scenarios(scenario: Any) -> List[Dict[str, Any]]:
    """Normalize scenario payload to a list of dict rows."""
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
    """Return scenario impact pct from explicit or derived fields."""
    explicit = scenario_row.get("forecast_adjustment_pct")
    if isinstance(explicit, (int, float)):
        return float(explicit)

    adjusted = scenario_row.get("adjusted_projection")
    baseline = scenario_row.get("baseline_projection")
    if isinstance(adjusted, (int, float)) and isinstance(baseline, (int, float)) and baseline != 0:
        return ((adjusted - baseline) / baseline) * 100.0

    return 0.0


def analyze_uncertainty(
    market: Dict[str, Any],
    forecast: Dict[str, Any],
    fundamentals: Dict[str, Any],
    scenario: Any,
) -> UncertaintyDetail:
    """
    Evaluate factors that raise uncertainty and produce a classified level.

    Returns UncertaintyDetail(level, drivers).
    """
    drivers = []

    # ── Factor 1: High Market Volatility ─────────────────────────────────────
    vol = market.get("volatility_percent", 0.0) if market else 0.0
    if vol > HIGH_VOLATILITY_PCT:
        drivers.append(
            f"Market volatility is elevated at {vol:.1f}% (threshold: {HIGH_VOLATILITY_PCT}%). "
            "Price behaviour is erratic and forecast reliability is reduced."
        )

    # ── Factor 2: Wide Forecast Uncertainty Band ──────────────────────────────
    if forecast:
        band_upper = forecast.get("uncertainty_band_upper_pct", 0.0)
        band_lower = forecast.get("uncertainty_band_lower_pct", 0.0)
        band_width = abs(band_upper) + abs(band_lower)
        if band_width > WIDE_UNCERTAINTY_BAND_PCT:
            drivers.append(
                f"Forecast uncertainty band spans {band_width:.1f}% "
                f"(threshold: {WIDE_UNCERTAINTY_BAND_PCT}%). "
                "The expected price range is too wide to give high-certainty directional guidance."
            )

    # ── Factor 3: Short Financial History ────────────────────────────────────
    if fundamentals:
        years = fundamentals.get("years_of_data", None)
        if years is not None and years < SHORT_HISTORY_YEARS:
            drivers.append(
                f"Only {years} year(s) of financial history available "
                f"(minimum recommended: {SHORT_HISTORY_YEARS}). "
                "Short history reduces reliability of trend and ratio analysis."
            )

    # ── Factor 4: High Earnings Variability ──────────────────────────────────
    if fundamentals:
        margin_variability = fundamentals.get("earnings_margin_variability", None)
        if margin_variability is not None and margin_variability > HIGH_EARNINGS_VARIABILITY:
            drivers.append(
                f"Earnings margin variability is high ({margin_variability:.1%}). "
                "Inconsistent profitability makes forward projections less reliable."
            )

    # ── Factor 5: Extreme Scenario Sensitivity ────────────────────────────────
    for sc in _extract_scenarios(scenario):
        impact = abs(_scenario_impact_pct(sc))
        if impact > HIGH_SCENARIO_IMPACT:
            scenario_name = sc.get("scenario_name") or sc.get("scenario_type") or "unknown"
            drivers.append(
                f"Scenario '{scenario_name}' shifts the baseline "
                f"forecast by {impact:.1f}% "
                f"(threshold: {HIGH_SCENARIO_IMPACT}%). "
                "The analysis is highly sensitive to macro conditions."
            )
            break  # Only report once even if multiple scenarios trigger

    # ── Classify Level ────────────────────────────────────────────────────────
    n = len(drivers)
    if n == 0:
        level = "low"
    elif n <= 2:
        level = "moderate"
    else:
        level = "high"

    logger.debug(f"Uncertainty analysis: level={level}, drivers={n}")
    return UncertaintyDetail(level=level, drivers=drivers)
