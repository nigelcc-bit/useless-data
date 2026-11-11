"""H5 leadership statistic — closes only, available before next US open.

Trough rule (fixed Pre-P1, replaces vague "local trough"):
  trough day τ = close[τ] is the lowest close of the prior 63 sessions
  (window [τ-62, τ], inclusive), confirmed by close[τ+1] > close[τ].
  L(k) starts counting *after* the confirmation close: cumulative return
  from close[τ+1] to close[τ+1+k].

Convention asserted in tests:
  - trough flag for day τ uses closes through τ+1 only (needs confirmation).
  - signal L dated at asof uses closes through asof−1 only (APAC pre-order).
  - a trough enters the signal set only once its confirmation date ≤ asof−1.

Implementability gate: no intraday; single pre-order before 5pm HKT.
"""

from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

HKT = ZoneInfo("Asia/Hong_Kong")
TROUGH_LOOKBACK = 63


def _beta_ratio(suppliers: pd.Series, builders: pd.Series, window: int = 63) -> float:
    s = suppliers.pct_change().dropna()
    b = builders.pct_change().dropna()
    aligned = pd.concat([s, b], axis=1, sort=False).dropna().iloc[-window:]
    if len(aligned) < max(20, window // 2):
        return np.nan
    cov = np.cov(aligned.iloc[:, 0], aligned.iloc[:, 1])
    var_b = cov[1, 1]
    if var_b <= 0:
        return np.nan
    beta_s = cov[0, 1] / var_b
    return float(beta_s / 1.0)


def confirmed_trough_flags(
    prices: pd.Series,
    lookback: int = TROUGH_LOOKBACK,
) -> pd.Series:
    """Boolean Series indexed by trough day τ (the low day).

    Flag at τ is True only when:
      1) close[τ] == min(close[τ-lookback+1 : τ])  (lookback sessions incl. τ)
      2) close[τ+1] > close[τ]  (confirmation)

    Computing the flag for τ requires closes through τ+1.
    """
    px = prices.astype(float).dropna()
    flags = pd.Series(False, index=px.index, dtype=bool)
    if len(px) < lookback + 1:
        return flags
    roll_min = px.rolling(lookback, min_periods=lookback).min()
    is_low = px == roll_min
    # confirmation: next close higher — known only at τ+1
    nxt = px.shift(-1)
    confirmed = is_low & nxt.notna() & (nxt > px)
    flags.loc[confirmed.fillna(False)] = True
    return flags


def trough_flag_at(
    prices: pd.Series,
    trough_day: pd.Timestamp,
    lookback: int = TROUGH_LOOKBACK,
) -> bool:
    """Compute trough flag for `trough_day` using only closes through trough_day+1."""
    if trough_day not in prices.index:
        return False
    loc = prices.index.get_loc(trough_day)
    if isinstance(loc, slice) or loc + 1 >= len(prices.index):
        return False
    cutoff = prices.index[loc + 1]
    truncated = prices.loc[:cutoff]
    return bool(confirmed_trough_flags(truncated, lookback=lookback).get(trough_day, False))


def leadership_after_trough(
    suppliers: pd.Series,
    builders: pd.Series,
    trough_day: pd.Timestamp,
    k: int = 5,
    beta_window: int = 63,
) -> float:
    """L(k) for one confirmed trough: cum relative return after confirmation close.

    confirmation = trough_day + 1 business day in the index.
    Window: close[confirmation] → close[confirmation + k].
    """
    if trough_day not in suppliers.index or trough_day not in builders.index:
        return float("nan")
    s_idx = suppliers.index
    loc = s_idx.get_loc(trough_day)
    if isinstance(loc, slice) or loc + 1 + k >= len(s_idx):
        return float("nan")
    conf = s_idx[loc + 1]
    end = s_idx[loc + 1 + k]
    s_cum = suppliers.loc[end] / suppliers.loc[conf] - 1.0
    b_cum = builders.loc[end] / builders.loc[conf] - 1.0
    # beta ratio through confirmation (no peek past end of L window for beta? use through end)
    br = _beta_ratio(suppliers.loc[:end], builders.loc[:end], window=beta_window)
    if not np.isfinite(br) or br == 0:
        return float("nan")
    return float((s_cum - b_cum) / br)


def leadership_stat(
    suppliers: pd.Series,
    builders: pd.Series,
    k: int = 5,
    asof: pd.Timestamp | None = None,
    beta_window: int = 63,
    lookback: int = TROUGH_LOOKBACK,
) -> float:
    """Desk signal: most recent eligible trough's L(k), APAC-safe.

    When `asof` is set, uses closes through asof−1 only. A trough is eligible
    only if its confirmation date ≤ asof−1 (so the trough flag is knowable
    without peeking past the signal cutoff).
    """
    if asof is not None:
        cutoff = asof - pd.tseries.offsets.BDay(1)
        suppliers = suppliers.loc[:cutoff]
        builders = builders.loc[:cutoff]

    if len(suppliers) < lookback + k + 2:
        return float("nan")

    flags = confirmed_trough_flags(suppliers, lookback=lookback)
    # confirmation must already be in the truncated series
    eligible = []
    for τ in flags.index[flags]:
        loc = suppliers.index.get_loc(τ)
        if isinstance(loc, slice):
            continue
        if loc + 1 + k >= len(suppliers.index):
            continue
        # confirmation close is inside series by construction of flags on truncated data
        eligible.append(τ)
    if not eligible:
        return float("nan")
    τ = eligible[-1]
    return leadership_after_trough(
        suppliers, builders, τ, k=k, beta_window=beta_window
    )


def interpret(L5: float, L10: float) -> str:
    """Desk-facing readout. Judgment commentary, not a trade ticket."""
    if not np.isfinite(L5):
        return "INSUFFICIENT_DATA"
    if L5 > 0 and L10 > 0:
        return "FLUSH_BIAS — suppliers leading builders on rebound window"
    if L5 < 0 and L10 < 0:
        return "THESIS_BIAS — builders leading; profit-pool rotation risk"
    return "MIXED — wait for next rebound cluster"


def main() -> None:
    """Delegate to the full daily desk monitor (spec deliverable 5)."""
    from src.monitor.daily_desk import main as desk_main

    desk_main()


if __name__ == "__main__":
    main()
