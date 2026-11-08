"""P3 look-ahead: features at episode start must match truncation at that date."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.config_io import ROOT, episodes
from src.features.build_panel import asof_loc, features_through, universe_tickers
from src.features.liquidity import load_volume_panel


@pytest.fixture(scope="module")
def close_volume():
    prices = pd.read_parquet(ROOT / "data" / "processed" / "prices.parquet")
    prices.index = pd.to_datetime(prices.index).tz_localize(None).normalize()
    tickers = [t for t in universe_tickers() if t in prices.columns]
    close = prices[tickers]
    volume = load_volume_panel(ROOT / "data" / "raw" / "2026-11-07", tickers)
    return close, volume


def test_features_through_matches_full_vs_truncated(close_volume):
    close, volume = close_volume
    eps = episodes()["episodes"]
    # Test every episode start + two mid-sample dates
    dates = [pd.Timestamp(meta["window"][0]) for meta in eps.values()]
    mid = close.index[len(close) // 2]
    dates.append(mid)
    price_cols = [
        "prior_63d_return",
        "dist_252d_high",
        "realised_vol_21d",
        "adv",
    ]
    for dt in dates:
        asof = asof_loc(close.index, dt)
        if asof is None:
            continue
        full = features_through(close, volume, asof)
        trunc = features_through(close.loc[:asof], volume.loc[:asof] if len(volume) else volume, asof)
        for col in price_cols:
            if col not in full.columns:
                continue
            a = full[col].astype(float)
            b = trunc[col].astype(float)
            both_nan = a.isna() & b.isna()
            either_nan = a.isna() | b.isna()
            assert (either_nan == both_nan).all(), f"NaN mismatch {col} @ {asof.date()}"
            valid = ~either_nan
            if valid.any():
                np.testing.assert_allclose(
                    a[valid].to_numpy(),
                    b[valid].to_numpy(),
                    rtol=0,
                    atol=0,
                    equal_nan=True,
                    err_msg=f"{col} mismatch at {asof.date()}",
                )


def test_features_change_when_future_stripped_changes_history(close_volume):
    """Sanity: truncating *before* a date must not equal features at a later asof
    for names with data in between (prior_63d uses the window ending at asof)."""
    close, volume = close_volume
    t1 = asof_loc(close.index, pd.Timestamp("2022-01-03"))
    t2 = asof_loc(close.index, pd.Timestamp("2022-10-14"))
    assert t1 is not None and t2 is not None and t2 > t1
    f1 = features_through(close.loc[:t1], volume.loc[:t1] if len(volume) else volume, t1)
    f2 = features_through(close.loc[:t2], volume.loc[:t2] if len(volume) else volume, t2)
    # NVDA should have different prior_63d at the two dates
    if "NVDA" in f1.index and "NVDA" in f2.index:
        a, b = f1.loc["NVDA", "prior_63d_return"], f2.loc["NVDA", "prior_63d_return"]
        if pd.notna(a) and pd.notna(b):
            assert a != b
