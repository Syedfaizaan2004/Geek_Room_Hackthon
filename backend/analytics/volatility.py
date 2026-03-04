"""
analytics/volatility.py — Volatility calculation.

Math for Annualised Volatility:
  1. Compute daily logarithmic returns: ln(Close_t / Close_{t-1})
     (Simple returns (Close_t/Close_{t-1} - 1) are also acceptable for small periods,
     but pct_change() is standard and slightly easier).
  2. Compute standard deviation of these daily returns.
  3. Annualise: multiply by sqrt(252) — roughly 252 trading days in a year.

Classification:
  - Low:      < 15%
  - Moderate: 15% - 30%
  - High:     > 30%
"""

import logging
from typing import Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Constants
_TRADING_DAYS_PER_YEAR = 252


def compute_annualised_volatility(close_prices: pd.Series) -> Tuple[float, str]:
    """
    Compute the historical annualised volatility from a series of daily prices.

    Args:
        close_prices: Pandas Series of daily closing prices.

    Returns:
        Tuple containing:
          - volatility_percent: float (e.g. 0.185 for 18.5%)
          - volatility_level: str ("low", "moderate", "high")

        If insufficient data (less than 2 days), returns (0.0, "low").
    """
    if len(close_prices) < 2:
        logger.debug("Insufficient data for volatility computation.")
        return 0.0, "low"

    # Compute daily returns (pct_change is (p_t - p_{t-1})/p_{t-1})
    daily_returns = close_prices.pct_change().dropna()

    if daily_returns.empty:
        return 0.0, "low"

    # Standard deviation of daily returns
    daily_std = daily_returns.std()

    # Annualise
    annualised_volatility_raw = daily_std * np.sqrt(_TRADING_DAYS_PER_YEAR)
    
    # Ensure it's a native float (not numpy float) and rounded
    volatility_percent = round(float(annualised_volatility_raw), 4)

    # Classify
    if volatility_percent < 0.15:
        level = "low"
    elif volatility_percent <= 0.30:
        level = "moderate"
    else:
        level = "high"

    return volatility_percent, level
