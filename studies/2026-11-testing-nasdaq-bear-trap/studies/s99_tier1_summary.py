"""Collect the 20 pre-registered Tier 1 primary p-values and apply
Benjamini-Hochberg (q = 0.05) across the whole tier. Run after s01-s04."""
from __future__ import annotations

import numpy as np
import pandas as pd

from common import ROOT, md_table
from src.inference import bh_fdr

R = ROOT / "results"


def main():
    rows = []
    a = R / "A_null_models" / "summary.csv"
    if a.exists():
        d = pd.read_csv(a)
        d = d[(d.model == "block") & (d.level == "min") & d.metric.isin(["reclaim_rate", "retest_rate"])]
        rows += [dict(study="A", test=f"{r['index']} {r.metric} vs block null", p=r.p, within_alpha=0.05 / 4)
                 for _, r in d.iterrows()]
    b = R / "B_second_sweep" / "results.csv"
    if b.exists():
        d = pd.read_csv(b)
        rows += [dict(study="B", test=f"{r['index']} {r.kind} r{r.h}", p=r.p_placebo, within_alpha=0.05 / 12)
                 for _, r in d.iterrows()]
    c = R / "C_survival" / "km_tables.csv"
    if c.exists():
        d = pd.read_csv(c)
        d = d[(d.event == "retest of sweep low") & (d.days_survived == 0)]
        if "logrank_p_vs_null" in d:
            rows += [dict(study="C", test=f"{r['index']} retest curve vs null (log-rank)",
                          p=r.logrank_p_vs_null, within_alpha=0.05 / 2) for _, r in d.iterrows()]
    dp = R / "D_panel" / "pooled.csv"
    if dp.exists():
        d = pd.read_csv(dp)
        d = d[d.stat.isin(["mean excess r60", "mean excess r120"])]
        rows += [dict(study="D", test=f"pooled {r.stat}", p=r.p_placebo, within_alpha=0.05 / 2)
                 for _, r in d.iterrows()]
    T = pd.DataFrame(rows)
    if T.empty:
        print("no results found; run s01-s04 first")
        return
    T["within_study_sig"] = T.p < T.within_alpha
    T["bh_tier1_q05"] = bh_fdr(T.p.fillna(1).to_numpy(), 0.05)
    n_expected = 20
    note = "" if len(T) == n_expected else f"\n\nWARNING: {len(T)} of {n_expected} pre-registered tests found."
    txt = "# Tier 1 primary tests\n\n" + md_table(T, "{:.4f}") + note + "\n"
    (R / "TIER1_SUMMARY.md").write_text(txt)
    print(txt)


if __name__ == "__main__":
    main()
