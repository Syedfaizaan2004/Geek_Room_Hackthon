"""
analytics/market_data.py — yfinance data fetching layer.

Responsibility:
  - Download historical OHLCV data for a ticker
  - Normalise timezone (all timestamps → UTC)
  - Handle errors gracefully with typed exceptions
  - Return a clean pandas DataFrame

This is the ONLY file that imports yfinance.
All other modules consume the DataFrame returned by fetch_price_history().
"""

import logging
from datetime import datetime, timezone

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Custom exceptions (routes map these to HTTP status codes)
# ---------------------------------------------------------------------------
class TickerNotFoundError(Exception):
    """Raised when yfinance returns no data for a given ticker."""


class MarketDataFetchError(Exception):
    """Raised on network failures or unexpected yfinance errors."""


class InsufficientDataError(Exception):
    """Raised when the returned dataset is too small for meaningful analysis."""


# Minimum bars needed for SMA-200 to be meaningful
_MIN_BARS = 30


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def fetch_price_history(
    ticker: str,
    period: str = "1y",
) -> pd.DataFrame:
    """
    Download historical OHLCV data for `ticker` using yfinance.

    Args:
        ticker: Stock/ETF ticker symbol (e.g. "AAPL", "RELIANCE.NS").
        period: yfinance period string — "1mo", "3mo", "6mo", "1y", "2y", "5y".

    Returns:
        DataFrame with columns: Open, High, Low, Close, Volume
        Index: DatetimeIndex (UTC, timezone-aware).

    Raises:
        TickerNotFoundError:    Empty dataset returned by yfinance.
        InsufficientDataError:  Fewer than _MIN_BARS rows returned.
        MarketDataFetchError:   Network or unexpected yfinance error.
    """
    # Validate period string against yfinance accepted values
    _valid_periods = {"1d","5d","1mo","3mo","6mo","1y","2y","5y","10y","ytd","max"}
    if period not in _valid_periods:
        period = "1y"   # Safe default — never crash on bad param

    try:
        tkr = yf.Ticker(ticker)
        # auto_adjust=True → Close is already adjusted for splits/dividends
        df: pd.DataFrame = tkr.history(period=period, auto_adjust=True)
    except Exception as exc:
        logger.error(
            "yfinance fetch failed",
            extra={"ticker": ticker, "period": period, "error": str(exc)},
        )
        raise MarketDataFetchError(
            f"Failed to fetch market data for '{ticker}': {exc}"
        ) from exc

    # Empty result → invalid ticker or no data available
    if df is None or df.empty:
        raise TickerNotFoundError(
            f"No market data found for ticker '{ticker}'. "
            "Verify the symbol is correct and listed on a supported exchange."
        )

    # Normalise to UTC timezone
    if df.index.tzinfo is None:
        df.index = df.index.tz_localize("UTC")
    else:
        df.index = df.index.tz_convert("UTC")

    # Keep only the four essential columns; drop Volume-related extras
    essential = [c for c in ["Open", "High", "Low", "Close", "Volume"] if c in df.columns]
    df = df[essential].sort_index()

    # Drop rows with NaN Close (can appear at market-open edge)
    df = df.dropna(subset=["Close"])

    if len(df) < _MIN_BARS:
        raise InsufficientDataError(
            f"Only {len(df)} data points returned for '{ticker}' (period={period}). "
            f"Need at least {_MIN_BARS} bars for analysis."
        )

    logger.info(
        "Market data fetched",
        extra={"ticker": ticker, "period": period, "rows": len(df)},
    )
    return df


def get_ticker_info(ticker: str) -> dict:
    """
    Fetch basic info (name, sector, currency) from yfinance for enrichment.
    Non-critical — returns empty dict on failure so callers degrade gracefully.
    """
    try:
        info = yf.Ticker(ticker).info
        return {
            "name":       info.get("longName", ticker),
            "sector":     info.get("sector", "Unknown"),
            "currency":   info.get("currency", "USD"),
            "exchange":   info.get("exchange", "Unknown"),
        }
    except Exception:
        return {}
