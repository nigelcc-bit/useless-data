"""Look-ahead audit (§9). Written before study code that consumes features."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.features.crowding import distance_from_high, prior_return, realised_vol


def _synthetic_prices(n: int = 400, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2024-01-02", periods=n)
    rets = rng.normal(0.0005, 0.02, size=(n, 3))
    prices = 100 * np.exp(np.cumsum(rets, axis=0))
    return pd.DataFrame(prices, index=idx, columns=["AAA", "BBB", "CCC"])


def test_features_change_when_frame_shifted_forward():
    px = _synthetic_prices()
    feat = pd.concat(
        [
            prior_return(px, 63).add_suffix("_mom63"),
            distance_from_high(px, 252).add_suffix("_dd"),
            realised_vol(px, 21).add_suffix("_vol21"),
        ],
        axis=1,
    )
    shifted = px.shift(1)
    feat_shift = pd.concat(
        [
            prior_return(shifted, 63).add_suffix("_mom63"),
            distance_from_high(shifted, 252).add_suffix("_dd"),
            realised_vol(shifted, 21).add_suffix("_vol21"),
        ],
        axis=1,
    )
    common = feat.dropna().index.intersection(feat_shift.dropna().index)
    assert len(common) > 50
    delta = (feat.loc[common] - feat_shift.loc[common]).abs().sum().sum()
    assert delta > 0


def test_distance_from_high_uses_only_history_through_t():
    px = _synthetic_prices()
    dd = distance_from_high(px, 252)
    t = dd.dropna().index[100]
    hist = px.loc[:t]
    window = hist.iloc[-252:]
    expected = window.iloc[-1] / window.max() - 1.0
    np.testing.assert_allclose(dd.loc[t], expected, rtol=1e-10)


def test_crowding_module_has_no_negative_shifts():
    from src.features import crowding

    source = open(crowding.__file__).read()
    assert "shift(-" not in source


def test_h5_signal_uses_closes_through_t_minus_1_only():
    from src.monitor.leadership import leadership_stat

    idx = pd.bdate_range("2025-01-02", periods=120)
    rng = np.random.default_rng(1)
    suppliers = pd.Series(100 * np.exp(np.cumsum(rng.normal(0, 0.01, 120))), index=idx)
    builders = pd.Series(100 * np.exp(np.cumsum(rng.normal(0, 0.008, 120))), index=idx)
    t = idx[90]
    L = leadership_stat(suppliers, builders, k=5, asof=t, beta_window=40)
    cutoff = t - pd.tseries.offsets.BDay(1)
    L_manual = leadership_stat(
        suppliers.loc[:cutoff], builders.loc[:cutoff], k=5, beta_window=40
    )
    assert np.isfinite(L)
    assert L == pytest.approx(L_manual)
