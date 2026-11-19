"""H3: is the 2026 R^2 of daily dDGS10 on dDGS2 in the bottom 10% of 1990-2025 calendar years?
Robustness R2: dDGS30 in place of dDGS10.

p = (number of base years with R^2 <= R^2_2026, plus 1) / (number of base years + 1).
With all 36 base years this is the PREREG's /37.

    python -m src.h3_decoupling
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm

from src import load
from src.common import BP, END_2026, OUT, log_run, log_test, pairwise_diff

MIN_DAYS = 100  # a calendar year needs this many paired days to enter the ranking


def yearly(f: pd.DataFrame, long: str) -> pd.DataFrame:
    d = pairwise_diff(f, [long, "DGS2"]) * BP
    d = d[d.index <= END_2026]
    rows = []
    for y, g in d.groupby(d.index.year):
        if len(g) < MIN_DAYS:
            rows.append({"year": y, "long": long, "n": len(g), "beta": np.nan, "r2": np.nan,
                         "note": f"excluded: n < {MIN_DAYS}"})
            continue
        fit = sm.OLS(g[long], sm.add_constant(g["DGS2"])).fit()
        rows.append({"year": y, "long": long, "n": len(g), "beta": fit.params["DGS2"], "r2": fit.rsquared,
                     "note": "2026-01-01 to 2026-11-13" if y == 2026 else ""})
    return pd.DataFrame(rows)


def rank_test(t: pd.DataFrame) -> dict:
    base = t[(t.year <= 2025) & t.r2.notna()]
    r26 = float(t.loc[t.year == 2026, "r2"].iloc[0])
    k = int((base.r2 <= r26).sum())
    m = len(base)
    p = (k + 1) / (m + 1)
    p10 = float(np.percentile(base.r2, 10))
    return {"r2_2026": r26, "k_le": k, "m": m, "p": p, "pct10": p10, "below_pct10": r26 < p10,
            "beta_2026": float(t.loc[t.year == 2026, "beta"].iloc[0]),
            "n_2026": int(t.loc[t.year == 2026, "n"].iloc[0])}


def main() -> pd.DataFrame:
    f = load.fred()
    t10, t30 = yearly(f, "DGS10"), yearly(f, "DGS30")
    out = pd.concat([t10, t30], ignore_index=True)
    out.to_csv(OUT / "h3_yearly_r2.csv", index=False, float_format="%.6g")
    res = {}
    for tid, t, fam in [("H3", t10, "primary"), ("R2", t30, "robustness")]:
        r = rank_test(t)
        res[tid] = r
        agree = (r["p"] <= 0.10) == r["below_pct10"]
        status = "pending BH" if fam == "primary" else ("p <= 0.10" if r["p"] <= 0.10 else "p > 0.10")
        excluded = t[(t.year <= 2025) & t.r2.isna()].year.tolist()
        notes = (f"k={r['k_le']} of m={r['m']} base years with R2 <= R2_2026; 10th pct of base R2 = {r['pct10']:.4f}; "
                 f"2026 below 10th pct: {r['below_pct10']}; rank rule and percentile rule "
                 f"{'agree' if agree else 'DISAGREE'}" + (f"; base years excluded (n < {MIN_DAYS}): {excluded}" if excluded else ""))
        log_test(tid, "H3", f"Yearly R2 of d{t.long.iloc[0]} on dDGS2: empirical rank of 2026 among 1990-2025",
                 status, r["p"], f"R2_2026 {r['r2_2026']:.4f}, beta_2026 {r['beta_2026']:.3f}", r["n_2026"], notes, fam)
    log_run("src/h3_decoupling.py", {"end_2026": END_2026, "min_days": MIN_DAYS}, res)
    print(out.to_string())
    print(res)
    return out


if __name__ == "__main__":
    main()
