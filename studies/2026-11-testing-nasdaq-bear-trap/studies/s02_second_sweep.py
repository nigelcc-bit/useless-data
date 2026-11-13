"""Study B: Is the second sweep the real signal?

Study 1 found the chart's "traps" were second, deeper sweeps. This tests two
pre-registered mechanical definitions (see PREREG/B_second_sweep.md):

  B1 second reclaim : first reclaim -> retest below sweep low S1 (within 60d) ->
                      first close back above support L within 20 days of the retest.
  B2 held retest    : first reclaim -> first close back below L (within 60d) before any
                      close < S1 -> close back above L within 10 days, low stayed above S1.

Entry is the close of the qualifying day. Forward returns at 20/60/120 days are
compared with the drawdown-matched pool (placebo test, Study 1 method) and with
first-reclaim returns. 2 definitions x 2 indices x 3 horizons = 12 tests.

    python studies/s02_second_sweep.py
"""
from __future__ import annotations

import argparse
import numpy as np
import pandas as pd

from common import out_dir, style, plt, SERIES, INK2, NEUTRAL, md_table
from src.data import load_index
from src.events import detect_events, second_sweep_events, PRIMARY
from src.inference import drawdown_pool, placebo_p, cluster_bootstrap_ci, bh_fdr

H = PRIMARY.horizons


def analyse(index: str, cutoff: str | None, b1_window: int):
    s = load_index(index)
    if cutoff:
        s = s[s.index <= cutoff]
    ev = detect_events(s, PRIMARY)
    ss = second_sweep_events(s, ev, PRIMARY, b1_window=b1_window)
    pool = drawdown_pool(s, H)
    first = ev[ev["reclaimed"] == True]  # noqa: E712
    rows = []
    for kind in ["B1", "B2"]:
        g = ss[ss.kind == kind] if len(ss) else ss
        for h in H:
            x = g[f"r{h}"].dropna() if len(g) else pd.Series(dtype=float)
            years = g.loc[x.index, "break_date"].dt.year if len(x) else []
            lo, hi, G = cluster_bootstrap_ci(x, years) if len(x) else (np.nan, np.nan, 0)
            rows.append(dict(index=index, kind=kind, h=h, n=len(x), clusters=G,
                             mean=x.mean() if len(x) else np.nan, ci_lo=lo, ci_hi=hi,
                             hit=(x > 0).mean() if len(x) else np.nan,
                             pool_mean=pool[f"r{h}"].mean(),
                             first_reclaim_mean=first[f"r{h}"].mean(),
                             p_placebo=placebo_p(x, pool[f"r{h}"]) if len(x) else np.nan))
    return s, ev, ss, pd.DataFrame(rows)


def chart(res, path):
    style()
    idxs = list(res["index"].unique())
    fig, axes = plt.subplots(1, len(idxs), figsize=(5.2 * len(idxs), 3.6), squeeze=False)
    for i, ix in enumerate(idxs):
        ax = axes[0, i]
        g = res[res["index"] == ix]
        xs = np.arange(len(H))
        w = 0.2
        series = [("Drawdown-matched days", g[g.kind == "B1"]["pool_mean"].to_numpy(), NEUTRAL),
                  ("First reclaim", g[g.kind == "B1"]["first_reclaim_mean"].to_numpy(), SERIES[0]),
                  ("B1 second reclaim", g[g.kind == "B1"]["mean"].to_numpy(), SERIES[1]),
                  ("B2 held retest", g[g.kind == "B2"]["mean"].to_numpy(), SERIES[2])]
        for k, (lab, vals, col) in enumerate(series):
            ax.bar(xs + (k - 1.5) * w, vals, w * 0.92, color=col, label=lab)
        for k, kind in [(2, "B1"), (3, "B2")]:
            gg = g[g.kind == kind]
            ax.errorbar(xs + (k - 1.5) * w, gg["mean"], yerr=[gg["mean"] - gg["ci_lo"], gg["ci_hi"] - gg["mean"]],
                        fmt="none", ecolor="#1f1f1e", elinewidth=1, capsize=2)
        n1 = int(g[(g.kind == "B1") & (g.h == 120)]["n"].iloc[0])
        n2 = int(g[(g.kind == "B2") & (g.h == 120)]["n"].iloc[0])
        ax.set_xticks(xs, [f"{h}d" for h in H])
        ax.axhline(0, color=INK2, lw=0.8)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:+.0%}"))
        ax.set_title(f"{ix}: mean forward return (n at 120d: B1 {n1}, B2 {n2})", fontsize=10)
        ax.grid(axis="x", visible=False)
        if i == 0:
            ax.legend(fontsize=8, loc="upper left")
    fig.text(0.01, -0.02, "Error bars: 95% bootstrap CI clustered by calendar year of the original break.",
             color=INK2, fontsize=8.5)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--indices", default="NDX,SPX")
    ap.add_argument("--cutoff", default=None, help="optional last date")
    ap.add_argument("--b1-window", type=int, default=20)
    a = ap.parse_args()
    out = out_dir("B_second_sweep")
    allres, allss = [], []
    chart_check = []
    for ix in a.indices.split(","):
        s, ev, ss, res = analyse(ix, a.cutoff, a.b1_window)
        allres.append(res)
        if len(ss):
            ss.insert(0, "index", ix)
            allss.append(ss)
        if ix == "NDX":   # do the definitions capture the original chart's episodes?
            for d in ["2025-03-13", "2026-03-20"]:
                hit = ss[ss.break_date == pd.Timestamp(d)] if len(ss) else ss
                chart_check.append(dict(break_date=d, captured=", ".join(hit.kind) if len(hit) else "none",
                                        entry=", ".join(hit.entry_date.dt.date.astype(str)) if len(hit) else ""))
    res = pd.concat(allres, ignore_index=True)
    res["bh_reject_q05"] = bh_fdr(res["p_placebo"].fillna(1).to_numpy(), 0.05)
    res["bonferroni_sig"] = res["p_placebo"] < 0.05 / len(res)
    res.to_csv(out / "results.csv", index=False)
    if allss:
        pd.concat(allss).to_csv(out / "second_sweep_events.csv", index=False)
    chart(res, out / "b1_returns.png")
    lines = ["# Study B results", "",
             f"B1 window {a.b1_window} days. 12 primary tests; Bonferroni alpha = {0.05/len(res):.4f}.", "",
             md_table(res), "", "## Original chart episodes", "",
             md_table(pd.DataFrame(chart_check)) if chart_check else "_NDX not run_", ""]
    (out / "results.md").write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
