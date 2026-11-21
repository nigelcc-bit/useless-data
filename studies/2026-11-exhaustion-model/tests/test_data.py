"""Data gates (prompt section 2). If these fail, the pipeline stops."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import ingest  # noqa: E402

C = ingest.load_closes()
ASSETS = ["SPX", "NDX", "SOX"]


def ser(a):
    return C[a].dropna()


@pytest.mark.parametrize("a", ASSETS + ["VIX", "VIX3M"])
def test_no_dupes_no_nulls(a):
    s = ser(a)
    assert not s.index.duplicated().any()
    assert s.notna().all() and (s > 0).all()


@pytest.mark.parametrize("a", ASSETS)
def test_max_calendar_gap(a):
    gaps = ser(a).index.to_series().diff().dt.days.dropna()
    # 7 days covers 9/11 (10 Sep -> 17 Sep 2001). Hurricane Sandy (2 days) is inside it.
    assert gaps.max() <= 7, gaps.idxmax()


def test_spx_starts_1950():
    assert ser("SPX").index[0] == pd.Timestamp("1950-01-03")


def test_crash_1987():
    r = ser("SPX").pct_change()
    assert abs(r.loc["1987-10-19"] - (-0.205)) < 0.002
    r = ser("NDX").pct_change()
    assert abs(r.loc["1987-10-19"] - (-0.151)) < 0.002


def test_sox_extremes():
    r = ser("SOX").pct_change().dropna()
    assert r.idxmin() == pd.Timestamp("2020-03-16") and abs(r.min() + 0.159) < 0.002
    assert r.idxmax() == pd.Timestamp("2025-04-09") and abs(r.max() - 0.187) < 0.002


def test_sox_peak():
    s = ser("SOX")
    assert s.idxmax() == pd.Timestamp("2026-06-22") and abs(s.max() - 14634.72) < 0.05


def test_sox_spx_corr():
    r = C[["SPX", "SOX"]].dropna().pct_change().dropna()
    assert abs(r.corr().iloc[0, 1] - 0.71) < 0.04


def test_vix_on_spx_calendar_and_vs_fred():
    v = ser("VIX")
    assert v.index.isin(ser("SPX").index).all()
    f = ingest._fred("fred_VIXCLS.csv")
    j = pd.concat([v, f], axis=1, join="inner").dropna()
    assert (j.iloc[:, 0] - j.iloc[:, 1]).abs().quantile(0.99) < 0.05


def test_vix3m_vs_fred():
    v = ser("VIX3M")
    assert v.index[0] >= pd.Timestamp("2007-12-04")
    f = ingest._fred("fred_VXVCLS.csv")
    j = pd.concat([v, f], axis=1, join="inner").dropna()
    assert (j.iloc[:, 0] - j.iloc[:, 1]).abs().quantile(0.99) < 0.05


def test_ndx_vs_fred():
    f = ingest._fred("fred_NASDAQ100.csv")
    j = pd.concat([ser("NDX"), f], axis=1, join="inner").dropna().loc["2006-01-01":]
    rel = (j.iloc[:, 0] / j.iloc[:, 1] - 1).abs()
    # 1986-2005: FRED NASDAQ100 disagrees with Yahoo on ~360 days (2003-2005 FRED values look
    # date-shifted; Yahoo 2003-12-31 = 1467.92 matches the published close). Logged in the
    # data-gap register; Yahoo is used. From 2006 the two agree.
    assert rel.max() < 0.002


def test_spx_vs_fred_last_decade():
    f = ingest._fred("fred_SP500.csv")
    j = pd.concat([ser("SPX"), f], axis=1, join="inner").dropna()
    assert (j.iloc[:, 0] / j.iloc[:, 1] - 1).abs().max() < 0.002  # one day (2021-08-11) at 0.12%


def test_registration_state():
    s = ser("SPX")
    assert abs(s.loc["2026-11-05"] - 7353.73) < 0.01
    assert abs(s.pct_change().loc["2026-11-05"] + 0.0436) < 0.0005
    x = ser("SOX")
    assert abs(x.loc["2026-11-20"] - 8408.59) < 0.01 and abs(x.loc["2026-11-05"] - 9011.14) < 0.01
    assert abs(ser("VIX").loc["2026-11-20"] - 35.89) < 0.01
    assert abs(ser("VIX").loc["2026-11-20"] / ser("VIX3M").loc["2026-11-20"] - 1.16) < 0.005


def test_monthly():
    m = ingest.load_monthly()
    sp = m["BAA_GS10"].dropna()
    assert abs(sp.min() - 0.29) < 1e-6 and abs(sp.max() - 6.01) < 1e-6
    assert abs(sp.loc["2026-10-01"] - 1.46) < 1e-6
    ff = m["FEDFUNDS"].dropna()
    assert ff.index[0] == pd.Timestamp("1954-07-01")
