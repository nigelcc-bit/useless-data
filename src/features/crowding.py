"""Crowding / momentum feature block (H3).

No look-ahead: every feature at date t uses prices ≤ t only.

P3 review policy:
  - Compute returns on each name's **own trading calendar** (dropna).
  - Never compute returns on forward-filled US holiday placeholder dates.
  - If a single-session hole must be aligned for a shared index, ffill is
    capped at 1 session (see ffill_audit.py) — feature math itself does not
    ffill.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# SI dropped pending FINRA back-to-2018 decision; module keeps the name for
# coverage schema compatibility when SI is absent.
SI_DROPPED = True
SI_DEVIATION = "DEVIATION_FROM_SPEC"


def _native_calendar_feature(
    prices: pd.DataFrame,
    fn,
) -> pd.DataFrame:
    """Apply `fn(series) -> series` on each column's dropna calendar, reindex."""
    out = {}
    for col in prices.columns:
        s = prices[col].dropna()
        if s.empty:
            out[col] = pd.Series(dtype="float64")
            continue
        out[col] = fn(s)
    return pd.DataFrame(out).reindex(prices.index)


def prior_return(prices: pd.DataFrame, window: int) -> pd.DataFrame:
    """Trailing window total return ending at t (native calendar)."""

    def _one(s: pd.Series) -> pd.Series:
        return s / s.shift(window) - 1.0

    return _native_calendar_feature(prices, _one)


def distance_from_high(prices: pd.DataFrame, window: int) -> pd.DataFrame:
    """Close / trailing window max − 1 on native calendar."""

    def _one(s: pd.Series) -> pd.Series:
        roll_max = s.rolling(window, min_periods=window).max()
        return s / roll_max - 1.0

    return _native_calendar_feature(prices, _one)


def realised_vol(prices: pd.DataFrame, window: int) -> pd.DataFrame:
    """Trailing annualised realised vol of daily log returns (native calendar)."""

    def _one(s: pd.Series) -> pd.Series:
        lr = np.log(s / s.shift(1))
        return lr.rolling(window, min_periods=window).std() * np.sqrt(252)

    return _native_calendar_feature(prices, _one)


def short_interest_pct_float(tickers: list[str]) -> pd.Series:
    """Placeholder when SI not in crowding block."""
    return pd.Series(
        index=tickers, dtype="float64", name="short_interest_pct_float"
    )


def ffill_cap1(prices: pd.DataFrame) -> pd.DataFrame:
    """Align sparse holes with at most one session of causal ffill (audit only / ADV)."""
    return prices.ffill(limit=1)
