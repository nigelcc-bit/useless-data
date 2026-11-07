"""§6.3 data-quality gates for SPEC_LITERAL ETF fixtures.

Name-level and Spearman gates are skipped (D5/D7) until P1 writes RAW_FILE
closes. Fixture *targets* in config/fixtures.yaml are unchanged.
"""

from __future__ import annotations

import pytest

from src.config_io import fixtures
from src.studies.reproduce_nov5 import etf_returns_from_closes

D5 = "D5: name-level YTD and prior-5d inputs unverified (circular reconstruction); panel quarantined"
D7 = "D7: name-level aggregate lacks RAW_FILE source under data/raw/"


@pytest.fixture(scope="module")
def fx():
    return fixtures()


@pytest.fixture(scope="module")
def rets():
    return etf_returns_from_closes()


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


@pytest.mark.skip(reason=D7)
def test_hyperscaler_and_supplier_ew():
    raise AssertionError("unreachable — requires RAW_FILE name panel")


@pytest.mark.skip(reason=D5)
def test_spearman_ytd_gate():
    raise AssertionError("unreachable — CALIBRATED panel quarantined")


@pytest.mark.skip(reason=D5)
def test_spearman_prior5():
    raise AssertionError("unreachable — CALIBRATED panel quarantined")


@pytest.mark.skip(reason=D5)
def test_ai_only_spearmans():
    raise AssertionError("unreachable — CALIBRATED panel quarantined")


@pytest.mark.skip(reason=D7)
def test_distance_from_high_count():
    raise AssertionError("unreachable — requires RAW_FILE name panel")


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


def test_name_level_cross_section_targets_unchanged(fx):
    t = fx["cross_section_targets"]
    assert t["hyperscaler_ew_nov5_pct"] == -3.0
    assert t["supplier_ew_nov5_pct"] == -12.9
    assert t["names_gt20pct_below_52w"] == 21
