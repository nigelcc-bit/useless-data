"""Crowding / momentum feature block (H3 regressors 1–3).

No look-ahead: every feature at date t uses prices ≤ t only.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def _causal_ffill(prices: pd.DataFrame) -> pd.DataFrame:
    """Fill internal holes with the prior close only (no backfill / no look-ahead)."""
    return prices.ffill()


def prior_return(prices: pd.DataFrame, window: int) -> pd.DataFrame:
    """Trailing window total return ending at t."""
    px = _causal_ffill(prices)
    return px / px.shift(window) - 1.0


def distance_from_high(prices: pd.DataFrame, window: int) -> pd.DataFrame:
    """Close / trailing window max − 1, using only history through t."""
    px = _causal_ffill(prices)
    roll_max = px.rolling(window, min_periods=window).max()
    return px / roll_max - 1.0


def realised_vol(prices: pd.DataFrame, window: int) -> pd.DataFrame:
    """Trailing annualised realised vol of daily log returns."""
    px = _causal_ffill(prices)
    lr = np.log(px / px.shift(1))
    return lr.rolling(window, min_periods=window).std() * np.sqrt(252)


def short_interest_pct_float(tickers: list[str]) -> pd.Series:
    """Short interest % float — not ingested in P3 coverage → NaN."""
    return pd.Series(
        index=tickers, dtype="float64", name="short_interest_pct_float"
    )
