"""Tests for src/power.py (N01) and src/gallery.py (N03)."""
import numpy as np
import pandas as pd
import pytest
from scipy import stats

from src import power as P
from src import gallery as G


@pytest.fixture(scope="module")
def events():
    return {ix: P.load_study1_events(ix) for ix in ("NDX", "SPX")}


# ---------------------------------------------------------------- data/anchors
def test_anchors_pass(events):
    a = P.check_anchors(events)
    assert a["ok"].all() and len(a) == 8


def test_anchor_failure_raises(events):
    bad = {"NDX": events["NDX"].assign(r20=events["NDX"]["r20"] + 0.01)}
    with pytest.raises(AssertionError):
        P.check_anchors(bad)


def test_reclaim_returns_excludes_unreclaimed_and_nan(events):
    ev = events["NDX"]
    x = P.reclaim_returns(ev, 120)
    assert x.size == ev.loc[ev["reclaimed"], "r120"].notna().sum()
    assert x.size < 37 and not np.isnan(x).any()   # the live Nov 2026 event has no r120


# ---------------------------------------------------------------- power / MDE
def test_power_analytic_at_zero_is_alpha():
    assert P.power_analytic(0.0, 40, 0.1) == pytest.approx(0.05, abs=1e-9)


def test_mde_analytic_close_to_normal_approx():
    n, sd = 400, 0.1   # large n: t ~ z
    approx = (stats.norm.ppf(0.95) + stats.norm.ppf(0.8)) * sd / np.sqrt(n)
    assert P.mde_analytic(n, sd) == pytest.approx(approx, rel=0.01)


def test_power_simulated_matches_analytic():
    n, sd, d = 30, 0.1, 0.04
    assert P.power_simulated(d, n, sd, R=20_000, seed=1) == pytest.approx(
        P.power_analytic(d, n, sd), abs=0.015)


def test_mde_simulated_matches_exact_and_tolerance():
    n, sd = 37, 0.2
    sim = P.mde_simulated(n, sd, R=10_000, seed=7)
    assert abs(sim - P.mde_analytic(n, sd)) < 0.004
    Z = P._draws(n, 10_000, 7)
    assert P.power_simulated(sim, n, sd, Z=Z) >= 0.8
    assert P.power_simulated(sim - P.TOL, n, sd, Z=Z) < 0.8


def test_mde_simulated_raises_if_unreachable():
    with pytest.raises(ValueError):
        P.mde_simulated(5, 10.0, hi=0.01, R=500)


def test_mde_scales_with_sd_and_n():
    assert P.mde_analytic(30, 0.2) == pytest.approx(2 * P.mde_analytic(30, 0.1), rel=1e-6)
    assert P.mde_analytic(120, 0.1) < P.mde_analytic(30, 0.1)


def test_mde_table_shape(events):
    t = P.mde_table(events, R=2000)
    assert len(t) == 6 and (t["mde_sim"] > 0).all()
    assert (t["mde_bonf_exact"] > t["mde_exact"]).all()
    assert (t.loc[t["index"] == "NDX", "n"].iloc[0]) == 36   # 37 reclaims; Nov 2026 has no r20 yet


# ---------------------------------------------------------------- TOST
def test_tost_known_case():
    x = np.array([0.0, 0.01, -0.01, 0.005, -0.005] * 20)
    r = P.tost(x, 0.0, 0.02)
    assert r["equivalent"] and r["p_tost"] < 1e-6
    r2 = P.tost(x + 0.03, 0.0, 0.02)
    assert not r2["equivalent"]


def test_tost_matches_ci_rule():
    rng = np.random.default_rng(3)
    for _ in range(50):
        x = rng.normal(rng.uniform(-0.05, 0.05), 0.1, 40)
        r = P.tost(x, 0.0, 0.03)
        inside = (r["ci90_lo"] > -0.03) and (r["ci90_hi"] < 0.03)
        assert r["equivalent"] == inside


def test_tost_symmetry():
    x = np.random.default_rng(4).normal(0.01, 0.05, 30)
    a, b = P.tost(x, 0.0, 0.02), P.tost(-x, 0.0, 0.02)
    assert a["p_lower"] == pytest.approx(b["p_upper"])


def test_bh_qvalues():
    q = P.bh_qvalues([0.01, 0.04, 0.03, 0.5])
    np.testing.assert_allclose(q, [0.04, 0.16 / 3, 0.16 / 3, 0.5], rtol=1e-12)


def test_tost_table_and_ledger(events, tmp_path):
    t = P.tost_table(events)
    assert len(t) == 12
    # nested bounds: equivalence at 2 pts implies equivalence at 5 pts
    w = t.pivot_table(index=["index", "horizon"], columns="bound", values="equivalent")
    assert not ((w[0.02] == 1) & (w[0.05] == 0)).any()
    led = tmp_path / "tests_run.csv"
    led.write_text(",".join(P.LEDGER_COLS) + "\n")
    P.update_ledger(t, led)
    P.update_ledger(t, led)        # idempotent
    df = pd.read_csv(led)
    assert len(df) == 12 and df["test_id"].is_unique


# ---------------------------------------------------------------- gallery
def test_gallery_frame_outcomes(events):
    ev = G.gallery_frame("NDX")
    assert len(ev) == 43
    counts = ev["outcome"].value_counts()
    assert counts["not reclaimed"] == 6
    assert counts.get("reclaimed, retested", 0) == 26          # Study 1 Table 7.2


def test_outcome_profiles_long():
    ev = G.gallery_frame("SPX")
    prof = G.outcome_profiles(ev)
    assert len(prof) == len(ev) * len(G.PROFILE_DAYS)
    assert (prof.loc[prof["day"] == 0, "ret"] == 0).all()


def test_outcome_summary_counts_sum():
    ev = G.gallery_frame("NDX")
    s = G.outcome_summary(ev)
    assert s["events"].sum() == len(ev)


def test_grid_shape():
    assert G.grid_shape(43, 6) == (8, 6)
    assert G.grid_shape(3, 6) == (1, 3)


def test_price_window_rebased_and_truncated():
    idx = pd.bdate_range("2020-01-01", periods=100)
    c = pd.Series(np.linspace(100, 199, 100), index=idx)
    w = G.price_window(c, idx[90], level=100.0, pre=10, post=20)
    assert w["day"].iloc[0] == -10 and w["day"].iloc[-1] == 9      # truncated at data end
    assert w.loc[w["day"] == 0, "rel"].iloc[0] == pytest.approx(c.iloc[90] / 100 - 1)
    with pytest.raises(KeyError):
        G.price_window(c, "1999-01-01", 100.0)


# ---------------------------------------------------------------- cluster MDE (descriptive)
def test_cluster_se_singletons_matches_iid_bootstrap():
    x = np.random.default_rng(5).normal(0, 0.1, 200)
    se, G = P.cluster_bootstrap_se(x, np.arange(200), B=4000, seed=1)
    assert G == 200
    assert se == pytest.approx(x.std(ddof=1) / np.sqrt(200), rel=0.06)


def test_cluster_se_grows_with_within_cluster_correlation():
    rng = np.random.default_rng(6)
    cl = np.repeat(np.arange(20), 5)
    x = np.repeat(rng.normal(0, 0.1, 20), 5) + rng.normal(0, 0.01, 100)   # strong cluster effect
    se, G = P.cluster_bootstrap_se(x, cl, B=3000)
    assert G == 20 and se > 1.8 * x.std(ddof=1) / np.sqrt(100)


def test_cluster_mde_table(events):
    t = P.cluster_mde_table(events, B=500)
    assert len(t) == 6
    assert (t["G"] < t["n"]).all()
    assert (t["mde_cluster_t"] > t["mde_cluster_z"]).all()
    np.testing.assert_allclose(t["mde_cluster_z"] / t["mde_iid_z"], t["se_ratio"])
