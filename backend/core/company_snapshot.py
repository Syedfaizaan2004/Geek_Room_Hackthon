"""
backend/core/company_snapshot.py

Generates a concise 5-bullet company snapshot using yfinance data and the LLM.

Strategy:
  1. Try shared yfinance info cache (populated by other tools in same request)
  2. If cache miss, try live yfinance fetch (with 15-min cache write-back)
  3. Build prompt from fetched data; if data is empty, ask LLM to use its own knowledge
  4. Call LLM (Groq with json_object mode for guaranteed JSON; other providers use regex fallback)
  5. On any LLM failure, return a minimal fallback built from whatever info was fetched
"""

import json
import logging
from typing import Dict, Any, Union

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Company info fetching (cache-first)
# ---------------------------------------------------------------------------

def _get_company_info(ticker: str) -> Dict[str, Any]:
    """
    Fetch yfinance .info for a ticker using the shared cache.
    Returns {} if both cache and live fetch fail.
    """
    # 1. Try shared cache populated by financials.py / peer_metrics.py
    try:
        from backend.utils.cache import get_cached_result, cache_result, key_yf_info
        cached = get_cached_result(key_yf_info(ticker))
        if cached:
            return cached
    except Exception:
        pass

    # 2. Live fetch with cache write-back
    try:
        import yfinance as yf
        info = yf.Ticker(ticker).info or {}
        if info and info.get("longName"):
            try:
                from backend.utils.cache import cache_result, key_yf_info
                cache_result(key_yf_info(ticker), info, ttl=900)  # 15 min
            except Exception:
                pass
        return info
    except Exception as e:
        logger.warning("[company_snapshot] Failed to fetch yfinance data for %s: %s", ticker, e)
        return {}


def _build_info_text(ticker: str, info: Dict[str, Any]) -> str:
    """Format yfinance info dict into a text block for the LLM prompt."""
    name     = info.get("longName") or info.get("shortName") or ticker
    sector   = info.get("sector", "N/A")
    industry = info.get("industry", "N/A")
    summary  = info.get("longBusinessSummary", "N/A")
    return (
        f"--- {name} ({ticker}) ---\n"
        f"Business Summary: {summary}\n"
        f"Sector: {sector}\n"
        f"Industry: {industry}\n\n"
    )


# ---------------------------------------------------------------------------
# LLM call with json_object enforcement for Groq
# ---------------------------------------------------------------------------

def _call_snapshot_llm(provider: str, prompt: str) -> str:
    """
    Call the LLM for snapshot generation.
    For Groq: uses response_format=json_object to guarantee JSON output.
    For other providers: falls back to the standard _call_llm path.
    """
    if provider == "groq":
        try:
            from backend.agent.memo_generator import _get_api_key, _get_model
            import httpx

            api_key = _get_api_key("groq")
            if not api_key:
                raise RuntimeError("GROQ_API_KEY not set")

            payload = {
                "model": _get_model("groq"),
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a financial analyst. "
                            "Always respond with valid JSON only — no prose, no markdown, no fences."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.1,
                "max_tokens": 600,
                "response_format": {"type": "json_object"},
            }
            r = httpx.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=20,
            )
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
        except Exception as e:
            logger.warning("[company_snapshot] Groq json_object call failed, falling back: %s", e)

    # Generic fallback for non-Groq or Groq failure
    from backend.agent.memo_generator import _call_llm
    return _call_llm(provider, prompt)


# ---------------------------------------------------------------------------
# Prompt template
# ---------------------------------------------------------------------------

PROMPT_TEMPLATE = """\
You are an expert financial analyst. Summarize the following company information \
into exactly 5 concise, factual bullet points (no marketing language).

The 5 bullets MUST cover in this order:
1. Core business and main products/services
2. Primary revenue drivers
3. Key strategic advantage or competitive moat
4. Competitive position vs peers
5. Major exposure risks or key threats

{context_instruction}

Return ONLY valid JSON in this exact format (no other text):
{{"snapshot": ["bullet 1", "bullet 2", "bullet 3", "bullet 4", "bullet 5"]}}

Company Info:
{info_text}
"""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_company_snapshot(tickers: Union[str, list]) -> Dict[str, Any]:
    """
    Generate a 5-bullet company snapshot via LLM.
    Uses shared yfinance cache; falls back to LLM's own knowledge when data is unavailable.
    Supports a single ticker or a list of tickers.
    """
    if isinstance(tickers, str):
        tickers = [tickers]

    logger.info("[company_snapshot] Generating snapshot for %s", tickers)

    # ------------------------------------------------------------------
    # 1. Collect company info from cache / live yfinance
    # ------------------------------------------------------------------
    summary_text = ""
    has_real_data = False

    for ticker in tickers:
        info = _get_company_info(ticker)
        if info and (info.get("longBusinessSummary") or info.get("longName")):
            summary_text += _build_info_text(ticker, info)
            has_real_data = True
        else:
            # Placeholder so LLM knows which ticker to describe from its own knowledge
            summary_text += f"--- {ticker} ---\n(No live data available — use your training knowledge)\n\n"

    # ------------------------------------------------------------------
    # 2. Get LLM provider
    # ------------------------------------------------------------------
    try:
        from backend.agent.memo_generator import _get_provider
        provider = _get_provider()
    except Exception:
        provider = "disabled"

    if provider == "disabled":
        return _fallback_snapshot(tickers, has_real_data=False)

    # ------------------------------------------------------------------
    # 3. Build prompt — tell LLM whether to rely on data or its own knowledge
    # ------------------------------------------------------------------
    if has_real_data:
        context_instruction = "Use the company info provided below."
    else:
        context_instruction = (
            "Live data is temporarily unavailable. "
            "Use your training knowledge about the ticker(s) listed below to generate accurate bullets."
        )

    prompt = PROMPT_TEMPLATE.format(
        context_instruction=context_instruction,
        info_text=summary_text,
    )

    # ------------------------------------------------------------------
    # 4. Call LLM and parse JSON
    # ------------------------------------------------------------------
    try:
        response_text = _call_snapshot_llm(provider, prompt)

        cleaned = response_text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            cleaned = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

        parsed = None
        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError:
            import re as _re
            m = _re.search(r'\{[\s\S]*"snapshot"[\s\S]*\}', response_text)
            if m:
                try:
                    parsed = json.loads(m.group(0))
                except json.JSONDecodeError:
                    pass

        if parsed is None:
            raise ValueError("No valid JSON found in LLM response")

        snapshot = parsed.get("snapshot", [])
        if not snapshot or not isinstance(snapshot, list) or len(snapshot) == 0:
            raise ValueError("Empty snapshot list in LLM response")

        logger.info(
            "[company_snapshot] LLM snapshot generated for %s (%d bullets)", tickers, len(snapshot)
        )
        return {"snapshot": snapshot[:5]}

    except Exception as e:
        logger.warning("[company_snapshot] LLM snapshot generation failed: %s", e)
        return _fallback_snapshot(tickers, has_real_data=has_real_data)


# ---------------------------------------------------------------------------
# Fallback when LLM fails
# ---------------------------------------------------------------------------

def _fallback_snapshot(tickers: list, has_real_data: bool) -> Dict[str, Any]:
    """Return a minimal, honest fallback snapshot."""
    ticker_str = ", ".join(tickers)
    bullets = [
        f"Analysis for {ticker_str} is temporarily unavailable.",
        "Live data source is currently rate-limited — please retry in a few minutes.",
        "Fundamental analysis data could not be retrieved from the market data provider.",
        "LLM-based summarization could not complete due to a service error.",
        "Please retry the query to get a full company snapshot.",
    ]
    return {"snapshot": bullets[:5]}
