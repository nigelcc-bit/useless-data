"""Study A: Does support exist?

Runs the Study 1 event engine on simulated price paths from five null models
and on trailing-quantile pseudo-levels, then asks whether the observed reclaim
and retest rates at 6-month lows differ from what the return process alone
produces. See PREREG/A_null_models.md.

    python studies/s01_null_models.py                 # 500 paths per model
    python studies/s01_null_models.py --paths 100     # quick run
"""
from __future__ import annotations

import argparse
import time
import numpy as np
import pandas as pd

from common import out_dir, style, plt, SERIES, INK2, md_table, write_json
from bear_trap.data import load_index
from bear_trap.events import path_stats, PRIMARY
from bear_trap.inference import two_sided_percentile_p
from bear_trap.nulls import MODELS

METRICS = ["reclaim_rate", "retest_rate", "breaks_per_year", "deep_share"]
QUANTS = ["q05", "q10", "q20"]


def run(index: str, models: list[str], n_paths: int, seed: int, cutoff: str):
    s = load_index(index)
    s = s[s.index <= cutoff]
    C = s.to_numpy(float)
    lr = np.diff(np.log(C))
    obs = {"min": path_stats(C, PRIMARY)}
    for q in QUANTS:
        obs[q] = path_stats(C, PRIMARY.with_(level=q))

    rows, diffs = [], []
    for m in models:
        t0 = time.time()
        sim = MODELS[m](lr)
        rng = np.random.default_rng(seed)
        for i in range(n_paths):
            P = sim(len(C), rng)
            rec = {"index": index, "model": m, "path": i, "level": "min", **path_stats(P, PRIMARY)}
            rows.append(rec)
            if m == "block":                     # pseudo-level DiD on the primary null only
                for q in QUANTS:
                    rq = path_stats(P, PRIMARY.with_(level=q))
                    rows.append({"index": index, "model": m, "path": i, "level": q, **rq})
        print(f"  {index} {m:6s} {n_paths} paths in {time.time() - t0:5.1f}s")
    sims = pd.DataFrame(rows)
    return s, obs, sims


def summarise(index, obs, sims):
    out = []
    for (m, lvl), g in sims.groupby(["model", "level"]):
        o = obs[lvl]
        for met in METRICS:
            d = g[met].to_numpy(float)
            out.append(dict(index=index, model=m, level=lvl, metric=met, observed=o[met],
                            null_mean=np.nanmean(d), null_lo=np.nanquantile(d, 0.025),
                            null_hi=np.nanquantile(d, 0.975), excess=o[met] - np.nanmean(d),
                            p=two_sided_percentile_p(o[met], d)))
    return pd.DataFrame(out)


def did(index, obs, sims):
    """Is the excess (real - null) larger at minima than at quantile pseudo-levels?
    Paired per path: d = rate_min - rate_q, observed vs block-null distribution."""
    b = sims[sims.model == "block"].pivot(index="path", columns="level")
    out = []
    for q in QUANTS:
        for met in ["reclaim_rate", "retest_rate"]:
            dn = (b[(met, "min")] - b[(met, q)]).to_numpy(float)
            do = obs["min"][met] - obs[q][met]
            out.append(dict(index=index, pseudo_level=q, metric=met, observed_diff=do,
                            null_diff_mean=np.nanmean(dn), p=two_sided_percentile_p(do, dn)))
    return pd.DataFrame(out)


def chart(summ_all, sims_all, path):
    style()
    idxs = list(summ_all["index"].unique())
    fig, axes = plt.subplots(len(idxs), 2, figsize=(10, 3.2 * len(idxs)), squeeze=False)
    models = list(dict.fromkeys(sims_all["model"]))
    for i, ix in enumerate(idxs):
        for j, met in enumerate(["reclaim_rate", "retest_rate"]):
            ax = axes[i, j]
            g = sims_all[(sims_all["index"] == ix) & (sims_all.level == "min")]
            data = [g[g.model == m][met].dropna().to_numpy() for m in models]
            bp = ax.boxplot(data, vert=False, widths=0.55, patch_artist=True, showfliers=False, whis=(2.5, 97.5),
                            medianprops=dict(color="white", linewidth=1.5))
            for k, b in enumerate(bp["boxes"]):
                b.set_facecolor(SERIES[k % len(SERIES)]); b.set_edgecolor("white")
            obs = summ_all[(summ_all["index"] == ix) & (summ_all.level == "min") &
                           (summ_all.metric == met)]["observed"].iloc[0]
            ax.axvline(obs, color="#1f1f1e", lw=2)
            ax.set_yticks(range(1, len(models) + 1), models)
            ax.set_xlim(0, 1)
            ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
            ax.set_title(f"{ix}: {met.replace('_', ' ')}, observed {obs:.0%} (black line)", fontsize=10)
            ax.grid(axis="y", visible=False)
    fig.suptitle("Study A: observed rates against simulated price paths", x=0.01, ha="left",
                 fontweight="bold")
    fig.text(0.01, -0.01, "Box = middle 50% of simulated paths, whiskers = middle 95%. Primary null: block (stationary bootstrap, mean block 20d).",
             color=INK2, fontsize=8.5)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--paths", type=int, default=500)
    ap.add_argument("--models", default="block,gbm,iid,garch,msvol")
    ap.add_argument("--indices", default="NDX,SPX")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--cutoff", default="2026-11-09", help="last date used (Study 1 sample end)")
    a = ap.parse_args()
    out = out_dir("A_null_models")
    models = a.models.split(",")
    summs, sims_all, dids, obs_all = [], [], [], {}
    for ix in a.indices.split(","):
        s, obs, sims = run(ix, models, a.paths, a.seed, a.cutoff)
        obs_all[ix] = {k: v for k, v in obs.items()} | {"source": s.attrs.get("source")}
        summs.append(summarise(ix, obs, sims))
        dids.append(did(ix, obs, sims) if "block" in models else pd.DataFrame())
        sims_all.append(sims)
    summ = pd.concat(summs)
    sims_all = pd.concat(sims_all)
    dd = pd.concat(dids)
    summ.to_csv(out / "summary.csv", index=False)
    sims_all.to_csv(out / "sim_paths.csv", index=False)
    dd.to_csv(out / "did_pseudo_levels.csv", index=False)
    write_json(obs_all, out / "observed.json")
    chart(summ, sims_all, out / "a1_null_rates.png")

    prim = summ[(summ.model == "block") & (summ.level == "min") &
                summ.metric.isin(["reclaim_rate", "retest_rate"])].copy()
    prim["bonferroni_sig"] = prim["p"] < 0.05 / 4
    lines = ["# Study A results", "",
             f"Paths per model: {a.paths}. Seed {a.seed}. Sample end {a.cutoff}.", "",
             "## Primary tests (block null, 4 tests, Bonferroni alpha = 0.0125)", "",
             md_table(prim[["index", "metric", "observed", "null_mean", "null_lo", "null_hi", "p",
                            "bonferroni_sig"]]),
             "", "## All models, swing-low level", "",
             md_table(summ[summ.level == "min"].drop(columns="level")),
             "", "## Pseudo-level difference-in-differences (secondary)", "",
             md_table(dd) if len(dd) else "_block model not run_", ""]
    (out / "results.md").write_text("\n".join(lines))
    print("\n".join(lines[:12]))
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
