"""
agents/thesis_generator.py — Deterministic bull/bear cases (Phase 10).

Constructs the "Why you should buy" and "Why you should short" logical arguments
using ONLY the computed mathematical data produced by prior engines.
"""

from typing import Dict, Any, List

def generate_bull_thesis(
    ticker: str,
    forecast: Dict[str, Any],
    fundamentals: Dict[str, Any],
    risk: Dict[str, Any],
    comparison: Dict[str, Any] = None
) -> List[str]:
    
    thesis = []
    
    # Growth Argument
    if fundamentals:
        rev_growth = fundamentals.get("growth", {}).get("revenue_growth_yoy")
        if rev_growth and rev_growth > 0.15:
            thesis.append(f"Top-line expansion is robust, with revenue growing rapidly at {rev_growth*100:.1f}% year-over-year.")
            
        roe = fundamentals.get("capital_efficiency", {}).get("roe")
        if roe and roe > 0.20:
            thesis.append(f"Exceptional capital compounding machine, generating {roe*100:.1f}% returns on equity.")
            
    # Forecast Momentum
    prob = forecast.get("probability_bullish", 50.0)
    if prob > 60:
        thesis.append(f"Statistical momentum is heavily asymmetric to the upside ({prob:.1f}% bullish probability).")
        
    # Peer Context
    if comparison:
        prof_comp = comparison.get("profitability_comparison", {})
        if prof_comp.get("margin_position") == "above_average":
            thesis.append("Pricing power is validated by maintaining profit margins above the peer group average.")
            
        val_comp = comparison.get("valuation_comparison", {})
        if val_comp.get("pe_status") == "undervalued":
            thesis.append("Valuation dislocation provides a margin of safety (trading at a discount to peers).")
            
    if not thesis:
        thesis.append("The bull case relies primarily on holding through a neutral market-performer phase.")
        
    return thesis


def generate_bear_thesis(
    ticker: str,
    forecast: Dict[str, Any],
    fundamentals: Dict[str, Any],
    risk: Dict[str, Any],
    comparison: Dict[str, Any] = None
) -> List[str]:
    
    thesis = []
    
    # Structural Risk
    risk_score = risk.get("composite_risk_score", 50)
    if risk_score > 65:
        thesis.append(f"Elevated total risk profile (Score: {risk_score:.1f}/100) suggests significant fundamental fragility.")
        
    hidden_risks = risk.get("hidden_risks", [])
    for hr in hidden_risks:
        if hr.get("severity") == "critical":
            thesis.append(hr.get("description", "A critical structural risk was detected."))
            
    # Growth Deceleration
    if fundamentals:
        rev_growth = fundamentals.get("growth", {}).get("revenue_growth_yoy")
        if rev_growth and rev_growth < 0.0:
            thesis.append(f"Core business is contracting, with revenues actively shrinking by {rev_growth*100:.1f}% YoY.")
            
    # Forecast Downside
    prob_bear = forecast.get("probability_bearish", 50.0)
    if prob_bear > 60:
        thesis.append(f"Path of least resistance is lower, supported by strong statistical downside momentum ({prob_bear:.1f}% bearish probability).")
        
    # Overvaluation
    if comparison:
        val_comp = comparison.get("valuation_comparison", {})
        if val_comp.get("pe_status") == "overvalued":
            thesis.append("Priced for perfection; valuation is stretched relative to sector peers, risking multiple compression.")
            
    if not thesis:
        thesis.append("The bear case is limited, mostly revolving around broader macroeconomic shocks rather than specific idiosyncratic failures.")
        
    return thesis
