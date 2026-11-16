"""Real-data pattern hunter and within-date placebo on the 28-cell grid.

Development sample only (data/panel_dev.parquet, built by src/build_panel.py,
which never loads 2026 rows). In-sample only: no walk-forward, no costs.

Steps (PREREG.md Method/Placebo + Deviations of 16 Nov 2026):
1. LCV bandwidth h_cv on a 20,000-row subsample of (x, y) normal scores, seed 7.
2. Real grid: bandwidth multiples {0.25, ..., 4} x min pocket {0.5%, 1%, 2%, 5%};
   E[y|x] by kde.cond_mean_binned at every row; periods = dates; NW 5 lags.
   -> out/real_grid.csv
3. Placebo: shuffle y across tickers within each date, rerun the same 28 cells
   with the same h_cv. Replication r uses np.random.default_rng([7, r]).
   Each replication's 28 rows are appended to out/placebo_grid.csv as soon as it
   finishes; completed replications are skipped on restart (resumable).
   Reps 0-2 are timed first; if 500 reps would take > 3 hours, the target is 200.
4. Per cell: real t, placebo share t > 2 and t > 3, the real t's percentile in the
   placebo distribution and the empirical p = (1 + #{placebo t >= real t}) / (1 + R).
   -> out/real_vs_placebo.csv, out/real_vs_placebo.png

Usage (study directory):
    python3 -m src.run_real            # all steps, resumes the placebo
    python3 -m src.run_real --target 500
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

from .kde import cond_mean_binned, lcv_bandwidth
from .pattern_hunter import PocketSearcher, default_n_bins
from .runlog import log_run

STUDY_DIR = Path(__file__).resolve().parents[1]
PANEL = STUDY_DIR / "data" / "panel_dev.parquet"
OUT = STUDY_DIR / "out"
H_CV_FILE = OUT / "real_h_cv.json"
REAL_CSV = OUT / "real_grid.csv"
PLACEBO_CSV = OUT / "placebo_grid.csv"
SUMMARY_CSV = OUT / "real_vs_placebo.csv"
SCRIPT = "src/run_real.py"

SEED = 7
MULTS = [0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 4.0]
MIN_FRACS = [0.005, 0.01, 0.02, 0.05]
FULL_REPS, FALLBACK_REPS, BUDGET_HOURS = 500, 200, 3.0
DEV_END = pd.Timestamp("2025-12-31")


def load_panel():
    p = pd.read_parquet(PANEL, columns=["date", "ticker", "x", "y"])
    p = p[p["x"].notna() & p["y"].notna()].sort_values(["date", "ticker"], kind="stable")
    assert p["date"].max() <= DEV_END, "holdout row in panel"
    codes = pd.factorize(p["date"], sort=True)[0]
    assert np.all(np.diff(codes) >= 0)
    return p["x"].to_numpy(), p["y"].to_numpy(), p["date"].to_numpy(), codes


def get_h_cv(x, y) -> float:
    if H_CV_FILE.exists():
        return float(json.loads(H_CV_FILE.read_text())["h_cv"])
    t0 = time.time()
    h, hs, sc = lcv_bandwidth(x, y, max_n=20_000, seed=SEED, return_path=True)
    H_CV_FILE.write_text(json.dumps({"h_cv": h, "grid": hs.tolist(), "score": sc.tolist()}))
    log_run(SCRIPT, {"step": "lcv_bandwidth", "subsample": 20_000, "seed": SEED, "n": int(x.size)},
            round(h, 6), {"h_cv": round(h, 6), "seconds": round(time.time() - t0, 1)})
    print(f"h_cv = {h:.6f} ({time.time() - t0:.0f}s)")
    return h


def run_grid(S: PocketSearcher, x, y, h_cv):
    rows = []
    for m in MULTS:
        h = m * h_cv
        m_obs = cond_mean_binned(x, y, x, h)
        for f in MIN_FRACS:
            p = S.best(y, m_obs, f)
            rows.append({"mult": m, "h": h, "min_frac": f, "n_bins": default_n_bins(f),
                         "t_nw": p.t_nw, "mean_ls": p.mean, "lo": p.lo, "hi": p.hi,
                         "frac": p.frac, "n_periods": int(p.returns.size)})
    return rows


def shuffle_within_date(y, codes, rng):
    """Panel is sorted by date, so lexsort by (random key, date) permutes y within each date."""
    return y[np.lexsort((rng.random(y.size), codes))]


def placebo(S, x, y, codes, h_cv, target: int | None):
    done = set()
    if PLACEBO_CSV.exists():
        done = set(pd.read_csv(PLACEBO_CSV, usecols=["rep"])["rep"].unique())
    times = []

    def one(rep: int) -> None:
        t0 = time.time()
        ys = shuffle_within_date(y, codes, np.random.default_rng([SEED, rep]))
        rows = [{"rep": rep, **r} for r in run_grid(S, x, ys, h_cv)]
        pd.DataFrame(rows).to_csv(PLACEBO_CSV, mode="a", header=not PLACEBO_CSV.exists(), index=False)
        secs = time.time() - t0
        times.append(secs)
        log_run(SCRIPT, {"step": "placebo", "rep": rep, "seed": [SEED, rep], "cells": 28}, round(h_cv, 6),
                {"t_nw": {f"{r['mult']:g}x_{r['min_frac']:.1%}": round(r["t_nw"], 3) for r in rows},
                 "seconds": round(secs, 1)})
        done.add(rep)

    for rep in range(3):  # timing replications
        if rep not in done:
            one(rep)
    target_file = OUT / "placebo_target.json"
    if target is None and target_file.exists():
        target = int(json.loads(target_file.read_text())["target"])
        print(f"Resuming: target {target} reps (decided on first run).", flush=True)
    elif target is None:
        per_rep = float(np.mean(times))
        est_h = per_rep * FULL_REPS / 3600
        target = FULL_REPS if est_h <= BUDGET_HOURS else FALLBACK_REPS
        target_file.write_text(json.dumps({"target": target, "sec_per_rep": per_rep, "est_hours_500": est_h}))
        log_run(SCRIPT, {"step": "placebo_timing", "reps_timed": 3}, round(h_cv, 6),
                {"sec_per_rep": round(per_rep, 2), "est_hours_500": round(est_h, 3), "target": target})
        print(f"Timing: {per_rep:.1f}s per replication -> {FULL_REPS} reps ~ {est_h:.2f} h "
              f"(budget {BUDGET_HOURS:g} h). Target this run: {target} reps.", flush=True)
    t0 = time.time()
    for rep in range(target):
        if rep in done:
            continue
        one(rep)
        if rep % 25 == 0:
            print(f"  placebo rep {rep + 1}/{target}, {time.time() - t0:.0f}s", flush=True)
    return target


def summarise(h_cv: float) -> pd.DataFrame:
    real = pd.read_csv(REAL_CSV)
    pl = pd.read_csv(PLACEBO_CSV)
    out = []
    for r in real.itertuples():
        t = pl.loc[(pl["mult"] == r.mult) & (pl["min_frac"] == r.min_frac), "t_nw"].to_numpy()
        out.append({"mult": r.mult, "min_frac": r.min_frac, "real_t": r.t_nw, "real_mean_ls": r.mean_ls,
                    "real_lo": r.lo, "real_hi": r.hi, "n_placebo": t.size,
                    "placebo_share_t_gt_2": float((t > 2).mean()),
                    "placebo_share_t_gt_3": float((t > 3).mean()),
                    "placebo_median_t": float(np.median(t)),
                    "placebo_p95_t": float(np.quantile(t, 0.95)),
                    "real_percentile": float((t < r.t_nw).mean()),
                    "emp_p": float((1 + (t >= r.t_nw).sum()) / (1 + t.size))})
    s = pd.DataFrame(out)
    s.to_csv(SUMMARY_CSV, index=False)
    log_run(SCRIPT, {"step": "summary", "n_placebo": int(s["n_placebo"].min())}, round(h_cv, 6),
            {f"{r.mult:g}x_{r.min_frac:.1%}": {"real_t": round(r.real_t, 3), "emp_p": round(r.emp_p, 4)}
             for r in s.itertuples()})
    return s


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", type=int, default=None, help="placebo reps (default: timed rule)")
    args = ap.parse_args()
    OUT.mkdir(exist_ok=True)

    x, y, dates, codes = load_panel()
    print(f"Panel: {x.size:,} rows, {codes.max() + 1:,} dates, last date {pd.Timestamp(dates.max()).date()}",
          flush=True)
    h_cv = get_h_cv(x, y)
    S = PocketSearcher(x, codes)

    if not REAL_CSV.exists():
        real = pd.DataFrame(run_grid(S, x, y, h_cv))
        real.to_csv(REAL_CSV, index=False)
        for r in real.itertuples():
            log_run(SCRIPT, {"step": "real", "mult": r.mult, "min_frac": r.min_frac, "n_bins": r.n_bins},
                    round(r.h, 6), {"t_nw": round(r.t_nw, 4), "mean_ls": round(r.mean_ls, 6),
                                    "lo": round(r.lo, 4), "hi": round(r.hi, 4), "frac": round(r.frac, 5),
                                    "n_periods": r.n_periods})
        print("Real grid written.", flush=True)

    target = placebo(S, x, y, codes, h_cv, args.target)
    s = summarise(h_cv)
    print(f"Done: {s['n_placebo'].min()} placebo reps per cell (target {target}).")


if __name__ == "__main__":
    main()
