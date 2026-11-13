"""Engine tests.

1. Synthetic unit tests (always run).
2. Regression against Study 1 Appendix B/C (runs when data/clean/*.csv exist).
   The engine must reproduce every event date, level and outcome; returns are
   compared at the report's 0.1-point rounding.
"""
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from src.events import detect_events, find_breaks, path_stats, PRIMARY, Spec
from src.inference import wilson, placebo_p

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "tests" / "fixtures"
CLEAN = ROOT / "data" / "clean"


# ----------------------------------------------------------------------------
# Synthetic
# ----------------------------------------------------------------------------
def _toy():
    """Flat-ish series with a clear swing low, a break 2 days below it and a reclaim."""
    c = np.full(200, 110.0)
    c[50] = 100.0                      # swing low, will be > 10 days old
    c[150] = 99.0                      # break (first close below 100)
    c[151] = 98.5                      # sweep low
    c[152] = 101.0                     # reclaim
    c[153:] = 105.0
    c[170] = 98.0                      # retest below sweep within 60 days
    return pd.Series(c, index=pd.bdate_range("2000-01-03", periods=200))


def test_toy_event():
    ev = detect_events(_toy(), PRIMARY)
    assert len(ev) == 1
    e = ev.iloc[0]
    assert e["t"] == 150 and e["level"] == 100.0
    assert bool(e["reclaimed"]) and e["entry"] == 152
    assert e["sweep_low"] == 98.5
    assert bool(e["retest"])                      # 98.0 < 98.5 at day 170


def test_min_age_rule_blocks_fresh_lows():
    c = np.linspace(200, 100, 300)                # straight decline: every low is 1 day old
    assert find_breaks(c, PRIMARY) == []


def test_cooldown():
    c = np.full(400, 110.0)
    c[50] = 100.0
    c[150] = 99.0; c[151] = 101.0
    c[160] = 98.0; c[161] = 101.0                 # 10 days later, inside cooldown
    c[200] = 97.0; c[201] = 101.0                 # 50 days later, outside cooldown
    t = [b[0] for b in find_breaks(c, PRIMARY)]
    assert t == [150, 200]


def test_path_stats_matches_detect_events():
    rng = np.random.default_rng(0)
    c = 100 * np.exp(np.cumsum(rng.normal(0, 0.012, 5000)))
    ev = detect_events(pd.Series(c), PRIMARY)
    ps = path_stats(c, PRIMARY)
    res = ev[ev["reclaimed"].notna()]
    assert ps["n_breaks"] == len(res)
    assert ps["reclaim_rate"] == pytest.approx(res["reclaimed"].astype(bool).mean())
    rt = ev["retest"].dropna().astype(bool)
    assert ps["retest_rate"] == pytest.approx(rt.mean())


def test_quantile_levels_run():
    rng = np.random.default_rng(1)
    c = 100 * np.exp(np.cumsum(rng.normal(0, 0.012, 3000)))
    for q in ("q05", "q10", "q20"):
        assert path_stats(c, PRIMARY.with_(level=q))["n_breaks"] > 0


def test_wilson_and_placebo():
    lo, hi = wilson(10, 17)
    assert 0.35 < lo < 0.37 and 0.77 < hi < 0.80      # report: 59% on 17 -> roughly 35-80%
    pool = np.random.default_rng(0).normal(0, 1, 10000)
    assert 0.05 < placebo_p(pool[:50], pool) < 0.95


# ----------------------------------------------------------------------------
# Regression against the Study 1 appendices
# ----------------------------------------------------------------------------
CASES = [("NDX", "ndx_1985_2026.csv", "expected_ndx_events.csv"),
         ("SPX", "spx_1950_2026.csv", "expected_spx_events.csv")]


@pytest.mark.parametrize("name,datafile,fixture", CASES)
def test_reproduces_study1(name, datafile, fixture):
    f = CLEAN / datafile
    if not f.exists():
        pytest.skip(f"{f} not present; copy the Study 1 cleaned series into data/clean/")
    from src.data import _read_close_csv
    s = _read_close_csv(f)
    s = s[s.index <= "2026-11-09"]
    got = detect_events(s, PRIMARY).reset_index(drop=True)
    exp = pd.read_csv(FIX / fixture, parse_dates=["break_date", "entry_date"])
    assert len(got) == len(exp), f"{name}: {len(got)} events vs {len(exp)} expected"
    assert (got["break_date"].values == exp["break_date"].values).all()
    assert (got["entry_date"].values == exp["entry_date"].values).all()
    np.testing.assert_allclose(got["level"], exp["level"], rtol=0, atol=0.006)
    for col in ["break_vs_level", "sweep_vs_level", "dd_at_break", "r20", "r60", "r120", "worst60"]:
        m = exp[col].notna()
        np.testing.assert_allclose(got.loc[m, col], exp.loc[m, col], atol=0.00051,
                                   err_msg=f"{name} {col}")
    for col in ["reclaimed", "retest", "regained_high"]:
        m = exp[col].notna()
        assert (got.loc[m, col].astype(bool).values == exp.loc[m, col].astype(bool).values).all(), col


def test_ndx_recent_events_from_yahoo_cache():
    """Events #33-43 (2020-2026) from the Yahoo cache, for users without the clean files."""
    f = ROOT / "data" / "raw" / "NDX.csv"
    if not f.exists():
        pytest.skip("run `python -m src.data` first to cache ^NDX")
    from src.data import _read_close_csv
    s = _read_close_csv(f)
    s = s[(s.index >= "2019-01-01") & (s.index <= "2026-11-09")]
    got = detect_events(s, PRIMARY).reset_index(drop=True)
    exp = pd.read_csv(FIX / "expected_ndx_events.csv", parse_dates=["break_date", "entry_date"])
    exp = exp[exp["n"] >= 33].reset_index(drop=True)
    assert list(got["break_date"]) == list(exp["break_date"])
    assert list(got["entry_date"]) == list(exp["entry_date"])
    for col in ["sweep_vs_level", "dd_at_break", "r20", "r60", "r120", "worst60"]:
        m = exp[col].notna()
        np.testing.assert_allclose(got.loc[m, col], exp.loc[m, col], atol=0.00051, err_msg=col)
