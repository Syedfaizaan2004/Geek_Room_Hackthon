"""
agents/synthesizer.py — Orchestrator compiling the cohesive memo (Phase 10).

Takes the full raw AgentState payload just before response formulation
and structures a deterministic investment memo tailored to user preferences.
"""

from datetime import datetime, timezone
from typing import Dict, Any, List

from agents.state import AgentState
from schemas.insights import InsightResponse, KeyMetricsSnapshot
from agents.summary_builder import build_executive_summary
from agents.thesis_generator import generate_bull_thesis, generate_bear_thesis


def synthesize_insights(state: AgentState) -> InsightResponse:
    """
    Transforms computed numbers into an institutional-grade investment memo.
    """
    
    ticker = state["ticker"]
    market = state.get("market_snapshot", {})
    forecast = state.get("forecast", {})
    funds = state.get("fundamentals", {})
    risk = state.get("risk", {})
    comp = state.get("comparison", {})
    prefs = state.get("preferences", {})
    
    # 1. Executive Summary
    exec_summ = build_executive_summary(ticker, market, forecast, risk, funds, comp)
    
    # 2. Extract Strengths (if comparison was run, it generated qualitative strengths)
    strengths = []
    if comp:
        strengths = comp.get("strengths", [])
    elif funds:
        if funds.get("classification") in ["strong", "stellar"]:
            strengths.append("Foundational balance sheet health is exceptional.")
            
    # 3. Extract Risks
    risks = []
    if risk:
        hr = risk.get("hidden_risks", [])
        for r_dict in hr:
            risks.append(r_dict.get("description", "Latent vulnerability detected."))
            
        lr = risk.get("leverage_risk", {})
        if lr.get("level") == "high":
            risks.append("Debt burden is elevated relative to equity and cash flows.")
            
    # 4. Generate Theses
    bull = generate_bull_thesis(ticker, forecast, funds, risk, comp)
    bear = generate_bear_thesis(ticker, forecast, funds, risk, comp)
    
    # 5. Plain Language Target
    risk_tol = prefs.get("risk_tolerance", "moderate")
    prob_bull = forecast.get("probability_bullish", 50.0)
    
    if risk_tol == "conservative" and risk.get("composite_risk_score", 50) > 60:
        pls = "Warning: This asset screens as structurally fragile. Due to your conservative profile, you should approach with extreme caution or avoid entirely."
    elif risk_tol == "aggressive" and prob_bull > 65:
        pls = "Aggressive Opportunity: While fundamental risks exist, the statistical momentum implies a highly asymmetric upside potential matching your high-risk appetite."
    elif prob_bull > 60:
        pls = "The asset shows strong upwards bias with a clean balance sheet, making it a reasonable foundational hold."
    else:
        pls = "The asset lacks a distinct catalyst in either direction. Continue to monitor for macro inflection points."
        
    # 6. Snap Metrics
    kms = KeyMetricsSnapshot(
        financial_health_score=funds.get("health_score_composite", 0.0) if funds else 0.0,
        risk_score=risk.get("composite_risk_score", 0.0) if risk else 0.0,
        probability_bullish=prob_bull,
        probability_bearish=forecast.get("probability_bearish", 50.0) if forecast else 50.0
    )
    
    return InsightResponse(
        ticker=ticker,
        executive_summary=exec_summ,
        strengths=strengths,
        risks=risks,
        bull_thesis=bull,
        bear_thesis=bear,
        plain_language_summary=pls,
        key_metrics_snapshot=kms,
        generated_at=datetime.now(timezone.utc)
    )
