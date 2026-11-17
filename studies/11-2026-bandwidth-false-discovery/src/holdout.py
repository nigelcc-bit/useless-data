"""Single holdout run on 2026 (PREREG.md: "Holdout unlocked 17 Nov 2026 ...").

Run once. Refuses to run if out/holdout_results.csv already exists.
`--dry-run` runs the identical pipeline with test year 2025 on development data
only (no 2026 rows are read) and checks the frozen pockets against
out/wf_pockets.csv; it writes nothing except a run-log row.

Pipeline (same code as src/walk_forward.py):
1. Holdout panel: for 2026-01-01 onward, rows built exactly as
   src/build_panel.py does (x = ln(Open_t/Close_t-1), NaN on |Adj/Close ratio
   change| > 0.5%; y = 5-day Adj Close log return minus same-date EW mean;
   within-date normal scores over rows with x and y). Only rows whose t+5 is in
   the data. Saved to data/panel_holdout.parquet (git-ignored).
2. Training 2021-01-01 to 2025-12-31 from data/panel_dev.parquet (targets that
   end in 2026 are not in that panel). LCV h_cv on a 20,000-row subsample,
   seed 7; for each of the 28 cells the best pocket is found and frozen
   (walk_forward.fit_years).
3. Trading 2026 (walk_forward.trade): cohorts formed only on holdout-panel
   dates (t+5 within the data), entered at the close of t, held close t ->
   close t+5, 5 overlapping 1/5-capital cohorts, 10bp per side on traded weight.
   Gap scores are ranked within date over all names with a valid gap that
   morning, as in the walk-forward. The book starts empty on the first 2026 day
   (no carry-over cohorts from December 2025).
4. Spearman correlation between bandwidth multiple and gross NW t over the 28
   cells, for the holdout and for the 2005-2025 walk-forward.

Usage (study directory):  python3 -m src.holdout [--dry-run]
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm, spearmanr

from . import walk_forward as wf
from .build_panel import ADJ_JUMP, EXCLUDE, HORIZON, RAW_DIR, normal_scores, ticker_rows
from .runlog import log_run

STUDY_DIR = Path(__file__).resolve().parents[1]
OUT = STUDY_DIR / "out"
PANEL_DEV = STUDY_DIR / "data" / "panel_dev.parquet"
PANEL_HO = STUDY_DIR / "data" / "panel_holdout.parquet"
RESULTS = OUT / "holdout_results.csv"
SPEARMAN = OUT / "holdout_spearman.csv"
SCRIPT = "src/holdout.py"
HOLDOUT_START = pd.Timestamp("2026-01-01")
READ_FROM = pd.Timestamp("2020-06-01")  # covers the 2021-2025 training window and its first gaps


def load_full():
    """Wide gap scores / returns from READ_FROM to the end of the raw data (includes 2026)."""
    xs, rs, ho_parts = {}, {}, []
    for p in sorted(RAW_DIR.glob("*.parquet")):
        if p.stem in EXCLUDE:
            continue
        df = pd.read_parquet(p, columns=["Open", "Close", "Adj Close"],
                             filters=[("Date", ">=", READ_FROM)]).sort_index()
        if len(df) <= HORIZON:
            continue
        tr = ticker_rows(p.stem, df)
        xs[p.stem] = pd.Series(tr["x_raw"].values, index=df.index)
        rs[p.stem] = df["Adj Close"].pct_change()
        ho_parts.append(tr[tr["date"] >= HOLDOUT_START])
    X = pd.DataFrame(xs).sort_index()
    R = pd.DataFrame(rs).reindex(index=X.index, columns=X.columns)
    rank = X.rank(axis=1, method="average")
    XN = norm.ppf(rank.div(X.notna().sum(axis=1) + 1, axis=0))

    # Holdout panel, exactly as build_panel.main does it.
    ho = pd.concat(ho_parts, ignore_index=True)
    ho = ho[ho["y_raw"].notna()].copy()
    ho["y_dm"] = ho["y_raw"] - ho.groupby("date")["y_raw"].transform("mean")
    both = ho["x_raw"].notna()
    ho["x"], ho["y"] = np.nan, np.nan
    sub = ho[both]
    ho.loc[both, "x"] = normal_scores(sub["x_raw"], sub["date"]).values
    ho.loc[both, "y"] = normal_scores(sub["y_dm"], sub["date"]).values
    ho = ho.sort_values(["date", "ticker"], kind="stable").reset_index(drop=True)
    return X.index.values, X.columns, np.asarray(XN), R.to_numpy(), ho


def training_rows(dates, tickers):
    panel = pd.read_parquet(PANEL_DEV, columns=["date", "ticker", "y"])
    panel = panel[panel["y"].notna()]
    ti = pd.Index(dates).get_indexer(panel["date"])
    ni = tickers.get_indexer(panel["ticker"])
    ok = (ti >= 0) & (ni >= 0)
    return ti[ok], ni[ok], panel["y"].to_numpy()[ok]


def run(dates, tickers, XN, R, form_dates, test_year: int, label: str):
    tr_t, tr_n, tr_y = training_rows(dates, tickers)
    pockets, hcv = wf.fit_years(XN, dates, tr_t, tr_n, tr_y, log_label=label, years_test=[test_year])
    form_ok = pd.Index(dates).isin(form_dates)
    days, res = wf.trade(XN, R, dates, pockets, years_test=[test_year], form_ok=form_ok)
    rows = []
    for (m, f) in wf.CELLS:
        g, n, tu = res[(m, f)]
        met = wf.metrics(days, g, n, tu)
        pk = pockets[(pockets["mult"] == m) & (pockets["min_frac"] == f)].iloc[0]
        rows.append({"mult": m, "min_frac": f, "h": pk["h"],
                     "ann_mean_gross": met["ann_mean_gross"], "ann_mean_net": met["ann_mean_net"],
                     "t_nw_gross": met["t_nw_gross"], "t_nw_net": met["t_nw_net"],
                     "sharpe_net": met["sharpe_net"], "avg_turnover": met["avg_turnover"],
                     "n_days": met["n_days"], "pocket_lo": pk["lo"], "pocket_hi": pk["hi"],
                     "train_t": pk["train_t"]})
    return pd.DataFrame(rows), pockets, hcv[test_year], days


def spearman_table(ho: pd.DataFrame) -> pd.DataFrame:
    wfr = pd.read_csv(wf.REAL_RESULTS)
    out = []
    for name, d in [("holdout_2026", ho), ("walk_forward_2005_2025", wfr)]:
        rho, p = spearmanr(d["mult"], d["t_nw_gross"])
        out.append({"sample": name, "spearman_rho_mult_vs_gross_t": rho, "p_value_naive": p, "n_cells": len(d)})
    return pd.DataFrame(out)


def dry_run() -> None:
    dates, tickers, XN, R, tr_t, tr_n, tr_y = wf.load_data()  # development data only
    panel_dates = pd.read_parquet(PANEL_DEV, columns=["date"])["date"].unique()
    res, pockets, h, days = run(dates, tickers, XN, R, panel_dates, 2025, "holdout_dryrun2025")
    ref = pd.read_csv(wf.REAL_POCKETS, float_precision="round_trip")
    ref = ref[ref["year"] == 2025].set_index(["mult", "min_frac"])
    got = pockets.set_index(["mult", "min_frac"])
    same = bool(np.array_equal(got[["lo", "hi"]].values, ref.loc[got.index, ["lo", "hi"]].values))
    log_run(SCRIPT, {"step": "dry_run", "test_year": 2025, "train": [2020, 2024]}, round(h, 6),
            {"pockets_match_walk_forward_2025": same, "n_days": int(days.size)})
    print(f"Dry run (test 2025, dev data only): h_cv={h:.6f}; pockets identical to walk-forward 2025: {same}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if args.dry_run:
        dry_run()
        return
    unlock = "Holdout unlocked 17 Nov 2026 by Nigel"
    assert unlock in (STUDY_DIR / "PREREG.md").read_text(), "PREREG.md has no holdout unlock line"
    if RESULTS.exists():
        raise SystemExit(f"{RESULTS.name} exists: the holdout is run once only.")

    t0 = time.time()
    dates, tickers, XN, R, ho = load_full()
    ho.to_parquet(PANEL_HO, index=False)
    form_dates = ho.loc[ho["x"].notna(), "date"].unique()
    log_run(SCRIPT, {"step": "holdout_panel", "from": str(HOLDOUT_START.date()), "adj_jump": ADJ_JUMP,
                     "horizon": HORIZON}, "",
            {"rows": int(len(ho)), "rows_xy": int(ho["x"].notna().sum()), "dates": int(ho["date"].nunique()),
             "first_date": str(pd.Timestamp(ho["date"].min()).date()),
             "last_date": str(pd.Timestamp(ho["date"].max()).date()),
             "tickers": int(ho["ticker"].nunique())})

    res, pockets, h, days = run(dates, tickers, XN, R, form_dates, 2026, "holdout")
    res.to_csv(RESULTS, index=False)
    for r in res.itertuples():
        log_run(SCRIPT, {"step": "holdout_trade", "mult": r.mult, "min_frac": r.min_frac,
                         "train": [2021, 2025], "test": 2026, "cost_bp_per_side": 10}, round(r.h, 6),
                {k: round(float(getattr(r, k)), 5) for k in
                 ["ann_mean_gross", "ann_mean_net", "t_nw_gross", "t_nw_net", "avg_turnover",
                  "pocket_lo", "pocket_hi"]} | {"n_days": int(r.n_days)})
    sp = spearman_table(res)
    sp.to_csv(SPEARMAN, index=False)
    log_run(SCRIPT, {"step": "spearman_mult_vs_gross_t"}, "",
            {r.sample: round(float(r.spearman_rho_mult_vs_gross_t), 4) for r in sp.itertuples()})
    print(f"Holdout: panel {len(ho):,} rows, {ho['date'].nunique()} dates "
          f"({pd.Timestamp(ho['date'].min()).date()} to {pd.Timestamp(ho['date'].max()).date()}); "
          f"P&L days {days.size} ({days[0].date()} to {days[-1].date()}); h_cv={h:.6f}; {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
