"""
llm/investment_insights.py — AI Investment Insights Q&A (Feature 3).

Generates structured investor Q&A using Gemini LLM
with the analysis data as grounding context.

Rules:
  - Only uses provided data (no hallucination of financial numbers)
  - Always falls back to deterministic answers if LLM unavailable
  - Returns list of {question, answer} pairs
"""

import json
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

INVESTOR_QUESTIONS = [
    "Should I invest in this company right now?",
    "How risky is this investment for a retail investor?",
    "Will this stock likely grow over the next 6–12 months?",
    "What are the biggest risks for investors to watch?",
    "How does this company compare to its competitors?",
    "Is the current stock valuation justified by fundamentals?",
]

SYSTEM_PROMPT = """You are a professional financial analyst assistant.
You help retail investors understand complex financial analysis results.
You MUST only use the data provided — never invent financial numbers.
Your answers must be clear, concise (2-4 sentences), and balanced.
Respond in JSON format: {"insights": [{"question": "...", "answer": "..."}]}"""

def _build_context(ticker: str, analysis: Dict[str, Any]) -> str:
    """Serialize analysis data into a concise LLM-readable context string."""
    risk = analysis.get("risk", {}) or {}
    forecast = analysis.get("forecast", {}) or {}
    fund = analysis.get("fundamentals", {}) or {}
    insights = analysis.get("insights", {}) or {}
    confidence = analysis.get("confidence", {}) or {}
    comparison = analysis.get("comparison", {}) or {}

    parts = [f"TICKER: {ticker}"]

    if insights.get("executive_summary"):
        parts.append(f"EXECUTIVE SUMMARY: {insights['executive_summary']}")
    if insights.get("strengths"):
        parts.append(f"STRENGTHS: {'; '.join(insights['strengths'])}")
    if insights.get("risks"):
        parts.append(f"KEY RISKS: {'; '.join(insights['risks'])}")

    rsc = risk.get("composite_risk_score")
    rcl = risk.get("risk_classification")
    if rsc is not None:
        parts.append(f"RISK SCORE: {rsc}/100 ({rcl})")

    fhs = fund.get("financial_health_score")
    fc = fund.get("classification")
    if fhs is not None:
        parts.append(f"FINANCIAL HEALTH: {fhs}/100 ({fc})")
        prof = fund.get("profitability", {}) or {}
        if prof.get("net_profit_margin") is not None:
            parts.append(f"NET MARGIN: {prof['net_profit_margin']*100:.1f}%")
        lev = fund.get("leverage", {}) or {}
        if lev.get("debt_to_equity") is not None:
            parts.append(f"DEBT/EQUITY: {lev['debt_to_equity']:.2f}")

    mp = forecast.get("mid_projection")
    cp = forecast.get("current_price")
    if mp and cp:
        chg = (mp - cp) / cp * 100
        parts.append(f"PRICE FORECAST ({forecast.get('forecast_horizon_days', 90)}d): "
                     f"Current ${cp:.2f} → Target ${mp:.2f} ({chg:+.1f}%)")

    conf = confidence.get("confidence_score")
    if conf is not None:
        parts.append(f"ANALYSIS CONFIDENCE: {conf:.0f}%")

    peers = comparison.get("peers") or comparison.get("comparison_summary")
    if peers:
        parts.append(f"PEER DATA: {str(peers)[:200]}")

    if insights.get("bull_thesis"):
        parts.append(f"BULL CASE: {'; '.join(insights['bull_thesis'][:2])}")
    if insights.get("bear_thesis"):
        parts.append(f"BEAR CASE: {'; '.join(insights['bear_thesis'][:2])}")

    return "\n".join(parts)


def _deterministic_answers(ticker: str, analysis: Dict[str, Any]) -> List[Dict[str, str]]:
    """Fallback: generate rule-based answers from the deterministic data."""
    risk = analysis.get("risk", {}) or {}
    forecast = analysis.get("forecast", {}) or {}
    fund = analysis.get("fundamentals", {}) or {}
    insights = analysis.get("insights", {}) or {}

    rsc = risk.get("composite_risk_score", 50)
    rcl = risk.get("risk_classification", "moderate")
    fhs = fund.get("financial_health_score", 50)
    fc = fund.get("classification", "moderate")
    mp = forecast.get("mid_projection")
    cp = forecast.get("current_price")
    summary = insights.get("plain_language_summary", "No summary available.")
    strengths = insights.get("strengths", [])
    risks_list = insights.get("risks", [])

    invest_rec = "moderate consideration" if rsc < 50 else "caution" if rsc < 70 else "high caution"
    growth_view = "positive" if (mp and cp and mp > cp) else "cautious"
    chg_str = f"a {((mp-cp)/cp*100):+.1f}% move to ${mp:.2f}" if mp and cp else "unavailable"

    return [
        {
            "question": INVESTOR_QUESTIONS[0],
            "answer": f"{summary} Current risk classification is {rcl} ({rsc:.0f}/100), suggesting {invest_rec}."
        },
        {
            "question": INVESTOR_QUESTIONS[1],
            "answer": f"Risk score is {rsc:.0f}/100 ({rcl}). "
                      + (f"Key concerns include: {'; '.join(risks_list[:2])}." if risks_list else "No major risks flagged.")
        },
        {
            "question": INVESTOR_QUESTIONS[2],
            "answer": f"The 90-day forecast projects {chg_str}. The outlook is {growth_view} based on trend and volatility data."
        },
        {
            "question": INVESTOR_QUESTIONS[3],
            "answer": "; ".join(risks_list[:3]) if risks_list else "No specific risks identified in the current analysis."
        },
        {
            "question": INVESTOR_QUESTIONS[4],
            "answer": "Peer comparison data not available in quick mode. Run a deep analysis for sector benchmarking."
        },
        {
            "question": INVESTOR_QUESTIONS[5],
            "answer": f"Financial health score is {fhs:.0f}/100 ({fc}). "
                      + (f"Strengths: {'; '.join(strengths[:2])}." if strengths else "Fundamental data limited.")
        },
    ]


async def generate_ai_insights(
    ticker: str,
    analysis: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Main entry point for Feature 3.

    Returns:
        {
            "insights": [{"question": str, "answer": str}, ...],
            "llm_used": bool,
            "provider": str
        }
    """
    from app.config import get_settings
    from llm.gemini_client import GeminiProvider
    settings = get_settings()

    context = _build_context(ticker, analysis)
    questions_str = "\n".join(f"{i+1}. {q}" for i, q in enumerate(INVESTOR_QUESTIONS))
    user_prompt = (
        f"Analysis data:\n{context}\n\n"
        f"Answer these investor questions using ONLY the data above:\n{questions_str}\n\n"
        f"Return JSON: {{\"insights\": [{{\"question\": \"...\", \"answer\": \"...\"}}]}}"
    )

    # AI Investment Insights is explicitly pinned to Gemini.
    provider = None
    if settings.LLM_PROVIDER.lower() != "disabled" and settings.ENABLE_LLM:
        try:
            provider = GeminiProvider()
        except Exception as e:
            logger.warning(f"Gemini unavailable for AI insights: {e}. Using deterministic fallback.")

    if not provider:
        return {
            "insights": _deterministic_answers(ticker, analysis),
            "llm_used": False,
            "provider": "deterministic"
        }

    try:
        response_text, in_tokens, out_tokens = await provider.generate_response(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            temperature=0.15
        )

        # Parse JSON from response
        # Strip markdown code fences if present
        clean = response_text.strip()
        if clean.startswith("```"):
            clean = clean.split("```")[1]
            if clean.startswith("json"):
                clean = clean[4:]
        clean = clean.strip()

        parsed = json.loads(clean)
        insights = parsed.get("insights", [])

        # Validate structure
        if not isinstance(insights, list) or not all("question" in i and "answer" in i for i in insights):
            raise ValueError("Unexpected response structure")

        return {
            "insights": insights,
            "llm_used": True,
            "provider": "gemini"
        }

    except Exception as e:
        logger.warning(f"AI insights LLM call failed for {ticker}: {e}. Using deterministic fallback.")
        return {
            "insights": _deterministic_answers(ticker, analysis),
            "llm_used": False,
            "provider": "deterministic"
        }
