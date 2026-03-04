"""
utils/contradiction_detector.py — Rule-based logical contradiction detection (Phase 11).

Detects inconsistencies between engine outputs. Each rule checks two or more
computed metric values and raises a ContradictionItem if they conflict.

Rules are deterministic — no LLM, no heuristic guessing.
"""

import logging
from typing import List, Dict, Any

from schemas.confidence import ContradictionItem

logger = logging.getLogger(__name__)


def detect_contradictions(
    market: Dict[str, Any],
    forecast: Dict[str, Any],
    fundamentals: Dict[str, Any],
    risk: Dict[str, Any],
) -> List[ContradictionItem]:
    """
    Run all contradiction rules across engine outputs.

    Returns a list of ContradictionItems (may be empty if no conflicts found).
    """
    contradictions: List[ContradictionItem] = []

    # Guard — skip rules if data isn't available
    _check_growth_margin_conflict(fundamentals, contradictions)
    _check_bullish_forecast_high_risk(forecast, risk, contradictions)
    _check_strong_health_weak_liquidity(fundamentals, contradictions)
    _check_low_risk_high_volatility(risk, market, contradictions)
    _check_positive_earnings_negative_fcf(fundamentals, contradictions)
    _check_bullish_trend_high_risk(market, risk, contradictions)
    _check_overvalued_peer_but_bearish(forecast, fundamentals, contradictions)

    if contradictions:
        logger.info(f"Contradiction detector found {len(contradictions)} conflict(s)")

    return contradictions


# ── Individual Rules ──────────────────────────────────────────────────────────

def _check_growth_margin_conflict(
    funds: Dict[str, Any], out: List[ContradictionItem]
) -> None:
    """High revenue growth but simultaneously declining margins = efficiency concern."""
    if not funds:
        return
    rev_growth = funds.get("revenue_growth_yoy", None)
    net_margin = funds.get("net_margin", None)
    op_margin = funds.get("operating_margin", None)

    if rev_growth is None or net_margin is None:
        return

    # High growth (>15%) but negative/very low net margin
    if rev_growth > 0.15 and net_margin < 0.02:
        out.append(ContradictionItem(
            type="growth_margin_conflict",
            explanation=(
                f"Revenue is growing strongly ({rev_growth:.1%} YoY) but net margin "
                f"is only {net_margin:.1%}. Growth is not converting to profitability — "
                "possible cost-scaling problem or aggressive reinvestment."
            )
        ))

    # Positive growth but declining operating margin (proxy: op < net suggests expense surge)
    if op_margin is not None and rev_growth > 0.05 and op_margin < 0.0:
        out.append(ContradictionItem(
            type="growth_negative_operating_margin",
            explanation=(
                f"Revenue growing ({rev_growth:.1%} YoY) but operating margin is negative "
                f"({op_margin:.1%}). Operations are unprofitable despite top-line momentum."
            )
        ))


def _check_bullish_forecast_high_risk(
    forecast: Dict[str, Any], risk: Dict[str, Any], out: List[ContradictionItem]
) -> None:
    """Forecast is optimistic but composite risk score paints a dangerous picture."""
    if not forecast or not risk:
        return

    prob_bull = forecast.get("probability_bullish", 50.0)
    risk_score = risk.get("composite_risk_score", 50.0)

    if prob_bull > 65 and risk_score > 70:
        out.append(ContradictionItem(
            type="bullish_forecast_high_risk",
            explanation=(
                f"Statistical forecast shows {prob_bull:.0f}% bullish probability, "
                f"but composite risk score is critically high at {risk_score:.0f}/100. "
                "Momentum signals conflict with structural risk — treat with caution."
            )
        ))


def _check_strong_health_weak_liquidity(
    funds: Dict[str, Any], out: List[ContradictionItem]
) -> None:
    """Balance sheet classified as 'strong' but current ratio is dangerously low."""
    if not funds:
        return

    classification = funds.get("classification", "")
    current_ratio = funds.get("current_ratio", None)

    if classification in ("strong", "stellar") and current_ratio is not None and current_ratio < 1.0:
        out.append(ContradictionItem(
            type="strong_health_weak_liquidity",
            explanation=(
                f"Fundamental classification is '{classification}' but current ratio is "
                f"{current_ratio:.2f}x — below 1.0, indicating short-term obligations may "
                "not be fully covered by liquid assets. Liquidity risk is underrepresented."
            )
        ))


def _check_low_risk_high_volatility(
    risk: Dict[str, Any], market: Dict[str, Any], out: List[ContradictionItem]
) -> None:
    """Risk engine labels composite risk as low but market volatility is extremely high."""
    if not risk or not market:
        return

    risk_score = risk.get("composite_risk_score", 50.0)
    volatility = market.get("volatility_percent", 0.0)

    if risk_score < 30 and volatility > 40:
        out.append(ContradictionItem(
            type="low_risk_high_volatility",
            explanation=(
                f"Composite risk score is low ({risk_score:.0f}/100) but market volatility "
                f"is very high at {volatility:.1f}%. Structural risk metrics appear benign "
                "while price behavior suggests the market is pricing in significant uncertainty."
            )
        ))


def _check_positive_earnings_negative_fcf(
    funds: Dict[str, Any], out: List[ContradictionItem]
) -> None:
    """Net income is positive (profitable) but free cash flow is deeply negative."""
    if not funds:
        return

    net_margin = funds.get("net_margin", None)
    fcf = funds.get("free_cash_flow", None)

    if net_margin is None or fcf is None:
        return

    if net_margin > 0.05 and fcf < 0:
        out.append(ContradictionItem(
            type="positive_earnings_negative_fcf",
            explanation=(
                f"Net margin is positive ({net_margin:.1%}) suggesting accounting profit, "
                "but free cash flow is negative. This implies heavy capital expenditure, "
                "aggressive working capital build, or possible accrual-vs-cash divergence."
            )
        ))


def _check_bullish_trend_high_risk(
    market: Dict[str, Any], risk: Dict[str, Any], out: List[ContradictionItem]
) -> None:
    """Price trend is bullish but structural risk score is dangerously high."""
    if not market or not risk:
        return

    trend = market.get("trend_direction", "")
    risk_score = risk.get("composite_risk_score", 50.0)

    if trend == "bullish" and risk_score > 75:
        out.append(ContradictionItem(
            type="bullish_trend_high_structural_risk",
            explanation=(
                f"Price action shows bullish momentum but the composite structural risk "
                f"score is {risk_score:.0f}/100 — critically elevated. The market may be "
                "ignoring underlying balance sheet or leverage deterioration."
            )
        ))


def _check_overvalued_peer_but_bearish(
    forecast: Dict[str, Any], funds: Dict[str, Any], out: List[ContradictionItem]
) -> None:
    """Forecast is bearish but financials are strong — may indicate overreaction."""
    if not forecast or not funds:
        return

    prob_bear = forecast.get("probability_bearish", 50.0)
    classification = funds.get("classification", "")
    health_score = funds.get("health_score_composite", 50.0)

    if prob_bear > 65 and classification in ("strong", "stellar") and health_score > 70:
        out.append(ContradictionItem(
            type="bearish_forecast_strong_fundamentals",
            explanation=(
                f"Statistical forecast leans bearish ({prob_bear:.0f}% probability) but "
                f"fundamental health is '{classification}' with composite score {health_score:.0f}/100. "
                "Technical/momentum signals conflict with solid underlying financials."
            )
        ))
