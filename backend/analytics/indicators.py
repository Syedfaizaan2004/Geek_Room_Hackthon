"""
analytics/indicators.py — Technical indicator calculations.

Implements:
  1. Simple Moving Averages (SMA 20, 50, 200)
  2. Trend detection (Bullish / Bearish / Neutral)

All functions are pure (no I/O, no side-effects) — easy to unit-test.

SMA MATH:
  SMA(n) = mean(Close[-n:])
  Uses pandas rolling(n, min_periods=n).mean() so only returns NaN
  until n bars of data are available.

TREND LOGIC:
  Bullish:  SMA20 > SMA50  AND  SMA50 > SMA200  ("golden cross alignment")
  Bearish:  SMA20 < SMA50  AND  SMA50 < SMA200  ("death cross alignment")
  Neutral:  any other arrangement (SMAs crossing or not yet aligned)
"""

import logging
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)

# Safely round final float outputs
_DP = 4   # decimal places


def compute_sma(series: pd.Series, window: int) -> Optional[float]:
    """
    Return the most recent Simple Moving Average for the given window.

    Returns None when there are fewer than `window` data points
    (so the route layer can surface a meaningful message instead of NaN).
    """
    if len(series) < window:
        logger.debug("SMA-%d: not enough data (%d bars)", window, len(series))
        return None
    sma_series = series.rolling(window=window, min_periods=window).mean()
    last = sma_series.iloc[-1]
    return round(float(last), _DP) if pd.notna(last) else None


def compute_moving_averages(close: pd.Series) -> dict:
    """
    Compute SMA-20, SMA-50, and SMA-200 from a Close price series.

    Args:
        close: Pandas Series of adjusted closing prices.

    Returns:
        {
          "sma_20":  float | None,
          "sma_50":  float | None,
          "sma_200": float | None,
        }
    """
    return {
        "sma_20":  compute_sma(close, 20),
        "sma_50":  compute_sma(close, 50),
        "sma_200": compute_sma(close, 200),
    }


def detect_trend(sma_20: Optional[float], sma_50: Optional[float], sma_200: Optional[float]) -> str:
    """
    Classify the current trend from the three SMA values.

    Logic:
      Bullish → SMA20 > SMA50 AND SMA50 > SMA200
                 Meaning: short-term momentum is above mid-term,
                 which is above long-term (upward alignment).

      Bearish → SMA20 < SMA50 AND SMA50 < SMA200
                 Meaning: downward alignment across all timeframes.

      Neutral → SMAs are crossing, flat, or insufficient data.

    Args:
        sma_20, sma_50, sma_200: Latest SMA values. None if unavailable.

    Returns:
        "bullish" | "bearish" | "neutral"
    """
    if any(v is None for v in (sma_20, sma_50, sma_200)):
        # Not enough history for a reliable trend signal
        return "neutral"

    if sma_20 > sma_50 > sma_200:      # type: ignore[operator]
        return "bullish"
    if sma_20 < sma_50 < sma_200:      # type: ignore[operator]
        return "bearish"
    return "neutral"
