"""§6.3 data-quality gates. Fail the build if fixtures do not reproduce.

Spearman gates that depended on back-solved YTD / prior5 inputs are skipped
(D5) until P1 ingests real closes. Fixture *targets* are unchanged.
"""

from __future__ import annotations

import pytest

from src.config_io import fixtures
from src.studies.reproduce_nov5 import (
    cross_section_stats,
    etf_returns_from_closes,
    load_panel,
)

D5 = "D5: name-level YTD and prior-5d inputs unverified (circular reconstruction)"


@pytest.fixture(scope="module")
def fx():
    return fixtures()


@pytest.fixture(scope="module")
def rets():
    return etf_returns_from_closes()


@pytest.fixture(scope="module")
def xs():
    return cross_section_stats(load_panel())


def test_soxx_nov5_return(fx, rets):
    g = fx["gates"]
    assert abs(rets["SOXX"] - g["soxx_nov5_ret"]) < g["soxx_tol"]


def test_spy_nov5_return(fx, rets):
    g = fx["gates"]
    assert abs(rets["SPY"] - g["spy_nov5_ret"]) < g["spy_tol"]


def test_qqq_and_smh_nov5(rets):
    assert abs(rets["QQQ"] + 0.065) < 0.002
    assert abs(rets["SMH"] + 0.112) < 0.002


def test_soxx_six_session(fx, rets):
    target = fx["cross_section_targets"]["soxx_six_session_pct"] / 100.0
    assert abs(rets["SOXX_six_session"] - target) < 0.003


def test_log_decline_share_before_nov5(fx, rets):
    target = fx["cross_section_targets"]["log_decline_share_before_nov5"]
    assert abs(rets["soxx_log_decline_share_before_nov5"] - target) < 0.02


def test_hyperscaler_and_supplier_ew(fx, xs):
    t = fx["cross_section_targets"]
    assert abs(xs["hyperscaler_ew_nov5_pct"] - t["hyperscaler_ew_nov5_pct"]) < 0.05
    assert abs(xs["supplier_ew_nov5_pct"] - t["supplier_ew_nov5_pct"]) < 0.15


@pytest.mark.skip(reason=D5)
def test_spearman_ytd_gate(fx, xs):
    assert xs["spearman_nov5_vs_ytd"] < fx["gates"]["spearman_ytd_max"]
    assert abs(xs["spearman_nov5_vs_ytd"] - fx["cross_section_targets"]["spearman_nov5_vs_ytd"]) < 0.05


@pytest.mark.skip(reason=D5)
def test_spearman_prior5(fx, xs):
    t = fx["cross_section_targets"]
    assert abs(xs["spearman_nov5_vs_prior5"] - t["spearman_nov5_vs_prior5"]) < 0.05
    assert xs["spearman_nov5_vs_prior5_p"] < 0.01


@pytest.mark.skip(reason=D5)
def test_ai_only_spearmans(fx, xs):
    t = fx["cross_section_targets"]
    assert abs(xs["spearman_nov5_vs_ytd_ai_only"] - t["spearman_nov5_vs_ytd_ai_only"]) < 0.05
    assert abs(xs["spearman_nov5_vs_prior5_ai_only"] - t["spearman_nov5_vs_prior5_ai_only"]) < 0.05


def test_distance_from_high_count(fx, xs):
    assert xs["names_gt20pct_below_52w"] == fx["cross_section_targets"]["names_gt20pct_below_52w"]


def test_panel_n_and_verified_missingness():
    """Missingness gate on verified columns only — not circular YTD/prior5."""
    df = load_panel()
    assert len(df) == 23
    assert df[["ret_nov5_pct", "dist_52w_high_pct"]].isna().mean().max() < 0.15


def test_ytd_prior5_marked_unverified():
    df = load_panel()
    assert "ytd_source" in df.columns and "prior5_source" in df.columns
    assert (df["ytd_source"] == "CALIBRATED_CIRCULAR").all()
    assert (df["prior5_source"] == "CALIBRATED_CIRCULAR").all()


def test_sp500_event_study_fixture_counts(fx):
    e = fx["sp500_event_study_1928_2019"]
    assert e["n_4pct_days"] == 151
    assert e["first_shock_within_5pct_of_high"]["hits_at_63d"] == 8
    assert e["first_shock_within_5pct_of_high"]["n"] == 9


def test_soxx_press_discrepancy_is_flagged(fx):
    soxx = fx["index_etf_moves_2026_11_05"]["SOXX"]
    assert soxx["move_pct"] == -12.1
    assert soxx["press_quote_pct"] == -12.8
    assert "D1" in soxx["note"]


def test_fixture_spearman_targets_unchanged(fx):
    """Do not edit fixture targets — D5 blocks the test, not the target."""
    t = fx["cross_section_targets"]
    assert t["spearman_nov5_vs_ytd"] == -0.69
    assert t["spearman_nov5_vs_prior5"] == 0.59
    assert t["spearman_nov5_vs_ytd_ai_only"] == -0.76
    assert t["spearman_nov5_vs_prior5_ai_only"] == 0.73
