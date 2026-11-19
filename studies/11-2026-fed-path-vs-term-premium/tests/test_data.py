"""Data gates. If any fails, the pipeline stops. Fixtures are never adjusted."""
from __future__ import annotations

import pandas as pd
import pytest

from src import load

FX = load.fixtures()
NOMINAL_FRED = ["DGS3MO", "DGS2", "DGS5", "DGS10", "DGS30", "THREEFY2", "THREEFY10"]


@pytest.fixture(scope="module")
def fred():
    return load.fred()


@pytest.fixture(scope="module")
def acm():
    return load.acm()


# --- checksums and row counts ------------------------------------------------

@pytest.mark.parametrize("name", sorted(FX["files"]))
def test_checksum(name):
    assert load.sha256(load.RAW / name) == FX["files"][name]["sha256"]


@pytest.mark.parametrize("name", sorted(FX["files"]))
def test_row_count(name):
    with open(load.RAW / name, "rb") as f:
        n = sum(1 for line in f if line.strip()) - 1  # exclude header
    assert n == FX["files"][name]["rows"]


# --- value fixtures ----------------------------------------------------------

def _cases(block):
    return [(block, v["series"], str(v["date"]), v["value"]) for v in FX[block]["values"]]


@pytest.mark.parametrize("block,series,date,value",
                         _cases("fred") + _cases("acm") + _cases("cross_source"))
def test_fixture(block, series, date, value, fred, acm):
    df = acm if block == "acm" else fred
    got = df.loc[pd.Timestamp(date), series]
    assert abs(got - value) <= FX[block]["tolerance"], f"{series} {date}: got {got!r}, fixture {value!r}"


# --- ACM identity ------------------------------------------------------------

@pytest.mark.parametrize("n", range(1, 11))
def test_acm_identity(n, acm):
    k = f"{n:02d}"
    resid = (acm[f"ACMY{k}"] - acm[f"ACMRNY{k}"] - acm[f"ACMTP{k}"]).dropna()
    assert len(resid) > 0
    assert resid.abs().max() < 1e-6


# --- calendars ---------------------------------------------------------------

@pytest.mark.parametrize("which", ["fred", "acm"])
def test_calendar(which, fred, acm):
    idx = (fred if which == "fred" else acm).index
    assert idx.is_unique
    assert idx.is_monotonic_increasing
    assert (idx.dayofweek < 5).all()


def test_acm_span(acm):
    assert acm.index.min() == pd.Timestamp("1990-01-02")
    assert acm.index.max() == pd.Timestamp("2026-11-17")


# --- ranges and sanity -------------------------------------------------------

def test_yield_ranges(fred, acm):
    """Nominal yields only (real yields and term premia can be below -0.5)."""
    cols = [fred[c] for c in NOMINAL_FRED] + [acm[f"ACMY{n:02d}"] for n in range(1, 11)]
    vals = pd.concat(cols).dropna()
    assert vals.min() >= -0.5
    assert vals.max() <= 20


def test_dgs10_max_daily_change(fred):
    d = fred["DGS10"].dropna().diff().dropna()
    assert d.abs().max() < 1.0


def test_acm_vs_dgs10(fred, acm):
    gap = (acm["ACMY10"] - fred["DGS10"]).dropna().abs()
    assert len(gap) > 8000
    assert gap.median() < 0.25
    assert gap.max() < 1.0


# --- events ------------------------------------------------------------------

def test_first_hikes():
    expected = [pd.Timestamp(str(d)) for d in FX["first_hikes"]]
    assert load.first_hikes() == expected


def test_fomc_gate():
    days = load.fomc_announcement_days("1994-02-04")
    by_year = pd.Series(1, index=days).groupby(days.year).sum()
    assert by_year.index.min() == 1994 and by_year.index.max() == 2026
    for y, n in by_year.items():
        assert n == (7 if y == 2020 else 8), f"{y}: {n} scheduled meetings"
    assert pd.Timestamp("2026-12-09") in days
    assert days.is_unique


def test_fomc_known_fixes():
    d = load.fomc_dates().set_index("date")
    for x in ["2017-02-01", "2017-11-01", "2018-08-01", "2023-02-01", "2023-11-01"]:
        assert d.loc[x, "flag"] == "scheduled", x
    assert d.loc["2003-09-15", "flag"] == "excluded"
    assert d.loc["2003-09-16", "flag"] == "scheduled"
    assert d.loc["2020-03-18", "flag"] == "cancelled"
