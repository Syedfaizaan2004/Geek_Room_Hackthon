"""
agents/summary_builder.py — Executive summary compilation (Phase 10).

Takes raw engine dicts and constructs a 3-5 sentence strategic overview.
"""

from typing import Dict, Any

def build_executive_summary(
    ticker: str,
    market: Dict[str, Any],
    forecast: Dict[str, Any],
    risk: Dict[str, Any],
    fundamentals: Dict[str, Any] = None,
    comparison: Dict[str, Any] = None
) -> str:
    """
    Constructs a deterministic plain-language summary based on computed metrics.
    """
    
    # 1. Base Trend
    trend = market.get("trend_direction", "neutral")
    last_price = market.get("last_price", 0.0)
    
    # 2. Financial Health
    health_str = ""
    if fundamentals:
        cls = fundamentals.get("classification", "moderate")
        health_str = f" with a {cls} foundational financial health score"
        
    summary = f"{ticker} is currently trading at ${last_price:,.2f}, demonstrating {trend} short-term momentum{health_str}. "
    
    # 3. Risk Level
    risk_score = risk.get("composite_risk_score", 50.0)
    level = "moderate"
    if risk_score > 60: level = "elevated"
    elif risk_score < 40: level = "low"
    
    hidden = risk.get("hidden_risks", [])
    if hidden:
        summary += f"The quantitative risk profile is {level} (Score: {risk_score:.1f}), though we flag {len(hidden)} latent structural concern(s) beneath the surface. "
    else:
        summary += f"The quantitative risk profile is strictly {level} (Score: {risk_score:.1f}) with no immediate structural red flags detected. "
        
    # 4. Forecast Bias
    prob_bull = forecast.get("probability_bullish", 50.0)
    prob_lbl = "neutral"
    if prob_bull > 60: prob_lbl = "bullish"
    elif prob_bull < 40: prob_lbl = "bearish"
    
    summary += f"Our nearest-term volatility-adjusted forecast maintains a {prob_lbl} bias ({prob_bull:.1f}% upside probability). "
    
    # 5. Peer Positioning
    if comparison:
        pos = comparison.get("strategic_summary", "")
        if pos:
            summary += pos
            
    return summary
