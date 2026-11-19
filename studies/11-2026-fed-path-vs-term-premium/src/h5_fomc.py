"""H5a: on scheduled FOMC announcement days 1994-2025, does dACMTP10 respond to dDGS2?
H5b (PRIOR ONLY, N = 7 < 8): 2026 days' D1 term-premium share vs the 1994-2025 mean.
Robustness R1: H5a with dTHREEFYTP10.

Each change is taken from that series' own previous published date (bp).

    python -m src.h5_fomc
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
import statsmodels.api as sm

from src import load
from src.common import BP, END_2026, OUT, d1_share, log_run, log_test, own_diff

BASE = (pd.Timestamp("1994-02-04"), pd.Timestamp("2025-12-31"))


def day_table() -> tuple[pd.DataFrame, list[str]]:
    a, f, kw = load.acm(), load.fred(), load.kim_wright()
    series = {"d_acm_tp10": a["ACMTP10"], "d_acm_rny10": a["ACMRNY10"], "d_acm_y10": a["ACMY10"],
              "d_kw_tp10": kw["KWTP10"], "d_dgs2": f["DGS2"], "d_dgs10": f["DGS10"]}
    prev = {}
    diffs = {}
    for k, s in series.items():
        s = s.dropna()
        diffs[k] = s.diff() * BP
        prev[k] = pd.Series(s.index, index=s.index).shift(1)
    days = load.fomc_announcement_days()
    days = days[days <= END_2026]
    rows, issues = [], []
    for d in days:
        r = {"date": d.date()}
        for k in series:
            r[k] = float(diffs[k].get(d, np.nan))
            p = prev[k].get(d, pd.NaT)
            r[f"prev_{k[2:]}"] = None if pd.isna(p) else pd.Timestamp(p).date()
        miss = [k for k in series if np.isnan(r[k])]
        if miss:
            issues.append(f"{d.date()}: missing {', '.join(miss)}")
        r["d1_share_acm"] = d1_share(r["d_acm_tp10"], r["d_acm_rny10"]) if not np.isnan(r["d_acm_tp10"] + r["d_acm_rny10"]) else np.nan
        rows.append(r)
    return pd.DataFrame(rows), issues


def ols_hc1(df: pd.DataFrame, y: str, x: str):
    d = df[[y, x]].dropna()
    return sm.OLS(d[y], sm.add_constant(d[x])).fit(cov_type="HC1"), len(d)


def main() -> pd.DataFrame:
    df, issues = day_table()
    dates = pd.to_datetime(df["date"])
    base = df[(dates >= BASE[0]) & (dates <= BASE[1])]
    y26 = df[dates.dt.year == 2026]
    df["sample"] = np.where(dates.dt.year == 2026, "2026 (H5b)", "1994-2025 (H5a)")

    res = {}
    for tid, fam, ycol, desc in [
        ("H5a", "primary", "d_acm_tp10", "dACMTP10 on dDGS2, scheduled announcement days 1994-02-04 to 2025-12-31, HC1, two-sided"),
        ("R1-H5a", "robustness", "d_kw_tp10", "H5a with dTHREEFYTP10"),
    ]:
        fit, n = ols_hc1(base, ycol, "d_dgs2")
        b, t, p = float(fit.params["d_dgs2"]), float(fit.tvalues["d_dgs2"]), float(fit.pvalues["d_dgs2"])
        sign = "positive" if b > 0 else "negative"
        res[tid] = {"alpha": float(fit.params["const"]), "beta": b, "t": t, "p_two": p, "n": n,
                    "r2": float(fit.rsquared), "sign": sign}
        status = "pending BH" if fam == "primary" else ("p <= 0.10" if p <= 0.10 else "p > 0.10")
        log_test(tid, "H5a", desc, status, p, f"beta {b:.4f} bp TP per bp dDGS2 ({sign}), t {t:.2f}", n,
                 f"HC1; R2 {fit.rsquared:.3f}", fam)

    bench = float(base["d1_share_acm"].mean())
    n_bench = int(base["d1_share_acm"].notna().sum())
    n26 = len(y26)
    above = int((y26["d1_share_acm"] > bench).sum())
    res["H5b"] = {"bench_mean_d1": bench, "n_bench": n_bench, "n_2026": n26,
                  "mean_2026_d1": float(y26["d1_share_acm"].mean()), "n_2026_above_bench": above}
    log_test("H5b", "H5b", "2026 announcement days: D1 TP share vs 1994-2025 mean D1 share (ACM)",
             f"prior only (N = {n26} < 8), not tested", None,
             f"2026 mean D1 {res['H5b']['mean_2026_d1']:.3f} vs 1994-2025 mean {bench:.3f}; {above} of {n26} days above",
             n26, "descriptive; every day printed in out/h5_fomc_days.csv", "prior")

    df.to_csv(OUT / "h5_fomc_days.csv", index=False, float_format="%.6g")
    (OUT / "h5a_fit.json").write_text(json.dumps(res, indent=2, default=str))
    log_run("src/h5_fomc.py", {"base": [str(BASE[0].date()), str(BASE[1].date())], "end": END_2026},
            {**res, "issues": issues})
    print(json.dumps(res, indent=2, default=str))
    print("PRIOR ONLY (N = 7 < 8): 2026 announcement days")
    print(y26[["date", "d_dgs2", "d_dgs10", "d_acm_y10", "d_acm_rny10", "d_acm_tp10", "d1_share_acm"]].to_string())
    print(f"1994-2025 mean D1 share: {bench:.4f} (n = {n_bench})")
    for i in issues:
        print("LOG:", i)
    return df


if __name__ == "__main__":
    main()
