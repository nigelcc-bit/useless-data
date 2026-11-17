"""Walk-forward test of the pattern hunter, with within-date placebo.

Development sample only. Raw prices are read with a Date <= 2025-12-31 filter
(src/build_panel.load_dev); training targets come from data/panel_dev.parquet.

Pipeline for each test year Y = 2005..2025 (PREREG.md Method + Deviations):
1. Training window: dates in [Y-5, Y-1]. Rows whose 5-day target ends in year Y
   are purged (the last 5 trading dates of Y-1), so no test-year price is used.
2. h_cv = LCV bandwidth on the training window only (20,000-row subsample, seed 7).
3. For each of the 28 cells (bandwidth multiple x min pocket): E[y|x] by
   kde.cond_mean_binned, best pocket by PocketSearcher; freeze its [lo, hi].
4. Trading in year Y. Formation day t: the gap x_t is known at the open of t;
   its within-date normal score uses all names with a valid gap that morning.
   Long (equal weight) the names with lo <= score <= hi, short (equal weight)
   the other names with a valid gap; gross 1 per leg, i.e. dollar neutral.
   The cohort is entered at the close of t and held close t -> close t+5,
   which is exactly the pre-registered target y (Close_t to Close_{t+5}).
   Five overlapping cohorts, each 1/5 of capital: weight on day d is
   W_d = (1/5) * sum_{k=1..5} C_{d-k}. Cohorts are held at constant weight
   (no intra-holding drift). A cohort with nobody inside the pocket is cash.
   Cohorts formed in late December of Y-1 (with Y-1's pocket) run into
   January of Y; the series simply stops on 2025-12-31 (no 2026 returns).
5. Daily gross return R_d = sum_i W_{d,i} r_{d,i}, r = Adj Close simple return
   (missing return -> 0). Turnover_d = sum_i |W_d - W_{d-1}| (the weight traded
   at the close of d-1); cost_d = 10bp x turnover_d; net = gross - cost.

Placebo (resumable): the same pipeline with gap scores permuted across names
within each date (rng = default_rng([7, rep])). For the training pairs this is
equivalent in distribution to shuffling y within date; for trading it makes
pocket membership random. Each replication appends 28 rows to
out/wf_placebo.csv and month-end cumulative net paths of the three plotted
cells to out/wf_placebo_paths.csv. Reps 0-1 are timed first; if 100 reps would
take more than 2 hours, the target is 50.

Usage (study directory):  python3 -m src.walk_forward [--target N]
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

from .build_panel import EXCLUDE, HORIZON, RAW_DIR, load_dev, ticker_rows
from .kde import cond_mean_binned, lcv_bandwidth
from .pattern_hunter import PocketSearcher, nw_tstat
from .runlog import log_run

STUDY_DIR = Path(__file__).resolve().parents[1]
PANEL = STUDY_DIR / "data" / "panel_dev.parquet"
OUT = STUDY_DIR / "out"
REAL_RESULTS = OUT / "wf_results.csv"
REAL_DAILY = OUT / "wf_real_daily.parquet"
REAL_POCKETS = OUT / "wf_pockets.csv"
PL_CSV = OUT / "wf_placebo.csv"
PL_PATHS = OUT / "wf_placebo_paths.csv"
PL_TARGET = OUT / "wf_placebo_target.json"
VS_CSV = OUT / "wf_vs_placebo.csv"
SCRIPT = "src/walk_forward.py"

SEED = 7
MULTS = [0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 4.0]
MIN_FRACS = [0.005, 0.01, 0.02, 0.05]
CELLS = [(m, f) for m in MULTS for f in MIN_FRACS]
PLOT_CELLS = [(1.0, 0.005), (1.0, 0.05), (0.25, 0.02)]
YEARS = list(range(2005, 2026))
TRAIN_YEARS = 5
HOLD = 5
COST = 0.001  # 10bp per side, per unit of weight traded
DEV_END = pd.Timestamp("2025-12-31")
FULL_REPS, FALLBACK_REPS, BUDGET_HOURS = 100, 50, 2.0


def cell_key(m: float, f: float) -> str:
    return f"{m:g}x_{f:.1%}"


# ---------------------------------------------------------------- data

def load_data():
    """Wide (date x ticker) gap normal scores and daily returns, plus training rows."""
    xs, rs = {}, {}
    for p in sorted(RAW_DIR.glob("*.parquet")):
        if p.stem in EXCLUDE:
            continue
        df = load_dev(p)
        if len(df) <= HORIZON:
            continue
        tr = ticker_rows(p.stem, df)
        xs[p.stem] = pd.Series(tr["x_raw"].values, index=df.index)
        rs[p.stem] = df["Adj Close"].pct_change()
    X = pd.DataFrame(xs).sort_index()
    R = pd.DataFrame(rs).reindex(index=X.index, columns=X.columns)
    assert X.index.max() <= DEV_END
    rank = X.rank(axis=1, method="average")
    n = X.notna().sum(axis=1)
    XN = norm.ppf(rank.div(n + 1, axis=0))
    dates = X.index.values
    tickers = X.columns

    panel = pd.read_parquet(PANEL, columns=["date", "ticker", "y"])
    panel = panel[panel["y"].notna()]
    ti = pd.Index(dates).get_indexer(panel["date"])
    ni = tickers.get_indexer(panel["ticker"])
    ok = (ti >= 0) & (ni >= 0)
    tr_t, tr_n, tr_y = ti[ok], ni[ok], panel["y"].to_numpy()[ok]
    return dates, tickers, np.asarray(XN), R.to_numpy(), tr_t, tr_n, tr_y


def permute_within_date(XN: np.ndarray, rng) -> np.ndarray:
    out = XN.copy()
    for t in range(out.shape[0]):
        idx = np.flatnonzero(~np.isnan(out[t]))
        out[t, idx] = out[t, idx[rng.permutation(idx.size)]]
    return out


# ---------------------------------------------------------------- pipeline

def fit_years(XN, dates, tr_t, tr_n, tr_y, log_label=None, years_test=None):
    """Per test year: training h_cv and frozen pocket bounds for every cell."""
    years = pd.DatetimeIndex(dates).year.values
    pockets = []
    hcv = {}
    for Y in (YEARS if years_test is None else years_test):
        win = np.flatnonzero((years >= Y - TRAIN_YEARS) & (years <= Y - 1))
        purge_from = win[-HORIZON]  # last HORIZON trading dates of Y-1: target ends in Y
        sel = (tr_t >= win[0]) & (tr_t < purge_from)
        t_i, n_i, y = tr_t[sel], tr_n[sel], tr_y[sel]
        x = XN[t_i, n_i]
        good = ~np.isnan(x)
        t_i, x, y = t_i[good], x[good], y[good]
        t0 = time.time()
        h_cv = lcv_bandwidth(x, y, max_n=20_000, seed=SEED)
        hcv[Y] = h_cv
        S = PocketSearcher(x, t_i)
        for m in MULTS:
            m_obs = cond_mean_binned(x, y, x, m * h_cv)
            for f in MIN_FRACS:
                p = S.best(y, m_obs, f)
                pockets.append({"year": Y, "mult": m, "min_frac": f, "h": m * h_cv, "lo": p.lo,
                                "hi": p.hi, "train_t": p.t_nw, "train_rows": int(x.size)})
        if log_label is not None:
            log_run(SCRIPT, {"step": f"{log_label}_lcv", "test_year": Y, "train": [Y - 5, Y - 1],
                             "purged_last_dates": HORIZON, "subsample": 20_000, "seed": SEED,
                             "train_rows": int(x.size)}, round(h_cv, 6),
                    {"h_cv": round(h_cv, 6), "seconds": round(time.time() - t0, 1)})
    return pd.DataFrame(pockets), hcv


def trade(XN, R, dates, pockets: pd.DataFrame, years_test=None, form_ok=None):
    """Daily gross, net and turnover for every cell, on the stitched OOS period.

    `years_test` (default YEARS) sets the OOS years. `form_ok` (bool per date in
    `dates`, default all True) restricts the days on which cohorts may be formed.
    """
    yt = YEARS if years_test is None else years_test
    years = pd.DatetimeIndex(dates).year.values
    oos = np.flatnonzero((years >= yt[0]) & (years <= yt[-1]))
    d0 = oos[0]
    Xo = XN[d0:]
    Ro = np.nan_to_num(R[d0:], nan=0.0)
    yo = years[d0:]
    valid = ~np.isnan(Xo)
    T = Xo.shape[0]
    res = {}
    for (m, f), g in pockets.groupby(["mult", "min_frac"]):
        lo = np.empty(T)
        hi = np.empty(T)
        for r in g.itertuples():
            sel = yo == r.year
            lo[sel], hi[sel] = r.lo, r.hi
        inside = valid & (Xo >= lo[:, None]) & (Xo <= hi[:, None])
        outside = valid & ~inside
        n_in = inside.sum(1, keepdims=True)
        n_out = outside.sum(1, keepdims=True)
        has = (n_in > 0) & (n_out > 0)
        with np.errstate(invalid="ignore", divide="ignore"):
            C = np.where(inside, 1.0 / n_in, 0.0) - np.where(outside, 1.0 / n_out, 0.0)
        C[~has[:, 0]] = 0.0
        if form_ok is not None:
            C[~np.asarray(form_ok)[d0:]] = 0.0
        cs = np.vstack([np.zeros((1, C.shape[1])), np.cumsum(C, axis=0)])
        # W_d = (1/5) * sum of cohorts formed on d-1..d-5
        idx = np.arange(T)
        W = (cs[idx] - cs[np.maximum(idx - HOLD, 0)]) / HOLD
        gross = (W * Ro).sum(1)
        turn = np.abs(np.diff(np.vstack([np.zeros((1, W.shape[1])), W]), axis=0)).sum(1)
        res[(m, f)] = (gross, gross - COST * turn, turn)
    return pd.DatetimeIndex(dates[d0:]), res


def metrics(days: pd.DatetimeIndex, gross, net, turn) -> dict:
    yr = pd.Series(net, index=days).groupby(days.year).apply(lambda s: np.prod(1 + s) - 1)
    sd = net.std(ddof=1)
    return {"ann_mean_net": net.mean() * 252, "ann_mean_gross": gross.mean() * 252,
            "sharpe_net": net.mean() / sd * np.sqrt(252) if sd > 0 else np.nan,
            "t_nw_net": nw_tstat(net, 5), "t_nw_gross": nw_tstat(gross, 5),
            "avg_turnover": turn.mean(), "share_pos_years": float((yr > 0).mean()),
            "n_days": int(net.size)}


def run_pipeline(XN, R, dates, tr_t, tr_n, tr_y, log_label=None):
    pockets, hcv = fit_years(XN, dates, tr_t, tr_n, tr_y, log_label)
    days, res = trade(XN, R, dates, pockets)
    rows = [{"mult": m, "min_frac": f, **metrics(days, *res[(m, f)])} for (m, f) in CELLS]
    return pd.DataFrame(rows), pockets, hcv, days, res


def month_end_paths(days, res) -> pd.DataFrame:
    out = []
    for m, f in PLOT_CELLS:
        cum = pd.Series(np.cumprod(1 + res[(m, f)][1]) - 1, index=days)
        me = cum.groupby(days.to_period("M")).last()
        out.append(pd.DataFrame({"cell": cell_key(m, f), "month": me.index.astype(str), "cum_net": me.values}))
    return pd.concat(out, ignore_index=True)


# ---------------------------------------------------------------- main

def run_real(data) -> None:
    dates, tickers, XN, R, tr_t, tr_n, tr_y = data
    t0 = time.time()
    res_df, pockets, hcv, days, res = run_pipeline(XN, R, dates, tr_t, tr_n, tr_y, log_label="real")
    res_df.to_csv(REAL_RESULTS, index=False)
    pockets.to_csv(REAL_POCKETS, index=False)
    daily = {}
    for (m, f) in CELLS:
        g, n, tu = res[(m, f)]
        k = cell_key(m, f)
        daily[f"{k}_gross"], daily[f"{k}_net"], daily[f"{k}_turn"] = g, n, tu
    pd.DataFrame(daily, index=days).rename_axis("date").to_parquet(REAL_DAILY)
    for r in res_df.itertuples():
        log_run(SCRIPT, {"step": "real_wf", "mult": r.mult, "min_frac": r.min_frac, "years": [2005, 2025],
                         "cost_bp_per_side": 10}, "per-year h_cv",
                {k: round(float(getattr(r, k)), 5) for k in
                 ["ann_mean_net", "ann_mean_gross", "sharpe_net", "t_nw_net", "t_nw_gross",
                  "avg_turnover", "share_pos_years"]})
    print(f"Real walk-forward done in {time.time() - t0:.0f}s", flush=True)


def run_placebo(data, target):
    dates, tickers, XN, R, tr_t, tr_n, tr_y = data
    done = set(pd.read_csv(PL_CSV, usecols=["rep"])["rep"].unique()) if PL_CSV.exists() else set()
    if PL_PATHS.exists():  # drop any path rows from a rep that did not finish
        paths = pd.read_csv(PL_PATHS)
        paths[paths["rep"].isin(done)].to_csv(PL_PATHS, index=False)
    times = []

    def one(rep: int) -> None:
        t0 = time.time()
        XP = permute_within_date(XN, np.random.default_rng([SEED, rep]))
        res_df, _, hcv, days, res = run_pipeline(XP, R, dates, tr_t, tr_n, tr_y)
        res_df.insert(0, "rep", rep)
        res_df.to_csv(PL_CSV, mode="a", header=not PL_CSV.exists(), index=False)
        pth = month_end_paths(days, res)
        pth.insert(0, "rep", rep)
        pth.to_csv(PL_PATHS, mode="a", header=not PL_PATHS.exists(), index=False)
        secs = time.time() - t0
        times.append(secs)
        log_run(SCRIPT, {"step": "wf_placebo", "rep": rep, "seed": [SEED, rep], "cells": 28}, "per-year h_cv",
                {"t_nw_net": {cell_key(r.mult, r.min_frac): round(r.t_nw_net, 3) for r in res_df.itertuples()},
                 "h_cv": {str(k): round(v, 4) for k, v in hcv.items()}, "seconds": round(secs, 1)})
        done.add(rep)

    for rep in range(2):
        if rep not in done:
            one(rep)
    if target is None and PL_TARGET.exists():
        target = int(json.loads(PL_TARGET.read_text())["target"])
        print(f"Resuming: target {target} reps.", flush=True)
    elif target is None:
        per = float(np.mean(times))
        est = per * FULL_REPS / 3600
        target = FULL_REPS if est <= BUDGET_HOURS else FALLBACK_REPS
        PL_TARGET.write_text(json.dumps({"target": target, "sec_per_rep": per, "est_hours_100": est}))
        log_run(SCRIPT, {"step": "wf_placebo_timing", "reps_timed": 2}, "", {"sec_per_rep": round(per, 1),
                "est_hours_100": round(est, 2), "target": target})
        print(f"Timing: {per:.0f}s per replication -> {FULL_REPS} reps ~ {est:.2f} h "
              f"(budget {BUDGET_HOURS:g} h). Target this run: {target} reps.", flush=True)
    t0 = time.time()
    for rep in range(target):
        if rep not in done:
            one(rep)
            print(f"  wf placebo rep {rep + 1}/{target}, {time.time() - t0:.0f}s", flush=True)
    return target


def summarise() -> pd.DataFrame:
    real = pd.read_csv(REAL_RESULTS)
    pl = pd.read_csv(PL_CSV)
    rows = []
    for r in real.itertuples():
        cell = pl[(pl["mult"] == r.mult) & (pl["min_frac"] == r.min_frac)]
        t = cell["t_nw_net"].to_numpy()
        tg = cell["t_nw_gross"].to_numpy()
        rows.append({"mult": r.mult, "min_frac": r.min_frac, "real_t_net": r.t_nw_net,
                     "real_ann_mean_net": r.ann_mean_net, "real_sharpe_net": r.sharpe_net,
                     "n_placebo": t.size, "placebo_share_t_gt_2": float((t > 2).mean()),
                     "placebo_share_t_gt_3": float((t > 3).mean()),
                     "placebo_median_t": float(np.median(t)),
                     "emp_p": float((1 + (t >= r.t_nw_net).sum()) / (1 + t.size)),
                     # Gross comparison: placebo pays the same ~10%/yr cost on ~zero gross, so
                     # the net-t p mainly tests gross > 0. Gross t vs placebo gross t isolates
                     # the signal from the common cost drag.
                     "real_t_gross": r.t_nw_gross, "real_ann_mean_gross": r.ann_mean_gross,
                     "placebo_share_gross_t_gt_2": float((tg > 2).mean()),
                     "placebo_share_gross_t_gt_3": float((tg > 3).mean()),
                     "emp_p_gross": float((1 + (tg >= r.t_nw_gross).sum()) / (1 + tg.size))})
    s = pd.DataFrame(rows)
    s.to_csv(VS_CSV, index=False)
    log_run(SCRIPT, {"step": "wf_summary", "n_placebo": int(s["n_placebo"].min())}, "per-year h_cv",
            {cell_key(r.mult, r.min_frac): {"t_net": round(r.real_t_net, 3), "emp_p": round(r.emp_p, 4),
                                             "t_gross": round(r.real_t_gross, 3),
                                             "emp_p_gross": round(r.emp_p_gross, 4)}
             for r in s.itertuples()})
    return s


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", type=int, default=None)
    args = ap.parse_args()
    OUT.mkdir(exist_ok=True)
    t0 = time.time()
    data = load_data()
    print(f"Data loaded in {time.time() - t0:.0f}s: {data[2].shape[0]} dates x {data[2].shape[1]} names, "
          f"{data[4].size:,} training rows", flush=True)
    if not REAL_RESULTS.exists():
        run_real(data)
    target = run_placebo(data, args.target)
    s = summarise()
    print(f"Done: {int(s['n_placebo'].min())} placebo reps per cell (target {target}).", flush=True)


if __name__ == "__main__":
    main()
