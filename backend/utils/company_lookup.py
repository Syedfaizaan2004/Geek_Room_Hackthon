"""
utils/company_lookup.py — Company name → ticker resolution (Feature 1).

Provides fast fuzzy lookup from company name to ticker symbol.
Priority order:
  1. Static map of 200+ major companies (instant, no network)
  2. yfinance search fallback for unknown companies
"""

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ─── Static map: lowercase company name → (ticker, canonical name) ───────────
COMPANY_MAP: dict[str, tuple[str, str]] = {
    # ── Technology ──────────────────────────────────────────────────────────
    "apple": ("AAPL", "Apple Inc."),
    "apple inc": ("AAPL", "Apple Inc."),
    "microsoft": ("MSFT", "Microsoft Corporation"),
    "microsoft corp": ("MSFT", "Microsoft Corporation"),
    "google": ("GOOGL", "Alphabet Inc."),
    "alphabet": ("GOOGL", "Alphabet Inc."),
    "alphabet inc": ("GOOGL", "Alphabet Inc."),
    "nvidia": ("NVDA", "NVIDIA Corporation"),
    "meta": ("META", "Meta Platforms Inc."),
    "meta platforms": ("META", "Meta Platforms Inc."),
    "facebook": ("META", "Meta Platforms Inc."),
    "amazon": ("AMZN", "Amazon.com Inc."),
    "amazon.com": ("AMZN", "Amazon.com Inc."),
    "tesla": ("TSLA", "Tesla Inc."),
    "tesla inc": ("TSLA", "Tesla Inc."),
    "netflix": ("NFLX", "Netflix Inc."),
    "salesforce": ("CRM", "Salesforce Inc."),
    "adobe": ("ADBE", "Adobe Inc."),
    "intel": ("INTC", "Intel Corporation"),
    "amd": ("AMD", "Advanced Micro Devices Inc."),
    "advanced micro devices": ("AMD", "Advanced Micro Devices Inc."),
    "qualcomm": ("QCOM", "QUALCOMM Inc."),
    "broadcom": ("AVGO", "Broadcom Inc."),
    "applied materials": ("AMAT", "Applied Materials Inc."),
    "micron": ("MU", "Micron Technology Inc."),
    "micron technology": ("MU", "Micron Technology Inc."),
    "oracle": ("ORCL", "Oracle Corporation"),
    "ibm": ("IBM", "International Business Machines"),
    "shopify": ("SHOP", "Shopify Inc."),
    "palantir": ("PLTR", "Palantir Technologies Inc."),
    "snowflake": ("SNOW", "Snowflake Inc."),
    "datadog": ("DDOG", "Datadog Inc."),
    "cloudflare": ("NET", "Cloudflare Inc."),
    "crowdstrike": ("CRWD", "CrowdStrike Holdings Inc."),
    "palo alto networks": ("PANW", "Palo Alto Networks Inc."),
    "palo alto": ("PANW", "Palo Alto Networks Inc."),
    "fortinet": ("FTNT", "Fortinet Inc."),
    "zoom": ("ZM", "Zoom Video Communications"),
    "zoom video": ("ZM", "Zoom Video Communications"),
    "uber": ("UBER", "Uber Technologies Inc."),
    "lyft": ("LYFT", "Lyft Inc."),
    "airbnb": ("ABNB", "Airbnb Inc."),
    "doordash": ("DASH", "DoorDash Inc."),
    "twitter": ("META", "Meta Platforms Inc."),  # acquired
    "x corp": ("META", "Meta Platforms Inc."),
    "pinterest": ("PINS", "Pinterest Inc."),
    "snap": ("SNAP", "Snap Inc."),
    "spotify": ("SPOT", "Spotify Technology S.A."),
    "roblox": ("RBLX", "Roblox Corporation"),
    # ── Finance ──────────────────────────────────────────────────────────────
    "jpmorgan": ("JPM", "JPMorgan Chase & Co."),
    "jp morgan": ("JPM", "JPMorgan Chase & Co."),
    "jpmorgan chase": ("JPM", "JPMorgan Chase & Co."),
    "bank of america": ("BAC", "Bank of America Corporation"),
    "wells fargo": ("WFC", "Wells Fargo & Company"),
    "goldman sachs": ("GS", "The Goldman Sachs Group Inc."),
    "morgan stanley": ("MS", "Morgan Stanley"),
    "citigroup": ("C", "Citigroup Inc."),
    "citi": ("C", "Citigroup Inc."),
    "blackrock": ("BLK", "BlackRock Inc."),
    "visa": ("V", "Visa Inc."),
    "mastercard": ("MA", "Mastercard Inc."),
    "paypal": ("PYPL", "PayPal Holdings Inc."),
    "american express": ("AXP", "American Express Company"),
    "amex": ("AXP", "American Express Company"),
    "berkshire hathaway": ("BRK-B", "Berkshire Hathaway Inc."),
    "berkshire": ("BRK-B", "Berkshire Hathaway Inc."),
    # ── Healthcare ───────────────────────────────────────────────────────────
    "johnson & johnson": ("JNJ", "Johnson & Johnson"),
    "johnson and johnson": ("JNJ", "Johnson & Johnson"),
    "j&j": ("JNJ", "Johnson & Johnson"),
    "pfizer": ("PFE", "Pfizer Inc."),
    "moderna": ("MRNA", "Moderna Inc."),
    "unitedhealth": ("UNH", "UnitedHealth Group Inc."),
    "unitedhealth group": ("UNH", "UnitedHealth Group Inc."),
    "abbvie": ("ABBV", "AbbVie Inc."),
    "merck": ("MRK", "Merck & Co. Inc."),
    "eli lilly": ("LLY", "Eli Lilly and Company"),
    "lilly": ("LLY", "Eli Lilly and Company"),
    "bristol-myers squibb": ("BMY", "Bristol-Myers Squibb Company"),
    "bms": ("BMY", "Bristol-Myers Squibb Company"),
    "amgen": ("AMGN", "Amgen Inc."),
    "biogen": ("BIIB", "Biogen Inc."),
    "illumina": ("ILMN", "Illumina Inc."),
    "intuitive surgical": ("ISRG", "Intuitive Surgical Inc."),
    "medtronic": ("MDT", "Medtronic plc"),
    "abbott": ("ABT", "Abbott Laboratories"),
    "edwards lifesciences": ("EW", "Edwards Lifesciences Corporation"),
    # ── Consumer ─────────────────────────────────────────────────────────────
    "walmart": ("WMT", "Walmart Inc."),
    "target": ("TGT", "Target Corporation"),
    "costco": ("COST", "Costco Wholesale Corporation"),
    "home depot": ("HD", "The Home Depot Inc."),
    "lowes": ("LOW", "Lowe's Companies Inc."),
    "lowe's": ("LOW", "Lowe's Companies Inc."),
    "nike": ("NKE", "Nike Inc."),
    "starbucks": ("SBUX", "Starbucks Corporation"),
    "mcdonalds": ("MCD", "McDonald's Corporation"),
    "mcdonald's": ("MCD", "McDonald's Corporation"),
    "coca-cola": ("KO", "The Coca-Cola Company"),
    "coca cola": ("KO", "The Coca-Cola Company"),
    "pepsi": ("PEP", "PepsiCo Inc."),
    "pepsico": ("PEP", "PepsiCo Inc."),
    "procter & gamble": ("PG", "The Procter & Gamble Company"),
    "procter and gamble": ("PG", "The Procter & Gamble Company"),
    "p&g": ("PG", "The Procter & Gamble Company"),
    "colgate": ("CL", "Colgate-Palmolive Company"),
    "colgate palmolive": ("CL", "Colgate-Palmolive Company"),
    # ── Energy ───────────────────────────────────────────────────────────────
    "exxon": ("XOM", "Exxon Mobil Corporation"),
    "exxon mobil": ("XOM", "Exxon Mobil Corporation"),
    "chevron": ("CVX", "Chevron Corporation"),
    "shell": ("SHEL", "Shell plc"),
    "bp": ("BP", "BP p.l.c."),
    "conocophillips": ("COP", "ConocoPhillips"),
    "marathon oil": ("MRO", "Marathon Oil Corporation"),
    "nextera energy": ("NEE", "NextEra Energy Inc."),
    "duke energy": ("DUK", "Duke Energy Corporation"),
    # ── Automotive ───────────────────────────────────────────────────────────
    "general motors": ("GM", "General Motors Company"),
    "gm": ("GM", "General Motors Company"),
    "ford": ("F", "Ford Motor Company"),
    "ford motor": ("F", "Ford Motor Company"),
    "rivian": ("RIVN", "Rivian Automotive Inc."),
    "lucid": ("LCID", "Lucid Group Inc."),
    "lucid motors": ("LCID", "Lucid Group Inc."),
    "toyota": ("TM", "Toyota Motor Corporation"),
    # ── Other ────────────────────────────────────────────────────────────────
    "boeing": ("BA", "The Boeing Company"),
    "lockheed martin": ("LMT", "Lockheed Martin Corporation"),
    "caterpillar": ("CAT", "Caterpillar Inc."),
    "3m": ("MMM", "3M Company"),
    "ge": ("GE", "GE Aerospace"),
    "general electric": ("GE", "GE Aerospace"),
    "comcast": ("CMCSA", "Comcast Corporation"),
    "disney": ("DIS", "The Walt Disney Company"),
    "walt disney": ("DIS", "The Walt Disney Company"),
    "verizon": ("VZ", "Verizon Communications Inc."),
    "at&t": ("T", "AT&T Inc."),
    "t-mobile": ("TMUS", "T-Mobile US Inc."),
    "tmobile": ("TMUS", "T-Mobile US Inc."),
    "realty income": ("O", "Realty Income Corporation"),
    "prologis": ("PLD", "Prologis Inc."),
}



def _append_unique(
    results: list[dict[str, str]],
    seen_tickers: set[str],
    ticker: str,
    company_name: str,
    limit: int,
) -> None:
    t = (ticker or "").strip().upper()
    if not t or t in seen_tickers or len(results) >= limit:
        return
    results.append({"ticker": t, "company_name": company_name or t})
    seen_tickers.add(t)


def _yfinance_lookup(query: str, limit: int = 6) -> list[dict[str, str]]:
    """
    Dynamic fallback using Yahoo search, then ticker-info fallback.
    """
    items: list[dict[str, str]] = []
    seen: set[str] = set()
    q = query.strip()
    if not q:
        return items

    try:
        import yfinance as yf
    except Exception as exc:
        logger.debug("yfinance import failed for lookup '%s': %s", q, exc)
        return items

    # Prefer Yahoo search for company name and ticker discovery.
    try:
        search = yf.Search(query=q, max_results=max(10, limit * 2))
        quotes = getattr(search, "quotes", []) or []
        for quote in quotes:
            if len(items) >= limit:
                break
            if not isinstance(quote, dict):
                continue
            symbol = (quote.get("symbol") or "").strip().upper()
            quote_type = str(quote.get("quoteType") or quote.get("type") or "").lower()
            if quote_type and quote_type not in {"equity"}:
                continue
            company_name = (
                quote.get("longname")
                or quote.get("shortname")
                or quote.get("name")
                or symbol
            )
            _append_unique(items, seen, symbol, str(company_name), limit)
    except Exception as exc:
        logger.debug("yfinance Search fallback failed for '%s': %s", q, exc)

    # Last resort: treat input as a ticker only when it looks like a symbol.
    ticker_like = (
        " " not in q
        and len(q) <= 10
        and all(ch.isalnum() or ch in ".-" for ch in q)
    )
    if len(items) == 0 and ticker_like:
        try:
            t = yf.Ticker(q.upper())
            info: dict[str, Any] = t.info or {}
            symbol = str(info.get("symbol") or q).upper()
            name = str(info.get("longName") or info.get("shortName") or symbol)
            _append_unique(items, seen, symbol, name, limit)
        except Exception as exc:
            logger.debug("yfinance ticker fallback failed for '%s': %s", q, exc)

    return items


def search_company(query: str) -> Optional[dict]:
    """
    Search for a company by name and return its best ticker match.
    """
    q = query.strip().lower()
    if not q:
        return None

    # 1. Exact match
    if q in COMPANY_MAP:
        ticker, name = COMPANY_MAP[q]
        return {"ticker": ticker, "company_name": name}

    # 2. Prefix match
    prefix_matches = [(k, v) for k, v in COMPANY_MAP.items() if k.startswith(q)]
    if prefix_matches:
        best = min(prefix_matches, key=lambda x: len(x[0]))
        return {"ticker": best[1][0], "company_name": best[1][1]}

    # 3. Substring match
    substr_matches = [(k, v) for k, v in COMPANY_MAP.items() if q in k]
    if substr_matches:
        best = min(substr_matches, key=lambda x: len(x[0]))
        return {"ticker": best[1][0], "company_name": best[1][1]}

    # 4. Dynamic fallback
    dynamic_matches = _yfinance_lookup(query, limit=1)
    return dynamic_matches[0] if dynamic_matches else None


def get_suggestions(query: str, limit: int = 6) -> list[dict]:
    """
    Return autocomplete suggestions as {"ticker": str, "company_name": str}.
    """
    q = query.strip().lower()
    if len(q) < 2:
        return []

    results: list[dict[str, str]] = []
    seen_tickers: set[str] = set()

    # Priority 1: prefix matches from local map
    for name, (ticker, full_name) in COMPANY_MAP.items():
        if name.startswith(q):
            _append_unique(results, seen_tickers, ticker, full_name, limit)

    # Priority 2: substring matches from local map
    for name, (ticker, full_name) in COMPANY_MAP.items():
        if q in name:
            _append_unique(results, seen_tickers, ticker, full_name, limit)

    # Priority 3: dynamic search to avoid strict hardcoded coverage
    if len(results) < limit:
        for item in _yfinance_lookup(query, limit=limit):
            _append_unique(results, seen_tickers, item["ticker"], item["company_name"], limit)

    return results[:limit]
