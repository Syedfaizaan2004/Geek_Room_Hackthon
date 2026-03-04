"""
analytics/service.py — Orchestrates market data fetch and analytics computation.

This service retrieves data from yfinance (via market_data.py), computes 
indicators, volatility, and performance, and structures a dict matching the
MarketSnapshotResponse schema.

Integrates simple in-memory caching to avoid hitting yfinance excessively.
"""

from datetime import datetime, timezone
import logging
import time

from analytics.indicators import compute_moving_averages, detect_trend
from analytics.market_data import fetch_price_history, MarketDataFetchError, TickerNotFoundError, InsufficientDataError
from analytics.performance import compute_performance_metrics
from analytics.volatility import compute_annualised_volatility
from schemas.market import MarketSnapshotResponse
from utils.caching import market_cache

logger = logging.getLogger(__name__)


def get_market_snapshot(ticker: str, period: str = "1y") -> MarketSnapshotResponse:
    """
    Fetch market data and compute all analytics for a given ticker.

    Uses an in-memory cache to prevent redundant external API calls.
    Blocks the thread (yfinance is synchronous), so callers should be aware,
    but the caching smooths out request times significantly.

    Args:
        ticker: The asset symbol (e.g., "AAPL").
        period: Time window string for yfinance.

    Returns:
        MarketSnapshotResponse object.

    Raises:
        TickerNotFoundError: If symbol doesn't exist.
        MarketDataFetchError: On network failures.
        InsufficientDataError: If not enough data.
    """
    ticker = ticker.upper().strip()
    cache_key = f"{ticker}:{period}"

    # 1. Check cache
    cached_response = market_cache.get(cache_key)
    if cached_response is not None:
        return cached_response

    # 2. Fetch DataFrame (synchronous yfinance call)
    yf_start = time.perf_counter()
    df = fetch_price_history(ticker, period=period)
    from utils.performance_logger import perf_logger
    perf_logger.record_yfinance((time.perf_counter() - yf_start) * 1000)

    # 3. Compute Analytics
    close_prices = df["Close"]
    last_price = float(close_prices.iloc[-1])
    
    # Calculate daily price change percent points (vs yesterday's close),
    # e.g. 1.23 means +1.23%.
    if len(close_prices) >= 2:
        prev_price = float(close_prices.iloc[-2])
        latest_change = (last_price - prev_price) / prev_price if prev_price != 0 else 0.0
    else:
        latest_change = 0.0

    # Moving Averages & Trend
    ma_dict = compute_moving_averages(close_prices)
    trend = detect_trend(ma_dict["sma_20"], ma_dict["sma_50"], ma_dict["sma_200"])

    # Volatility
    vol_pct, vol_level = compute_annualised_volatility(close_prices)

    # Performance
    perf_dict = compute_performance_metrics(df)

    # 4. Construct Response
    response = MarketSnapshotResponse(
        ticker=ticker,
        last_price=round(last_price, 2),
        price_change_percent=round(latest_change * 100, 4),
        trend_direction=trend,
        volatility_percent=vol_pct,
        volatility_level=vol_level,
        performance=perf_dict,
        moving_averages=ma_dict,
        data_points=len(df),
        last_updated=datetime.now(timezone.utc)
    )

    # 5. Cache and return
    market_cache.set(cache_key, response)
    return response
