"""
demo/fixtures.py — Phase 16 Demo Mode Static Fixtures.

Provides pre-computed, realistic-looking data for popular tickers
so the system can run fully without live API keys or Qdrant.
Used when DEMO_MODE=true in .env.

All field names MUST match real backend Pydantic schemas:
  - MarketSnapshotResponse: moving_averages.sma_20, sma_50, sma_200
  - ForecastResponse:       mid_projection, projected_upper_bound, projected_lower_bound, current_price
  - FundamentalResponse:    financial_health_score, profitability, growth, capital_efficiency, cash_flow, leverage, liquidity
  - ScenarioResponse:       scenario_type, adjusted_risk_score, adjusted_projection, baseline_projection, impact_analysis
"""

from datetime import datetime, timezone

_NOW = datetime.now(timezone.utc).isoformat()

# ─── Market snapshots — matches MarketSnapshotResponse ───────────────────────
DEMO_MARKET: dict = {
    "AAPL": {
        "ticker": "AAPL", "company_name": "Apple Inc.",
        "last_price": 193.45, "price_change_percent": 1.23,
        "volatility_percent": 0.215, "volatility_level": "moderate", "trend_direction": "bullish",
        "moving_averages": {"sma_20": 188.30, "sma_50": 182.10, "sma_200": 175.40},
        "performance": {"one_month": 0.032, "three_month": 0.071, "six_month": 0.118, "one_year": 0.214, "ytd": 0.054},
        "data_points": 252, "last_updated": _NOW,
    },
    "MSFT": {
        "ticker": "MSFT", "company_name": "Microsoft Corporation",
        "last_price": 418.72, "price_change_percent": 0.88,
        "volatility_percent": 0.185, "volatility_level": "moderate", "trend_direction": "bullish",
        "moving_averages": {"sma_20": 410.50, "sma_50": 398.75, "sma_200": 380.20},
        "performance": {"one_month": 0.028, "three_month": 0.065, "six_month": 0.095, "one_year": 0.320, "ytd": 0.041},
        "data_points": 252, "last_updated": _NOW,
    },
    "GOOGL": {
        "ticker": "GOOGL", "company_name": "Alphabet Inc.",
        "last_price": 171.55, "price_change_percent": -0.42,
        "volatility_percent": 0.230, "volatility_level": "moderate", "trend_direction": "neutral",
        "moving_averages": {"sma_20": 174.80, "sma_50": 168.20, "sma_200": 155.90},
        "performance": {"one_month": -0.018, "three_month": 0.042, "six_month": 0.087, "one_year": 0.185, "ytd": 0.012},
        "data_points": 252, "last_updated": _NOW,
    },
    "NVDA": {
        "ticker": "NVDA", "company_name": "NVIDIA Corporation",
        "last_price": 875.10, "price_change_percent": 2.15,
        "volatility_percent": 0.480, "volatility_level": "high", "trend_direction": "bullish",
        "moving_averages": {"sma_20": 820.00, "sma_50": 780.50, "sma_200": 650.30},
        "performance": {"one_month": 0.082, "three_month": 0.198, "six_month": 0.312, "one_year": 1.850, "ytd": 0.145},
        "data_points": 252, "last_updated": _NOW,
    },
    "TSLA": {
        "ticker": "TSLA", "company_name": "Tesla Inc.",
        "last_price": 234.90, "price_change_percent": -1.87,
        "volatility_percent": 0.520, "volatility_level": "high", "trend_direction": "bearish",
        "moving_averages": {"sma_20": 245.00, "sma_50": 260.30, "sma_200": 220.80},
        "performance": {"one_month": -0.092, "three_month": -0.148, "six_month": -0.215, "one_year": -0.087, "ytd": -0.120},
        "data_points": 252, "last_updated": _NOW,
    },
}

# ─── Forecast — matches ForecastResponse ─────────────────────────────────────
DEMO_FORECAST: dict = {
    "AAPL": {
        "forecast_horizon_days": 90, "current_price": 193.45,
        "mid_projection": 203.20, "projected_upper_bound": 224.80, "projected_lower_bound": 181.60,
        "expected_move_percent": 0.1630,
        "probability_outlook": {"probability_bullish": 0.68, "probability_bearish": 0.32, "confidence_level": "high"},
        "uncertainty": {"uncertainty_percent": 16.3, "classification": "moderate"},
        "based_on": {"volatility_percent": 0.215, "trend_direction": "bullish", "time_horizon": "medium_term"},
    },
    "MSFT": {
        "forecast_horizon_days": 90, "current_price": 418.72,
        "mid_projection": 439.80, "projected_upper_bound": 479.40, "projected_lower_bound": 400.20,
        "expected_move_percent": 0.1488,
        "probability_outlook": {"probability_bullish": 0.72, "probability_bearish": 0.28, "confidence_level": "high"},
        "uncertainty": {"uncertainty_percent": 14.9, "classification": "moderate"},
        "based_on": {"volatility_percent": 0.185, "trend_direction": "bullish", "time_horizon": "medium_term"},
    },
    "GOOGL": {
        "forecast_horizon_days": 90, "current_price": 171.55,
        "mid_projection": 175.20, "projected_upper_bound": 198.70, "projected_lower_bound": 151.70,
        "expected_move_percent": 0.1852,
        "probability_outlook": {"probability_bullish": 0.52, "probability_bearish": 0.48, "confidence_level": "moderate"},
        "uncertainty": {"uncertainty_percent": 18.5, "classification": "wide"},
        "based_on": {"volatility_percent": 0.230, "trend_direction": "neutral", "time_horizon": "medium_term"},
    },
    "NVDA": {
        "forecast_horizon_days": 90, "current_price": 875.10,
        "mid_projection": 972.40, "projected_upper_bound": 1185.50, "projected_lower_bound": 759.30,
        "expected_move_percent": 0.3866,
        "probability_outlook": {"probability_bullish": 0.74, "probability_bearish": 0.26, "confidence_level": "moderate"},
        "uncertainty": {"uncertainty_percent": 38.7, "classification": "wide"},
        "based_on": {"volatility_percent": 0.480, "trend_direction": "bullish", "time_horizon": "medium_term"},
    },
    "TSLA": {
        "forecast_horizon_days": 90, "current_price": 234.90,
        "mid_projection": 211.20, "projected_upper_bound": 307.80, "projected_lower_bound": 114.60,
        "expected_move_percent": 0.4186,
        "probability_outlook": {"probability_bullish": 0.38, "probability_bearish": 0.62, "confidence_level": "moderate"},
        "uncertainty": {"uncertainty_percent": 41.9, "classification": "wide"},
        "based_on": {"volatility_percent": 0.520, "trend_direction": "bearish", "time_horizon": "medium_term"},
    },
}

# ─── Fundamentals — matches FundamentalResponse (nested sub-objects) ──────────
DEMO_FUNDAMENTALS: dict = {
    "AAPL": {
        "financial_health_score": 82.0, "classification": "strong", "data_years_used": 3,
        "profitability": {"net_profit_margin": 0.253, "operating_margin": 0.305, "gross_margin": 0.442, "ebitda_margin": 0.328},
        "growth": {"revenue_growth_yoy": 0.048, "revenue_cagr_3y": 0.071, "earnings_growth_yoy": 0.078},
        "capital_efficiency": {"roe": 1.474, "roa": 0.279, "roic": 0.581},
        "cash_flow": {"free_cash_flow": 99584000000, "fcf_margin": 0.258, "fcf_growth_yoy": 0.095},
        "leverage": {"debt_to_equity": 1.79, "debt_to_assets": 0.318, "interest_coverage_ratio": 41.2, "classification": "moderate"},
        "liquidity": {"current_ratio": 0.99, "quick_ratio": 0.98, "classification": "adequate"},
    },
    "MSFT": {
        "financial_health_score": 91.0, "classification": "strong", "data_years_used": 3,
        "profitability": {"net_profit_margin": 0.341, "operating_margin": 0.446, "gross_margin": 0.695, "ebitda_margin": 0.502},
        "growth": {"revenue_growth_yoy": 0.158, "revenue_cagr_3y": 0.142, "earnings_growth_yoy": 0.217},
        "capital_efficiency": {"roe": 0.388, "roa": 0.171, "roic": 0.295},
        "cash_flow": {"free_cash_flow": 63300000000, "fcf_margin": 0.289, "fcf_growth_yoy": 0.185},
        "leverage": {"debt_to_equity": 0.42, "debt_to_assets": 0.184, "interest_coverage_ratio": 52.8, "classification": "low"},
        "liquidity": {"current_ratio": 1.78, "quick_ratio": 1.75, "classification": "strong"},
    },
    "GOOGL": {
        "financial_health_score": 78.0, "classification": "strong", "data_years_used": 3,
        "profitability": {"net_profit_margin": 0.212, "operating_margin": 0.274, "gross_margin": 0.564, "ebitda_margin": 0.318},
        "growth": {"revenue_growth_yoy": 0.082, "revenue_cagr_3y": 0.118, "earnings_growth_yoy": 0.234},
        "capital_efficiency": {"roe": 0.231, "roa": 0.145, "roic": 0.198},
        "cash_flow": {"free_cash_flow": 60100000000, "fcf_margin": 0.218, "fcf_growth_yoy": 0.142},
        "leverage": {"debt_to_equity": 0.10, "debt_to_assets": 0.048, "interest_coverage_ratio": 88.4, "classification": "low"},
        "liquidity": {"current_ratio": 2.10, "quick_ratio": 2.08, "classification": "strong"},
    },
    "NVDA": {
        "financial_health_score": 88.0, "classification": "strong", "data_years_used": 3,
        "profitability": {"net_profit_margin": 0.557, "operating_margin": 0.614, "gross_margin": 0.745, "ebitda_margin": 0.638},
        "growth": {"revenue_growth_yoy": 1.220, "revenue_cagr_3y": 0.685, "earnings_growth_yoy": 5.880},
        "capital_efficiency": {"roe": 0.912, "roa": 0.548, "roic": 0.781},
        "cash_flow": {"free_cash_flow": 32700000000, "fcf_margin": 0.415, "fcf_growth_yoy": 1.850},
        "leverage": {"debt_to_equity": 0.41, "debt_to_assets": 0.235, "interest_coverage_ratio": 62.1, "classification": "low"},
        "liquidity": {"current_ratio": 4.17, "quick_ratio": 3.87, "classification": "strong"},
    },
    "TSLA": {
        "financial_health_score": 48.0, "classification": "moderate", "data_years_used": 3,
        "profitability": {"net_profit_margin": 0.053, "operating_margin": 0.086, "gross_margin": 0.175, "ebitda_margin": 0.142},
        "growth": {"revenue_growth_yoy": 0.019, "revenue_cagr_3y": 0.318, "earnings_growth_yoy": -0.234},
        "capital_efficiency": {"roe": 0.142, "roa": 0.062, "roic": 0.108},
        "cash_flow": {"free_cash_flow": -2400000000, "fcf_margin": -0.025, "fcf_growth_yoy": -0.680},
        "leverage": {"debt_to_equity": 0.88, "debt_to_assets": 0.268, "interest_coverage_ratio": 12.4, "classification": "moderate"},
        "liquidity": {"current_ratio": 1.73, "quick_ratio": 1.38, "classification": "adequate"},
    },
}

# ─── Scenario stress tests — list of ScenarioResponse-shaped dicts ────────────
def _make_scenarios(ticker: str, base_risk: float, base_proj: float) -> list:
    return [
        {
            "scenario_type": "recession",
            "baseline_risk_score": base_risk, "adjusted_risk_score": min(100, base_risk + 22),
            "baseline_projection": base_proj, "adjusted_projection": round(base_proj * 0.82, 2),
            "baseline_uncertainty_percent": 0.18, "adjusted_uncertainty_percent": 0.35,
            "impact_analysis": f"In a recession scenario, {ticker} faces revenue headwinds and multiple compression. Equity risk increases materially.",
            "assumptions": ["GDP contracts 2%+", "Consumer spending falls", "Credit spreads widen"],
            "probability_shift": {"probability_bullish": 0.20, "probability_bearish": 0.80, "confidence_level": "moderate"},
        },
        {
            "scenario_type": "high_inflation",
            "baseline_risk_score": base_risk, "adjusted_risk_score": min(100, base_risk + 15),
            "baseline_projection": base_proj, "adjusted_projection": round(base_proj * 0.91, 2),
            "baseline_uncertainty_percent": 0.18, "adjusted_uncertainty_percent": 0.28,
            "impact_analysis": f"Sustained inflation pressures {ticker}'s cost structure and compresses margins. Real returns deteriorate.",
            "assumptions": ["CPI above 5% for 2+ quarters", "Fed maintains high rates", "Input costs rise"],
            "probability_shift": {"probability_bullish": 0.30, "probability_bearish": 0.70, "confidence_level": "moderate"},
        },
        {
            "scenario_type": "interest_rate_hike",
            "baseline_risk_score": base_risk, "adjusted_risk_score": min(100, base_risk + 12),
            "baseline_projection": base_proj, "adjusted_projection": round(base_proj * 0.94, 2),
            "baseline_uncertainty_percent": 0.18, "adjusted_uncertainty_percent": 0.24,
            "impact_analysis": f"Rate hikes increase {ticker}'s discount rate, compressing its DCF valuation and increasing borrowing costs.",
            "assumptions": ["Fed funds rate +100bps", "Bond yields spike", "P/E multiples contract"],
            "probability_shift": {"probability_bullish": 0.38, "probability_bearish": 0.62, "confidence_level": "moderate"},
        },
        {
            "scenario_type": "growth_slowdown",
            "baseline_risk_score": base_risk, "adjusted_risk_score": min(100, base_risk + 8),
            "baseline_projection": base_proj, "adjusted_projection": round(base_proj * 0.97, 2),
            "baseline_uncertainty_percent": 0.18, "adjusted_uncertainty_percent": 0.22,
            "impact_analysis": f"{ticker}'s growth trajectory decelerates. Market re-rates the stock toward value multiples.",
            "assumptions": ["Revenue growth halves", "Margin expansion stalls", "Capex guidance lowered"],
            "probability_shift": {"probability_bullish": 0.44, "probability_bearish": 0.56, "confidence_level": "moderate"},
        },
    ]


DEMO_SCENARIO: dict = {
    "AAPL":  _make_scenarios("AAPL",  32.0, 203.20),
    "MSFT":  _make_scenarios("MSFT",  28.0, 439.80),
    "GOOGL": _make_scenarios("GOOGL", 41.0, 175.20),
    "NVDA":  _make_scenarios("NVDA",  55.0, 972.40),
    "TSLA":  _make_scenarios("TSLA",  74.0, 211.20),
}

# ─── Risk profiles ────────────────────────────────────────────────────────────
DEMO_RISK: dict = {
    "AAPL": {
        "composite_risk_score": 32.0, "risk_classification": "low",
        "leverage_risk": {"score": 25.0, "flags": []},
        "liquidity_risk": {"score": 15.0, "flags": []},
        "earnings_volatility_risk": {"score": 38.0, "flags": ["Earnings beat variability"]},
        "cashflow_instability_risk": {"score": 20.0, "flags": []},
        "hidden_structural_risks": [],
    },
    "MSFT": {
        "composite_risk_score": 28.0, "risk_classification": "low",
        "leverage_risk": {"score": 22.0, "flags": []},
        "liquidity_risk": {"score": 12.0, "flags": []},
        "earnings_volatility_risk": {"score": 30.0, "flags": []},
        "cashflow_instability_risk": {"score": 18.0, "flags": []},
        "hidden_structural_risks": [],
    },
    "TSLA": {
        "composite_risk_score": 74.0, "risk_classification": "high",
        "leverage_risk": {"score": 68.0, "flags": ["High D/E ratio"]},
        "liquidity_risk": {"score": 55.0, "flags": ["Rising inventories"]},
        "earnings_volatility_risk": {"score": 82.0, "flags": ["High EPS variance", "Guidance misses"]},
        "cashflow_instability_risk": {"score": 71.0, "flags": ["Declining FCF"]},
        "hidden_structural_risks": ["Regulatory scrutiny in EU market", "CEO distraction risk"],
    },
    "GOOGL": {
        "composite_risk_score": 41.0, "risk_classification": "moderate",
        "leverage_risk": {"score": 30.0, "flags": []},
        "liquidity_risk": {"score": 22.0, "flags": []},
        "earnings_volatility_risk": {"score": 48.0, "flags": ["Ad revenue cyclicality"]},
        "cashflow_instability_risk": {"score": 35.0, "flags": []},
        "hidden_structural_risks": ["Antitrust litigation exposure"],
    },
    "NVDA": {
        "composite_risk_score": 55.0, "risk_classification": "moderate",
        "leverage_risk": {"score": 30.0, "flags": []},
        "liquidity_risk": {"score": 25.0, "flags": []},
        "earnings_volatility_risk": {"score": 65.0, "flags": ["AI cycle demand uncertainty"]},
        "cashflow_instability_risk": {"score": 42.0, "flags": []},
        "hidden_structural_risks": ["China export restriction risk", "Semiconductor cycle exposure"],
    },
}

# ─── Insights ─────────────────────────────────────────────────────────────────
DEMO_INSIGHTS: dict = {
    "AAPL": {
        "executive_summary": "Apple showcases a formidable balance sheet with strong recurring revenue from Services. Low leverage and stable cash generation underpin the bull case.",
        "strengths": ["Ecosystem lock-in", "Record Services revenue", "Strong FCF generation"],
        "risks": ["China revenue concentration", "Smartphone market saturation"],
        "bull_thesis": ["Services grow to 40% of revenue by 2026", "Vision Pro creates new product category"],
        "bear_thesis": ["China regulatory crackdown", "Innovation slowdown post-Jobs era"],
        "plain_language_summary": "Apple is a financially strong company with low risk. Its growing services business provides stability even as iPhone growth slows.",
    },
    "MSFT": {
        "executive_summary": "Microsoft is a best-in-class cloud platform with Azure growing 28% YoY. AI integration via Copilot creates durable competitive advantage.",
        "strengths": ["Azure market share gains", "AI integration across product suite", "Recurring enterprise contracts"],
        "risks": ["AI cost curve not yet optimized", "Regulatory scrutiny on Activision"],
        "bull_thesis": ["Azure reaches AWS-level margins", "Copilot drives enterprise pricing power"],
        "bear_thesis": ["Cloud growth decelerates", "AI commoditises faster than expected"],
        "plain_language_summary": "Microsoft is a low-risk, high-quality investment driven by cloud and AI. Suitable for conservative and moderate investors.",
    },
    "GOOGL": {
        "executive_summary": "Alphabet's advertising duopoly remains robust. Cloud and Gemini AI provide long-term growth vectors while Search maintains pricing power.",
        "strengths": ["Search advertising dominance", "YouTube monetization", "GCP AI capabilities"],
        "risks": ["Antitrust regulatory pressure", "AI search disruption"],
        "bull_thesis": ["Gemini AI integrates across all surfaces", "GCP reaches profitability inflection"],
        "bear_thesis": ["OpenAI erodes search share", "Regulatory breakup risk"],
        "plain_language_summary": "Google/Alphabet is a moderate-risk tech giant with strong free cash flow. Antitrust is the key near-term risk to watch.",
    },
    "NVDA": {
        "executive_summary": "NVIDIA dominates the AI accelerator market with 80%+ GPU share. Revenue tripled YoY driven by data center demand for H100/H200 chips.",
        "strengths": ["AI chip monopoly", "CUDA software moat", "Data center growth"],
        "risks": ["Export controls to China", "AI bubble risk", "AMD competition"],
        "bull_thesis": ["Blackwell architecture drives next upcycle", "Software margins expand with CUDA ecosystem"],
        "bear_thesis": ["AI capex cycle turns", "Geopolitical restrictions limit addressable market"],
        "plain_language_summary": "NVIDIA is the dominant AI infrastructure play. High growth but also high volatility — suitable for aggressive investors only.",
    },
    "TSLA": {
        "executive_summary": "Tesla faces margin compression and intensifying competition in the EV market. High risk score reflects earnings volatility and leverage concerns.",
        "strengths": ["Brand recognition", "Energy storage growth", "FSD monetization potential"],
        "risks": ["Price war impact on margins", "High operational leverage"],
        "bull_thesis": ["FSD reaches Level 4 autonomy", "Robotaxi network generates new revenue stream"],
        "bear_thesis": ["Margin decline continues into 2025", "BYD gains significant market share"],
        "plain_language_summary": "Tesla has high risk due to earnings volatility and competition. Only invest if you have a high risk tolerance and long time horizon.",
    },
}

# ─── Confidence scores ────────────────────────────────────────────────────────
DEMO_CONFIDENCE: dict = {
    "AAPL":  {"confidence_score": 88.0, "confidence_classification": "high", "data_completeness_pct": 95.0, "contradictions": [], "uncertainty": {"level": "low", "factors": ["Seasonal iPhone revision"]}},
    "MSFT":  {"confidence_score": 91.0, "confidence_classification": "high", "data_completeness_pct": 98.0, "contradictions": [], "uncertainty": {"level": "low", "factors": []}},
    "TSLA":  {"confidence_score": 61.0, "confidence_classification": "moderate", "data_completeness_pct": 88.0, "contradictions": [{"title": "FCF vs expansion capex", "severity": "medium"}], "uncertainty": {"level": "high", "factors": ["Guidance volatility", "Macro sensitivity"]}},
    "GOOGL": {"confidence_score": 78.0, "confidence_classification": "high", "data_completeness_pct": 92.0, "contradictions": [], "uncertainty": {"level": "moderate", "factors": ["Ad market cyclicality"]}},
    "NVDA":  {"confidence_score": 72.0, "confidence_classification": "moderate", "data_completeness_pct": 90.0, "contradictions": [], "uncertainty": {"level": "moderate", "factors": ["AI demand visibility", "Export controls"]}},
}

# ─── Generic fallbacks for unknown tickers ────────────────────────────────────
def _GENERIC_MARKET(t: str) -> dict:
    return {
        "ticker": t, "company_name": f"{t} Corp (Demo)",
        "last_price": 100.0, "price_change_percent": 0.5,
        "volatility_percent": 0.25, "volatility_level": "moderate", "trend_direction": "neutral",
        "moving_averages": {"sma_20": 98.0, "sma_50": 96.0, "sma_200": 90.0},
        "performance": {"one_month": 0.01, "three_month": 0.02, "six_month": 0.04, "one_year": 0.08, "ytd": 0.005},
        "data_points": 252, "last_updated": _NOW,
    }

def _GENERIC_FORECAST(t: str, p: float = 100.0) -> dict:
    return {
        "forecast_horizon_days": 90, "current_price": p,
        "mid_projection": round(p * 1.05, 2),
        "projected_upper_bound": round(p * 1.20, 2),
        "projected_lower_bound": round(p * 0.90, 2),
        "expected_move_percent": 0.15,
        "probability_outlook": {"probability_bullish": 0.55, "probability_bearish": 0.45, "confidence_level": "moderate"},
        "uncertainty": {"uncertainty_percent": 15.0, "classification": "moderate"},
        "based_on": {"volatility_percent": 0.25, "trend_direction": "neutral", "time_horizon": "medium_term"},
    }

_GENERIC_FUNDAMENTALS: dict = {
    "financial_health_score": 55.0, "classification": "moderate", "data_years_used": 0,
    "profitability": {"net_profit_margin": None, "operating_margin": None, "gross_margin": None, "ebitda_margin": None},
    "growth": {"revenue_growth_yoy": None, "revenue_cagr_3y": None, "earnings_growth_yoy": None},
    "capital_efficiency": {"roe": None, "roa": None, "roic": None},
    "cash_flow": {"free_cash_flow": None, "fcf_margin": None, "fcf_growth_yoy": None},
    "leverage": {"debt_to_equity": None, "debt_to_assets": None, "interest_coverage_ratio": None, "classification": "unknown"},
    "liquidity": {"current_ratio": None, "quick_ratio": None, "classification": "unknown"},
}
_GENERIC_RISK: dict = {"composite_risk_score": 50.0, "risk_classification": "moderate", "leverage_risk": {"score": 50.0, "flags": []}, "liquidity_risk": {"score": 50.0, "flags": []}, "earnings_volatility_risk": {"score": 50.0, "flags": []}, "cashflow_instability_risk": {"score": 50.0, "flags": []}, "hidden_structural_risks": []}
_GENERIC_INSIGHTS: dict = {"executive_summary": "Demo mode: No real data available for this ticker.", "strengths": [], "risks": [], "bull_thesis": [], "bear_thesis": [], "plain_language_summary": "Demo data only. Run with a real API key for live analysis."}
_GENERIC_CONFIDENCE: dict = {"confidence_score": 50.0, "confidence_classification": "moderate", "data_completeness_pct": 0.0, "contradictions": [], "uncertainty": {"level": "high", "factors": ["Demo mode active — no live data"]}}


def get_demo_data(ticker: str) -> dict:
    """Return a complete demo analysis payload for any ticker."""
    t = ticker.strip().upper()
    market = DEMO_MARKET.get(t, _GENERIC_MARKET(t))
    price = market.get("last_price", 100.0)
    return {
        "market":       market,
        "forecast":     DEMO_FORECAST.get(t, _GENERIC_FORECAST(t, price)),
        "fundamentals": DEMO_FUNDAMENTALS.get(t, _GENERIC_FUNDAMENTALS),
        "risk":         DEMO_RISK.get(t, _GENERIC_RISK),
        "scenario":     DEMO_SCENARIO.get(t, _make_scenarios(t, 50.0, round(price * 1.05, 2))),
        "insights":     DEMO_INSIGHTS.get(t, _GENERIC_INSIGHTS),
        "confidence":   DEMO_CONFIDENCE.get(t, _GENERIC_CONFIDENCE),
        "comparison":   None,
        "next_step_recommendation": "Run a Deep Analysis for full insights.",
        "demo_mode":    True,
        "demo_note":    f"Pre-built demo data for {t}. Set DEMO_MODE=false + add API keys for live analysis.",
    }


DEMO_TICKERS = list(DEMO_MARKET.keys())
