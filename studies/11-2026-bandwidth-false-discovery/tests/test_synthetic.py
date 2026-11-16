"""Synthetic checks of the estimator. No real stock data is loaded here.

Design (fixed before the first run, 16 Nov 2026):
- Seed 7, n = 50,000 per dataset, arranged as 500 periods x 100 names so the
  long-short series has a time index for Newey-West (5 lags).
- Null case: x, y independent N(0, 1). R = 50 independent datasets. The LCV
  bandwidth h_cv is estimated once, on dataset 0, and reused for all R
  (the null DGP is identical across replications). For each dataset and each
  multiple in {0.25, 0.5, 0.75, 1, 1.5, 2, 4}, record the best_pocket NW t.
  Pass conditions:
    A1  share(t > 3) at 1x h_cv <= 0.20               ("usually below 3")
    A2  share(t > 3) at 0.25x  >  share(t > 3) at 1x  ("often higher")
    A3  t(0.25x) > t(1x) in at least 50% of datasets
- Signal case: y = 0.05 x + N(0, 1). cond_mean at h_cv, evaluated at 200
  quantiles of x between the 2.5% and 97.5% points (avoids Nadaraya-Watson
  boundary bias); OLS slope of fitted values on x must be within 20% of 0.05.
- Density: kde2d on a 301 x 301 grid over [-6, 6]^2 integrates (trapezoid)
  to 1 within 1%, at h_cv and at 0.25x h_cv.

Every check appends to out/runs.csv. Run with:  pytest -s  (from the study dir)
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.kde import cond_mean, kde2d, lcv_bandwidth
from src.pattern_hunter import best_pocket
from src.runlog import log_run

SEED = 7
N_DATES, N_NAMES = 500, 100
N = N_DATES * N_NAMES
R_NULL = 50
MULTS = [0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 4.0]
SCRIPT = "tests/test_synthetic.py"
OUT = Path(__file__).resolve().parents[1] / "out"


@pytest.fixture(scope="module")
def null_sets():
    rng = np.random.default_rng(SEED)
    dates = np.repeat(np.arange(N_DATES), N_NAMES)
    sets = [(rng.standard_normal(N), rng.standard_normal(N)) for _ in range(R_NULL)]
    return dates, sets


@pytest.fixture(scope="module")
def h_cv_null(null_sets):
    _, sets = null_sets
    x0, y0 = sets[0]
    return lcv_bandwidth(x0, y0, max_n=20_000, seed=SEED)


def test_null_pattern_hunter(null_sets, h_cv_null):
    dates, sets = null_sets
    rows = []
    for rep, (x, y) in enumerate(sets):
        for m in MULTS:
            p = best_pocket(x, y, m * h_cv_null, min_frac=0.05, dates=dates)
            rows.append({"rep": rep, "mult": m, "h": m * h_cv_null, "t_nw": p.t_nw,
                         "lo": p.lo, "hi": p.hi, "frac": p.frac, "mean_ls": p.mean})
    df = pd.DataFrame(rows)
    OUT.mkdir(exist_ok=True)
    df.to_csv(OUT / "synthetic_null.csv", index=False)

    tab = df.groupby("mult")["t_nw"].agg(
        median="median", mean="mean", p90=lambda s: s.quantile(0.9), max="max",
        share_t_gt_3=lambda s: (s > 3).mean())
    tab.insert(0, "h", tab.index * h_cv_null)
    tab.insert(1, "t_rep0", df[df.rep == 0].set_index("mult")["t_nw"])
    print(f"\nNULL CASE  n={N} ({N_DATES} periods x {N_NAMES} names), R={R_NULL} datasets, "
          f"seed={SEED}, h_cv={h_cv_null:.4f}")
    print(tab.round(3).to_string())

    params = {"case": "null", "n": N, "n_dates": N_DATES, "R": R_NULL, "seed": SEED,
              "min_frac": 0.05, "nw_lags": 5, "h_cv": round(h_cv_null, 6)}
    for m, r in tab.iterrows():
        log_run(SCRIPT, {**params, "mult": m}, round(r["h"], 6),
                {k: round(float(r[k]), 4) for k in ["t_rep0", "median", "mean", "p90", "max", "share_t_gt_3"]})

    piv = df.pivot(index="rep", columns="mult", values="t_nw")
    share_1, share_q = tab.loc[1.0, "share_t_gt_3"], tab.loc[0.25, "share_t_gt_3"]
    frac_higher = float((piv[0.25] > piv[1.0]).mean())
    print(f"A1 share(t>3) at 1x = {share_1:.2f} (need <= 0.20)")
    print(f"A2 share(t>3) at 0.25x = {share_q:.2f} vs 1x = {share_1:.2f} (need 0.25x > 1x)")
    print(f"A3 t(0.25x) > t(1x) in {frac_higher:.0%} of datasets (need >= 50%)")
    log_run(SCRIPT, {**params, "check": "A1-A3"}, round(h_cv_null, 6),
            {"A1_share_1x": share_1, "A2_share_025x": share_q, "A3_frac_higher": frac_higher})
    assert share_1 <= 0.20
    assert share_q > share_1
    assert frac_higher >= 0.5


def test_signal_slope_recovery():
    rng = np.random.default_rng(SEED)
    x = rng.standard_normal(N)
    y = 0.05 * x + rng.standard_normal(N)
    h = lcv_bandwidth(x, y, max_n=20_000, seed=SEED)
    xe = np.quantile(x, np.linspace(0.025, 0.975, 200))
    slope = float(np.polyfit(xe, cond_mean(x, y, xe, h), 1)[0])
    rel_err = slope / 0.05 - 1
    print(f"\nSIGNAL CASE  y = 0.05x + e, n={N}, h_cv={h:.4f}: slope {slope:.4f} "
          f"(rel. error {rel_err:+.1%}, need within 20%)")
    log_run(SCRIPT, {"case": "signal", "n": N, "seed": SEED, "true_slope": 0.05},
            round(h, 6), {"slope": round(slope, 5), "rel_err": round(rel_err, 4)})
    assert abs(rel_err) < 0.20


@pytest.mark.parametrize("mult", [1.0, 0.25])
def test_density_integrates_to_one(null_sets, h_cv_null, mult):
    _, sets = null_sets
    x, y = sets[0]
    g = np.linspace(-6, 6, 301)
    z = kde2d(x, y, mult * h_cv_null, xg=g, yg=g)
    total = float(np.trapezoid(np.trapezoid(z, g, axis=1), g))
    print(f"\nDENSITY  {mult}x h_cv: integral = {total:.5f}")
    log_run(SCRIPT, {"case": "density", "n": N, "seed": SEED, "grid": "301x301 [-6,6]", "mult": mult},
            round(mult * h_cv_null, 6), {"integral": round(total, 6)})
    assert abs(total - 1) < 0.01
