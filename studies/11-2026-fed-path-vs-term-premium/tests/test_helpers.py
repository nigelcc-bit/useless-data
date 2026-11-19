"""Synthetic tests for the window helpers: trading-day offsets, weekly sampling, pairwise differencing."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.common import d1_share, one_sided_p, own_diff, pairwise_diff, share, weekly_diff, weekly_last, window


# --- trading-day offsets ----------------------------------------------------

def test_window_counts_trading_days_not_calendar_days():
    idx = pd.bdate_range("2020-01-01", periods=300)
    idx = idx.delete([10, 11, 12])  # holes in the calendar
    t0 = idx[200]
    w = window(idx, t0, 126, 41)
    assert idx.get_loc(t0) - idx.get_loc(w["start"]) == 126
    assert idx.get_loc(w["end"]) - idx.get_loc(t0) == 41
    assert not w["truncated"]


def test_window_cap_truncates_and_flags():
    idx = pd.bdate_range("2026-01-01", "2026-11-20")
    t0 = pd.Timestamp("2026-09-16")
    # weekday calendar: t0 + 41 = 2026-11-12, so a cap on Sunday 2026-11-08 binds at Friday 11-06
    assert window(idx, t0, 126, 41)["end"] == pd.Timestamp("2026-11-12")
    w = window(idx, t0, 126, 41, cap=pd.Timestamp("2026-11-08"))
    assert w["end"] == pd.Timestamp("2026-11-06")
    assert w["truncated"]
    assert w["end_offset"] == idx.get_loc(pd.Timestamp("2026-11-06")) - idx.get_loc(t0)


def test_window_cap_inactive_when_not_binding():
    idx = pd.bdate_range("2026-01-01", "2026-12-31")
    w = window(idx, pd.Timestamp("2026-03-02"), 10, 5, cap=pd.Timestamp("2026-11-13"))
    assert not w["truncated"] and w["end_offset"] == 5


def test_window_rejects_t0_off_calendar_and_short_history():
    idx = pd.bdate_range("2020-01-01", periods=50)
    with pytest.raises(KeyError):
        window(idx, pd.Timestamp("2020-01-04"), 5, 5)  # Saturday
    with pytest.raises(IndexError):
        window(idx, idx[3], 5, 5)


# --- weekly sampling ---------------------------------------------------------

def test_weekly_last_takes_last_available_business_day():
    idx = pd.bdate_range("2026-01-05", "2026-01-23")  # three Mon-Fri weeks
    s = pd.Series(np.arange(len(idx), dtype=float), index=idx)
    s.loc["2026-01-16"] = np.nan  # Friday missing -> Thursday is used
    w = weekly_last(s)
    assert list(w.index) == list(pd.to_datetime(["2026-01-09", "2026-01-16", "2026-01-23"]))
    assert w.loc["2026-01-09"] == s.loc["2026-01-09"]
    assert w.loc["2026-01-16"] == s.loc["2026-01-15"]


def test_weekly_diff_does_not_bridge_an_empty_week():
    idx = pd.bdate_range("2026-01-05", "2026-01-30")
    s = pd.Series(1.0, index=idx)
    s.loc["2026-01-12":"2026-01-16"] = np.nan  # whole week missing
    s.loc["2026-01-19":] = 3.0
    d = weekly_diff(s)
    assert np.isnan(d.loc["2026-01-16"]) and np.isnan(d.loc["2026-01-23"])
    assert d.loc["2026-01-30"] == 0.0


def test_weekly_ignores_weekend_rows():
    s = pd.Series([1.0, 99.0, 2.0], index=pd.to_datetime(["2026-01-09", "2026-01-10", "2026-01-16"]))
    w = weekly_last(s)
    assert w.loc["2026-01-09"] == 1.0 and w.loc["2026-01-16"] == 2.0


# --- pairwise differencing ---------------------------------------------------

def test_own_diff_uses_previous_published_date_without_fill():
    s = pd.Series([1.0, np.nan, 4.0, 5.0], index=pd.bdate_range("2026-01-05", periods=4))
    d = own_diff(s)
    assert list(d.index) == list(pd.to_datetime(["2026-01-07", "2026-01-08"]))
    assert d.loc["2026-01-07"] == 3.0  # from 01-05, the previous published date


def test_pairwise_requires_both_series_on_t():
    idx = pd.bdate_range("2026-01-05", periods=5)
    df = pd.DataFrame({"a": [1.0, 2.0, np.nan, 4.0, 5.0], "b": [10.0, 11.0, 12.0, np.nan, 14.0]}, index=idx)
    d = pairwise_diff(df, ["a", "b"])
    # 01-06 both; 01-07 a missing; 01-08 b missing; 01-09 both (a from 01-08, b from 01-07)
    assert list(d.index) == [idx[1], idx[4]]
    assert d.loc[idx[4], "a"] == 1.0 and d.loc[idx[4], "b"] == 2.0


# --- shares --------------------------------------------------------------------

def test_share_rules():
    assert np.isnan(share(10.0, 24.9)) and share(30.0, 60.0) == 0.5 and share(-30.0, -60.0) == 0.5
    assert d1_share(3.0, -1.0) == 0.75 and np.isnan(d1_share(0.0, 0.0))


def test_one_sided_p():
    assert one_sided_p(2.0, 0.04) == pytest.approx(0.02)
    assert one_sided_p(-2.0, 0.04) == pytest.approx(0.98)
