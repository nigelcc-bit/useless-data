"""Crowding / momentum feature block (H3 regressors 1–3).

No look-ahead: every feature at date t uses prices ≤ t only.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def prior_return(prices: pd.DataFrame, window: int) -> pd.DataFrame:
    """Trailing window total return ending at t."""
    return prices / prices.shift(window) - 1.0


def distance_from_high(prices: pd.DataFrame, window: int) -> pd.DataFrame:
    """Close / trailing window max − 1, using only history through t."""
    roll_max = prices.rolling(window, min_periods=window).max()
    return prices / roll_max - 1.0


def realised_vol(prices: pd.DataFrame, window: int) -> pd.DataFrame:
    """Trailing annualised realised vol of daily log returns."""
    lr = np.log(prices / prices.shift(1))
    return lr.rolling(window, min_periods=window).std() * np.sqrt(252)
