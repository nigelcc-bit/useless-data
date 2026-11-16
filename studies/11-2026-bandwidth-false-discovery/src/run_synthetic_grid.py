"""Synthetic null on the deviation grid: bandwidth multiple x minimum pocket size.

PREREG.md, Deviations (16 Nov 2026). Synthetic data only; no stock data.
- Seed 7. Each null dataset: x, y independent N(0, 1), n = 50,000 laid out as
  500 periods x 100 names. Datasets are drawn in the same order as
  tests/test_synthetic.py, so datasets 0-49 are the same as in that test.
- R = 500 datasets. h_cv = LCV bandwidth on dataset 0 (subsample 20,000, seed 7),
  reused for all datasets (identical null DGP).
- For each dataset and bandwidth multiple, E[y|x] is fitted once at every
  observation (kde.cond_mean_binned) and shared across the four pocket sizes.
- Pocket sizes {0.5%, 1%, 2%, 5%}, n_bins = max(200, 4 / min_frac), NW 5 lags.

Writes out/synthetic_null_grid.csv (one row per dataset x cell) and appends one
row per cell to out/runs.csv. Usage, from the study directory:
    python3 -m src.run_synthetic_grid
"""

from __future__ import annotations

import time
from pathlib import Path

import numpy as np
import pandas as pd

from .kde import cond_mean_binned, lcv_bandwidth
from .pattern_hunter import best_pocket, default_n_bins
from .runlog import log_run

SEED = 7
N_DATES, N_NAMES = 500, 100
N = N_DATES * N_NAMES
R = 500
MULTS = [0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 4.0]
MIN_FRACS = [0.005, 0.01, 0.02, 0.05]
SCRIPT = "src/run_synthetic_grid.py"
OUT = Path(__file__).resolve().parents[1] / "out"


def main() -> None:
    rng = np.random.default_rng(SEED)
    dates = np.repeat(np.arange(N_DATES), N_NAMES)
    rows = []
    h_cv = None
    t0 = time.time()
    for rep in range(R):
        x = rng.standard_normal(N)
        y = rng.standard_normal(N)
        if h_cv is None:
            h_cv = lcv_bandwidth(x, y, max_n=20_000, seed=SEED)
            print(f"h_cv = {h_cv:.6f}")
        for m in MULTS:
            h = m * h_cv
            m_obs = cond_mean_binned(x, y, x, h)
            for f in MIN_FRACS:
                p = best_pocket(x, y, h, min_frac=f, dates=dates, m_obs=m_obs)
                rows.append({"rep": rep, "mult": m, "h": h, "min_frac": f,
                             "n_bins": default_n_bins(f), "t_nw": p.t_nw, "lo": p.lo,
                             "hi": p.hi, "frac": p.frac, "mean_ls": p.mean,
                             "n_periods": int(p.returns.size)})
        if (rep + 1) % 50 == 0:
            print(f"  {rep + 1}/{R} datasets, {time.time() - t0:.0f}s")

    df = pd.DataFrame(rows)
    OUT.mkdir(exist_ok=True)
    df.to_csv(OUT / "synthetic_null_grid.csv", index=False)

    cell = df.groupby(["min_frac", "mult"]).agg(
        share_t_gt_2=("t_nw", lambda s: (s > 2).mean()),
        share_t_gt_3=("t_nw", lambda s: (s > 3).mean()),
        median_t=("t_nw", "median"),
        p95_t=("t_nw", lambda s: s.quantile(0.95)),
        max_t=("t_nw", "max"),
        median_periods=("n_periods", "median"),
        min_periods=("n_periods", "min"),
    )
    params = {"case": "null_grid", "n": N, "n_dates": N_DATES, "R": R, "seed": SEED,
              "nw_lags": 5, "h_cv": round(h_cv, 6), "fit": "cond_mean_binned(4096)"}
    for (f, m), r in cell.iterrows():
        log_run(SCRIPT, {**params, "mult": m, "min_frac": f, "n_bins": default_n_bins(f)},
                round(m * h_cv, 6), {k: round(float(v), 4) for k, v in r.items()})

    pd.set_option("display.width", 140)
    print(f"\nNULL GRID  n={N} ({N_DATES} periods x {N_NAMES} names), R={R}, seed={SEED}, h_cv={h_cv:.4f}")
    for col in ["share_t_gt_2", "share_t_gt_3", "median_t", "median_periods"]:
        tab = cell[col].unstack("mult")
        tab.index = [f"{f:.1%}" for f in tab.index]
        tab.columns = [f"{m:g}x" for m in tab.columns]
        print(f"\n{col} (rows: min pocket, cols: bandwidth multiple)")
        print(tab.round(3).to_string())
    print(f"\nTotal time {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
