"""
comparison/summary_generator.py — Automated insights generation.

Synthesizes the quantitative benchmarking results into
Strings of strengths, weaknesses, and a strategic summary paragraph.
"""

from typing import Dict, Any, List

def generate_strategic_summary(
    ticker: str,
    valuation: Dict[str, str],
    profitability: Dict[str, Any],
    growth: Dict[str, Any],
    risk: Dict[str, Any],
    target_health: str
) -> Dict[str, Any]:
    
    strengths = []
    weaknesses = []
    
    # Analyze Valuation
    if valuation["pe_status"] == "undervalued":
        strengths.append("Trading at a discount to peers on an earnings basis.")
    elif valuation["pe_status"] == "overvalued":
        weaknesses.append("Priced at a premium relative to sector peers.")
        
    # Analyze Profitability
    if profitability["margin_position"] == "above_average":
        strengths.append("Demonstrates superior pricing power and margin profile vs peers.")
    elif profitability["margin_position"] == "below_average":
        weaknesses.append("Suffers from below-average profit margins.")
        
    if profitability["roe_rank"] == 1:
        strengths.append("Sector leader in returns on equity (Capital Efficiency).")
        
    # Analyze Growth
    if growth["revenue_growth_position"] == "above_average":
        strengths.append("Expanding market share with above-average topline growth.")
    elif growth["revenue_growth_position"] == "below_average":
        weaknesses.append("Losing ground to competitors on revenue growth.")
        
    # Analyze Risk & Health
    if risk["safety_position"] == "safest_in_class":
        strengths.append("Boasts the most resilient risk profile among evaluated peers.")
    elif risk["safety_position"] == "highest_risk":
        weaknesses.append("Screens as the most structurally risky asset in its peer group.")
        
    if target_health == "strong" and not weaknesses:
        strengths.append("Immaculate absolute financial health.")
    elif target_health == "weak":
        weaknesses.append("Absolute foundational financial health is poor.")

    # Fill default if empty
    if not strengths:
        strengths.append("Performs largely in-line with peers across major metrics without distinct advantages.")
    if not weaknesses:
        weaknesses.append("No glaring structural disadvantages compared to immediate peer group.")
        
    # Trim to Top 3
    strengths = strengths[:3]
    weaknesses = weaknesses[:3]
    
    # Generate Narrative
    summary = f"{ticker} is currently positioned as a "
    
    if "premium" in " ".join(weaknesses) and "above-average topline" in " ".join(strengths):
        summary += "premium growth leader, trading at high multiples justified by rapid expansion."
    elif valuation["pe_status"] == "undervalued" and target_health == "strong":
        summary += "potential value play, offering a solid absolute balance sheet at a discount to peers."
    elif target_health == "weak" and risk["safety_position"] == "highest_risk":
        summary += "highly speculative distressed asset, trailing peers significantly in safety and margin."
    elif profitability["margin_position"] == "above_average":
        summary += "quality compounder, leaning on superior margins and capital efficiency."
    else:
        summary += "market-performer, pacing alongside the broader sector with a balanced fundamental profile."
        
    return {
        "strengths": strengths,
        "weaknesses": weaknesses,
        "strategic_summary": summary
    }
