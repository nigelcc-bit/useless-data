"""Study D: Cross-market panel.

Runs the primary event engine on a panel of broad equity indices to multiply
the number of episodes, then re-asks Study 1's questions with inference that
respects cross-market clustering (crashes are global, so 2008 in ten markets
is closer to one episode than ten). See PREREG/D_panel.md.

    python studies/s04_panel.py                # primary panel
    python studies/s04_panel.py --secondary    # + sectors, DJI, gold, BTC (descriptive)
    python studies/s04_panel.py --refresh      # re-download from Yahoo
"""
from __future__ import annotations

import argparse
import numpy as np
import pandas as pd

from common import out_dir, style, plt, SERIES, INK2, NEUTRAL, md_table
from bear_trap.data import load_panel, PANEL_PRIMARY, PANEL_SECONDARY
from bear_trap.events import detect_events, PRIMARY
from bear_trap.inference import (drawdown_pool, stratified_placebo_p, cluster_bootstrap_ci, wilson)

H = PRIMARY.horizons


def build(series: dict) -> tuple[pd.DataFrame, dict]:
    evs, pools = [], {}
    for name, s in series.items():
        ev = detect_events(s, PRIMARY)
        if ev.empty:
            continue
        pool = drawdown_pool(s, H)
        pools[name] = pool
        for h in H:
            ev[f"x{h}"] = ev[f"r{h}"] - pool[f"r{h}"].mean()          # excess vs own benchmark
            ev[f"pool{h}"] = pool[f"r{h}"].mean()
        ev.insert(0, "market", name)
        evs.append(ev)
    E = pd.concat(evs, ignore_index=True)
    E["month"] = pd.to_datetime(E["break_date"]).dt.to_period("M").astype(str)
    E["quarter"] = pd.to_datetime(E["break_date"]).dt.to_period("Q").astype(str)
    return E, pools


def per_market(E: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for m, g in E.groupby("market", sort=False):
        rec = g[g["reclaimed"] == True]  # noqa: E712
        rt = rec["retest"].dropna().astype(bool)
        rows.append(dict(market=m, start=g.break_date.min().date(), breaks=int(g["reclaimed"].notna().sum()),
                         reclaim_rate=rec.shape[0] / max(1, g["reclaimed"].notna().sum()),
                         retest_rate=rt.mean() if len(rt) else np.nan,
                         x60=rec["x60"].mean(), x120=rec["x120"].mean(), n120=int(rec["x120"].notna().sum())))
    return pd.DataFrame(rows)


def pooled(E: pd.DataFrame, pools: dict, tag: str) -> pd.DataFrame:
    rec = E[E["reclaimed"] == True]  # noqa: E712
    rows = []
    res = E[E["reclaimed"].notna()]
    for name, val, cl in [("reclaim_rate", res["reclaimed"].astype(float), res["month"]),
                          ("retest_rate", rec["retest"].astype(float), rec["month"])]:
        lo, hi, G = cluster_bootstrap_ci(val, cl)
        rows.append(dict(sample=tag, stat=name, n=int(val.notna().sum()), clusters_month=G,
                         estimate=float(val.mean()), ci_lo=lo, ci_hi=hi, p_placebo=np.nan))
    for h in H:
        x = rec[f"x{h}"]
        lo, hi, G = cluster_bootstrap_ci(x, rec["month"])
        loq, hiq, Gq = cluster_bootstrap_ci(x, rec["quarter"])
        by = {m: g[f"r{h}"].to_numpy() for m, g in rec.groupby("market")}
        pb = {m: pools[m][f"r{h}"].to_numpy() for m in by}
        rows.append(dict(sample=tag, stat=f"mean excess r{h}", n=int(x.notna().sum()), clusters_month=G,
                         estimate=float(x.mean()), ci_lo=lo, ci_hi=hi,
                         ci_lo_quarter=loq, ci_hi_quarter=hiq, clusters_quarter=Gq,
                         p_placebo=stratified_placebo_p(by, pb)))
    return pd.DataFrame(rows)


def analog(E: pd.DataFrame, tag: str) -> pd.DataFrame:
    rec = E[(E["reclaimed"] == True) & (E["dd_at_break"] <= -0.10) & (E["dd_at_break"] >= -0.20)]  # noqa: E712
    rows = []
    for col in ["regained_high", "dd20", "retest"]:
        v = rec[col].dropna().astype(float)
        cl = rec.loc[v.index, "month"]
        lo, hi, G = cluster_bootstrap_ci(v, cl)
        wl, wh = wilson(int(v.sum()), len(v))
        rows.append(dict(sample=tag, outcome=col, n=len(v), clusters_month=G, share=v.mean(),
                         wilson_lo=wl, wilson_hi=wh, cluster_ci_lo=lo, cluster_ci_hi=hi))
    return pd.DataFrame(rows)


def chart(pm: pd.DataFrame, pool_row: pd.Series, path):
    style()
    pm = pm.sort_values("x120")
    fig, ax = plt.subplots(figsize=(7.5, 0.32 * len(pm) + 1.6))
    y = np.arange(len(pm))
    ax.barh(y, pm["x120"], color=SERIES[0], height=0.6)
    ax.barh([len(pm) + 0.4], [pool_row["estimate"]], color=SERIES[1], height=0.6)
    ax.errorbar([pool_row["estimate"]], [len(pm) + 0.4],
                xerr=[[pool_row["estimate"] - pool_row["ci_lo"]], [pool_row["ci_hi"] - pool_row["estimate"]]],
                fmt="none", ecolor="#1f1f1e", capsize=3)
    labels = [f"{m} (n={n})" for m, n in zip(pm["market"], pm["n120"])] + [f"Pooled (n={int(pool_row['n'])})"]
    ax.set_yticks(list(y) + [len(pm) + 0.4], labels)
    ax.axvline(0, color=INK2, lw=0.8)
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:+.0%}"))
    ax.set_title("120-day return after a reclaim, minus each market's drawdown-matched mean", fontsize=10)
    ax.grid(axis="y", visible=False)
    fig.text(0.01, -0.02, "Pooled error bar: 95% bootstrap CI resampling calendar months (cross-market clusters).",
             color=INK2, fontsize=8.5)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--secondary", action="store_true")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--min-years", type=int, default=15)
    a = ap.parse_args()
    out = out_dir("D_panel")
    series = load_panel(PANEL_PRIMARY, refresh=a.refresh, min_years=a.min_years)
    E, pools = build(series)
    E.to_csv(out / "events_primary.csv", index=False)
    pm = per_market(E)
    pr = pooled(E, pools, "primary")
    an = analog(E, "primary")
    pm.to_csv(out / "per_market.csv", index=False)
    pr.to_csv(out / "pooled.csv", index=False)
    an.to_csv(out / "analogs.csv", index=False)
    chart(pm, pr[pr.stat == "mean excess r120"].iloc[0], out / "d1_forest.png")
    lines = ["# Study D results", "", f"Markets: {', '.join(series)}", "",
             "## Per market", "", md_table(pm), "",
             "## Pooled (primary tests: mean excess r60 and r120, alpha = 0.025 each)", "", md_table(pr), "",
             "## Analogs: reclaimed while 10-20% below the 120-day high", "", md_table(an), ""]
    if a.secondary:
        sec = load_panel(PANEL_SECONDARY, refresh=a.refresh, min_years=5)
        E2, pools2 = build(sec)
        E2.to_csv(out / "events_secondary.csv", index=False)
        lines += ["## Secondary universe (descriptive only)", "", md_table(per_market(E2)), "",
                  md_table(pooled(E2, pools2, "secondary")), ""]
    (out / "results.md").write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
