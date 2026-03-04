"""
analytics/performance.py — Multi-timeframe performance metrics.

Formulas:
  return_pct = (last_price - price_at_t) / price_at_t

Handles:
  1-month, 3-month, 6-month, 1-year, and YTD (Year-To-Date) returns.

Robustness:
  If data for exactly 'n' days ago doesn't exist (e.g. weekend), we use the
  closest available data point moving backwards in time. If the dataset 
  doesn't go back that far, the metric will be None.
"""

from datetime import datetime, timezone
import logging
from typing import Optional

import pandas as pd
from dateutil.relativedelta import relativedelta

logger = logging.getLogger(__name__)

_DP = 4 # Decimal places


def _get_return(df: pd.DataFrame, current_price: float, target_date: datetime) -> Optional[float]:
    """
    Look backward from target_date to find the closest available trading day's
    closing price, then compute the percentage return to current_price.
    """
    # Filter for dates less than or equal to target_date
    past_df = df[df.index <= target_date]
    if past_df.empty:
        return None  # Data doesn't go back this far

    # Get the closest price (the last row of the filtered dataframe)
    past_price = float(past_df.iloc[-1]["Close"])
    
    if past_price == 0: # Avoid division by zero
        return None
        
    ret = (current_price - past_price) / past_price
    return round(ret, _DP)


def compute_performance_metrics(df: pd.DataFrame) -> dict:
    """
    Compute historical returns across multiple time horizons.

    Args:
        df: DataFrame containing at least a 'Close' column and a DatetimeIndex.

    Returns:
        dict:
        {
            "one_month":   float | None,
            "three_month": float | None,
            "six_month":   float | None,
            "one_year":    float | None,
            "ytd":         float | None
        }
    """
    if df.empty or "Close" not in df.columns:
        return {
            "one_month": None, "three_month": None,
            "six_month": None, "one_year": None, "ytd": None
        }

    last_dt = df.index[-1]
    current_price = float(df.iloc[-1]["Close"])

    # YTD start date: Last trading day of the previous year
    # (or essentially Dec 31st of previous year).
    ytd_start_date = datetime(last_dt.year - 1, 12, 31, tzinfo=timezone.utc)

    # Calculate target dates
    date_1mo = last_dt - relativedelta(months=1)
    date_3mo = last_dt - relativedelta(months=3)
    date_6mo = last_dt - relativedelta(months=6)
    date_1yr = last_dt - relativedelta(years=1)

    return {
        "one_month": _get_return(df, current_price, date_1mo),
        "three_month": _get_return(df, current_price, date_3mo),
        "six_month": _get_return(df, current_price, date_6mo),
        "one_year": _get_return(df, current_price, date_1yr),
        "ytd": _get_return(df, current_price, ytd_start_date),
    }
