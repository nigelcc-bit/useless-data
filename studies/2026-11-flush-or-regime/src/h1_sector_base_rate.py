"""H1 — Semis do not inherit the S&P's benign first-shock base rate.

Power check FIRST: report N per conditional cell before looking at returns.
If a conditional cell has N < 8, report as a prior and do not test.
Pooling across indices to manufacture N is forbidden.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ShockSpec:
    abs_threshold: float = -0.04
    sigma_threshold: float = -2.5
    first_shock_window: int = 126
    near_high_band: float = 0.05
    forward_horizon: int = 63
    further_dd: float = -0.10
    min_cell_n: int = 8


def daily_returns(prices: pd.Series) -> pd.Series:
    return prices.pct_change()


def trailing_sigma(returns: pd.Series, window: int = 252) -> pd.Series:
    return returns.rolling(window, min_periods=window).std()


def distance_from_252d_high(prices: pd.Series) -> pd.Series:
    hi = prices.rolling(252, min_periods=252).max()
    return prices / hi - 1.0


def flag_shock_days(returns: pd.Series, prices: pd.Series, spec: ShockSpec) -> pd.DataFrame:
    sig = trailing_sigma(returns)
    abs_hit = returns <= spec.abs_threshold
    sigma_hit = returns <= spec.sigma_threshold * sig
    dist = distance_from_252d_high(prices)
    out = pd.DataFrame(
        {
            "ret": returns,
            "sigma": sig,
            "dist_high": dist,
            "abs_shock": abs_hit,
            "sigma_shock": sigma_hit,
        }
    )
    return out.dropna(subset=["sigma", "dist_high"])


def first_shocks(mask: pd.Series, window: int) -> pd.Series:
    """True on shock days with no other shock in the prior `window` sessions."""
    hits = mask.fillna(False)
    prior = hits.rolling(window, min_periods=1).sum().shift(1).fillna(0)
    return hits & (prior == 0)


def power_check(prices: pd.Series, label: str, spec: ShockSpec | None = None) -> pd.DataFrame:
    """Report N per cell BEFORE inspecting forward returns."""
    spec = spec or ShockSpec()
    rets = daily_returns(prices)
    flagged = flag_shock_days(rets, prices, spec)
    rows = []
    for rule, col in (("abs_-4pct", "abs_shock"), ("sigma_-2.5", "sigma_shock")):
        shock = flagged[col]
        first = first_shocks(shock, spec.first_shock_window)
        near = first & (flagged["dist_high"] >= -spec.near_high_band)
        mid = first & (flagged["dist_high"] >= -0.10) & (flagged["dist_high"] < -spec.near_high_band)
        far = first & (flagged["dist_high"] < -0.10)
        for cell, m in (
            ("all_shocks", shock),
            ("first_shocks", first),
            ("first_within_5pct_high", near),
            ("first_5_to_10pct_below", mid),
            ("first_gt10pct_below", far),
        ):
            n = int(m.sum())
            rows.append(
                {
                    "series": label,
                    "rule": rule,
                    "cell": cell,
                    "n": n,
                    "testable": n >= spec.min_cell_n,
                    "action": "TEST" if n >= spec.min_cell_n else "PRIOR_ONLY_N_LT_8",
                }
            )
    return pd.DataFrame(rows)


def forward_paths(prices: pd.Series, event_mask: pd.Series, horizon: int) -> pd.DataFrame:
    """Return forward cumulative returns and worst drawdown for each event date."""
    events = event_mask[event_mask].index
    records = []
    for t in events:
        loc = prices.index.get_loc(t)
        if isinstance(loc, slice):
            continue
        if loc + horizon >= len(prices):
            continue
        path = prices.iloc[loc : loc + horizon + 1]
        fwd = path.iloc[-1] / path.iloc[0] - 1.0
        worst = (path / path.cummax() - 1.0).min()
        records.append({"date": t, "fwd_ret": fwd, "worst_dd": worst})
    return pd.DataFrame(records)


def main() -> None:
    print("H1 power check requires prices.parquet (P1).")
    print("Until then, known trap stands: SOX ~32y, shocks cluster; expect N 5–12 after conditioning.")
    print("Do not pool SPX/SOX/SMH to manufacture N.")


if __name__ == "__main__":
    main()
