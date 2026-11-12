"""Look-ahead audit (§9).

Convention (Pre-P1):
  Truncation test — compute features on the full sample, recompute on data
  cut at date t, assert every feature dated ≤ t is identical.
  (Replaces the weak "shift forward and confirm features change" check.)

H5 convention:
  - trough flag at τ uses closes through τ+1 only
  - signal L at asof uses closes through asof−1 only
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from core.features.crowding import distance_from_high, prior_return, realised_vol
from src.monitor.leadership import (
    confirmed_trough_flags,
    leadership_stat,
    trough_flag_at,
)


def _synthetic_prices(n: int = 400, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2024-01-02", periods=n)
    rets = rng.normal(0.0005, 0.02, size=(n, 3))
    prices = 100 * np.exp(np.cumsum(rets, axis=0))
    return pd.DataFrame(prices, index=idx, columns=["AAA", "BBB", "CCC"])


def _feature_frame(px: pd.DataFrame) -> pd.DataFrame:
    return pd.concat(
        [
            prior_return(px, 63).add_suffix("_mom63"),
            distance_from_high(px, 252).add_suffix("_dd"),
            realised_vol(px, 21).add_suffix("_vol21"),
        ],
        axis=1,
    )


def test_truncation_features_identical_on_five_random_dates():
    """Full-sample features dated ≤ t must match features from data cut at t."""
    px = _synthetic_prices()
    full = _feature_frame(px)
    usable = full.dropna().index
    assert len(usable) > 20
    rng = np.random.default_rng(20261108)
    dates = rng.choice(usable.to_numpy(), size=5, replace=False)
    for t in sorted(dates):
        truncated = _feature_frame(px.loc[:t])
        cols = full.columns
        left = full.loc[:t, cols]
        right = truncated.loc[:t, cols]
        # Align on rows present in both (warm-up NaNs OK if both NaN)
        common = left.index.intersection(right.index)
        a = left.loc[common]
        b = right.loc[common]
        # Where either side is NaN, both must be; elsewhere equal
        both_nan = a.isna() & b.isna()
        either_nan = a.isna() | b.isna()
        assert (either_nan == both_nan).all().all(), f"NaN mismatch at cutoff {t}"
        valid = ~either_nan
        if valid.any().any():
            np.testing.assert_allclose(
                a.where(valid).to_numpy(dtype=float),
                b.where(valid).to_numpy(dtype=float),
                rtol=0,
                atol=0,
                equal_nan=True,
                err_msg=f"feature mismatch for truncation at {t}",
            )


def test_distance_from_high_uses_only_history_through_t():
    px = _synthetic_prices()
    dd = distance_from_high(px, 252)
    t = dd.dropna().index[100]
    hist = px.loc[:t]
    window = hist.iloc[-252:]
    expected = window.iloc[-1] / window.max() - 1.0
    np.testing.assert_allclose(dd.loc[t], expected, rtol=1e-10)


def test_crowding_module_has_no_negative_shifts():
    from core.features import crowding

    source = open(crowding.__file__).read()
    assert "shift(-" not in source


def test_h5_trough_flag_uses_closes_through_t_plus_1_only():
    idx = pd.bdate_range("2025-01-02", periods=120)
    # Construct a clear trough at idx[70]
    values = np.linspace(100, 120, 120)
    values[70] = 90.0
    values[71] = 92.0  # confirmation up
    px = pd.Series(values, index=idx)
    τ = idx[70]
    assert trough_flag_at(px, τ) is True
    # Truncation through τ+1 matches full-sample flag for τ
    assert confirmed_trough_flags(px).loc[τ] == confirmed_trough_flags(px.loc[: idx[71]]).loc[τ]
    # Truncation that stops at τ (no confirmation yet) must NOT flag τ
    flags_no_conf = confirmed_trough_flags(px.loc[:τ])
    assert bool(flags_no_conf.loc[τ]) is False


def test_h5_signal_uses_closes_through_asof_minus_1_only():
    idx = pd.bdate_range("2025-01-02", periods=120)
    rng = np.random.default_rng(1)
    suppliers = pd.Series(100 * np.exp(np.cumsum(rng.normal(0, 0.01, 120))), index=idx)
    builders = pd.Series(100 * np.exp(np.cumsum(rng.normal(0, 0.008, 120))), index=idx)
    # Force a trough early enough that L(k) is defined
    suppliers.iloc[50] = suppliers.iloc[50 - 62 : 51].min() - 1.0
    suppliers.iloc[51] = suppliers.iloc[50] + 0.5
    t = idx[90]
    L = leadership_stat(suppliers, builders, k=5, asof=t, beta_window=40)
    cutoff = t - pd.tseries.offsets.BDay(1)
    L_manual = leadership_stat(
        suppliers.loc[:cutoff], builders.loc[:cutoff], k=5, beta_window=40
    )
    if np.isfinite(L) or np.isfinite(L_manual):
        assert L == pytest.approx(L_manual)
    else:
        assert np.isnan(L) and np.isnan(L_manual)
