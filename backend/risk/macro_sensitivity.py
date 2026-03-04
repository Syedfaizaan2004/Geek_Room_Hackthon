"""
risk/macro_sensitivity.py — Macro Sensitivity Estimator.

Placeholder logic inferring macro sensitivity from fundamentals:
- High leverage -> yield curve / interest rate sensitivity
- Low margins -> inflation / commodity input sensitivity
"""

from typing import Dict, Any

def estimate_macro_sensitivity(fundamentals: Dict[str, Any], market_stats: Dict[str, Any]) -> str:
    notes = []
    
    # 1. Rate sensitivity (Leverage)
    lev = fundamentals.get("leverage", {}).get("classification", "unknown")
    if lev == "high":
        notes.append("High debt load makes the asset inherently sensitive to interest rate hikes and refinancing risk.")
        
    # 2. Inflation sensitivity (Margins)
    npm = fundamentals.get("profitability", {}).get("net_profit_margin")
    if npm is not None and npm < 0.05:
        notes.append("Razor-thin net margins (<5%) suggest high vulnerability to inflation or rising supply-chain costs.")
        
    # 3. Market shock/Recession (Volatility)
    vol = market_stats.get("volatility_percent")
    if vol is not None and vol > 0.40:
        notes.append("Extreme historical volatility marks this as a high-beta asset, likely to suffer disproportionately in a recessionary macro shock.")
        
    if not notes:
        return "Asset exhibits standard macro-economic sensitivity with no extreme structural vulnerabilities flagged."
        
    return " ".join(notes)
