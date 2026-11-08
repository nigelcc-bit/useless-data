"""P3 look-ahead: features at episode start must match truncation at that date."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.config_io import ROOT, episodes
from src.features.crowding import distance_from_high, prior_return, realised_vol
from src.features.layer import layer_assignments
from src.features.liquidity import adv_dollar, load_volume_panel, resolve_yahoo_raw_dir


def _tickers():
    return sorted(layer_assignments()["ticker"].tolist())


@pytest.fixture(scope="module")
def close_volume():
    from src.features.calendar_hygiene import scrub_processed_price_frames

    scrub_processed_price_frames()
    prices = pd.read_parquet(ROOT / "data" / "processed" / "prices.parquet")
    prices.index = pd.to_datetime(prices.index).tz_localize(None).normalize()
    tickers = [t for t in _tickers() if t in prices.columns]
    close = prices[tickers]
    volume = load_volume_panel(resolve_yahoo_raw_dir(), tickers)
    # Holiday placeholders from ^VIX must not remain in the trading calendar
    for hol in (pd.Timestamp("2026-05-25"), pd.Timestamp("2026-09-07")):
        assert hol not in close.index, f"{hol.date()} still in prices calendar"
    return close, volume


def _feature_pack(close: pd.DataFrame, volume: pd.DataFrame) -> dict[str, pd.DataFrame]:
    return {
        "prior_63d_return": prior_return(close, 63),
        "dist_252d_high": distance_from_high(close, 252),
        "realised_vol_21d": realised_vol(close, 21),
        "adv": adv_dollar(close, volume, 21) if len(volume) else pd.DataFrame(),
    }


def test_truncation_matches_full_at_episode_starts(close_volume):
    close, volume = close_volume
    full = _feature_pack(close, volume)
    eps = episodes()["episodes"]
    dates = [pd.Timestamp(meta["window"][0]) for meta in eps.values()]
    dates.append(close.index[len(close) // 2])
    for dt in dates:
        # asof = last available index ≤ dt
        pos = close.index.searchsorted(dt, side="right") - 1
        if pos < 0:
            continue
        asof = close.index[pos]
        trunc = _feature_pack(close.loc[:asof], volume.loc[:asof] if len(volume) else volume)
        for name, fdf in full.items():
            if fdf.empty or name not in trunc or trunc[name].empty:
                continue
            if asof not in fdf.index or asof not in trunc[name].index:
                continue
            a = fdf.loc[asof].astype(float)
            b = trunc[name].loc[asof].astype(float)
            both_nan = a.isna() & b.isna()
            either_nan = a.isna() | b.isna()
            assert (either_nan == both_nan).all(), f"NaN mismatch {name} @ {asof.date()}"
            valid = ~either_nan
            if valid.any():
                np.testing.assert_allclose(
                    a[valid].to_numpy(),
                    b[valid].to_numpy(),
                    rtol=0,
                    atol=0,
                    equal_nan=True,
                    err_msg=f"{name} mismatch at {asof.date()}",
                )


def test_features_differ_across_episode_starts(close_volume):
    close, volume = close_volume
    t1 = pd.Timestamp("2022-01-03")
    t2 = pd.Timestamp("2022-10-14")
    p1 = close.index.searchsorted(t1, side="right") - 1
    p2 = close.index.searchsorted(t2, side="right") - 1
    a1, a2 = close.index[p1], close.index[p2]
    f1 = prior_return(close.loc[:a1], 63)
    f2 = prior_return(close.loc[:a2], 63)
    if "NVDA" in f1.columns:
        v1, v2 = f1.loc[a1, "NVDA"], f2.loc[a2, "NVDA"]
        if pd.notna(v1) and pd.notna(v2):
            assert v1 != v2


def test_no_unlimited_ffill_in_crowding_source():
    from src.features import crowding

    src = open(crowding.__file__).read()
    assert "ffill()" not in src.replace("ffill(limit=1)", "")
    assert "dropna()" in src
