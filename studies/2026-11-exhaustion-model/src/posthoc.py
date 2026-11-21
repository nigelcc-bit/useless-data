"""Post-hoc diagnostics (PREREGISTRATION Part D, D4-D9). Changes no pre-registered result.

Outputs in results/posthoc/:
  power_mde.csv        item 1: effective N and minimum detectable Brier skill per asset x target x layer
  neff_pooled.csv      item 1: pooled cross-asset effective N
  holdout_events.csv   item 2: hold-out events with targets, Layer 0 and constant predictions
  holdout_baseline.csv item 2: Layer 0 vs constant Brier per asset x target, with cluster bootstrap
  h5_prepost.csv       item 3: pre/post-2018 descriptive comparison
  data_checks.csv      item 4
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import evaluate as ev  # noqa: E402
import features as F  # noqa: E402
import models as M  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "results"
OUT = R / "posthoc"
Z = 1.959964 + 0.841621          # two-sided alpha 0.05, power 0.80
WIN = 252
SEED = 20261121


# ------------------------------------------------------------------ effective N
def clusters(i_sessions: np.ndarray, win: int = WIN) -> np.ndarray:
    """Cluster ids: events whose [t, t+win] session windows overlap are chained into one cluster."""
    o = np.argsort(i_sessions)
    lab = np.empty(len(i_sessions), int)
    c, end = -1, -np.inf
    for k in o:
        if i_sessions[k] > end:
            c += 1
            end = i_sessions[k] + win
        else:
            end = max(end, i_sessions[k] + win)
        lab[k] = c
    return lab


def greedy_nonoverlap(i_sessions: np.ndarray, win: int = WIN) -> int:
    """Largest set of events with mutually non-overlapping [t, t+win] windows (greedy from earliest)."""
    n, last = 0, -np.inf
    for x in np.sort(i_sessions):
        if x > last + win:
            n += 1
            last = x
    return n


def window_end_dates(d: pd.DataFrame, i: np.ndarray, win: int = WIN) -> np.ndarray:
    idx = d.index
    j = np.minimum(i + win, len(idx) - 1)
    return idx[j].to_numpy()


def mde_skill(n_eff: float, base_rate: float, brier_l0: float) -> float:
    """Minimum detectable Brier-skill gain vs Layer 0 (80% power, two-sided alpha 0.05).

    A layer that splits events into groups whose hit rates differ by the smallest detectable
    amount (two-proportion z-test) lowers Brier by w1*w0*Delta^2 (the resolution term). With
    Delta = Z*sqrt(p(1-p)/(N w1 w0)) this equals Z^2 p(1-p)/N for any split; the continuous-feature
    analogue (detectable r = Z/sqrt(N)) gives the same. Skill vs Layer 0 divides by Brier(L0).
    It assumes the layer is orthogonal to Layer 0 and ignores the out-of-sample fitting cost,
    so it is a LOWER bound on the true MDE.
    """
    return Z ** 2 * base_rate * (1 - base_rate) / (n_eff * brier_l0)


def power_table(data):
    meds = json.load(open(R / "credit_medians.json"))
    for a in ev.ASSETS:
        r = data[a]["rows"]
        r["credit_nc"] = np.where(r["credit_ratio"].isna(), np.nan, (r["credit_ratio"] < meds[a]["credit"]).astype(float))
        r["credit_nc_daily"] = np.where(r["credit_ratio_daily"].isna(), np.nan,
                                        (r["credit_ratio_daily"] < meds[a]["credit_daily"]).astype(float))
    L = pd.read_csv(R / "layer_tests_train.csv")
    rows, pooled_src = [], []
    for _, t in L.iterrows():
        if isinstance(t.get("skip"), str):
            continue
        a, tgt, layer = t["asset"], t["target"], t["layer"]
        df = ev.layer_frame(a, data, layer, tgt, "train")
        d = data[a]["d"]
        i = d.index.get_indexer(df.index)
        lab = clusters(i)
        lab63 = clusters(i, 63)
        p = float(df[tgt].mean())
        n_eff = int(lab.max() + 1)
        mde = mde_skill(n_eff, p, t["brier_l0"])
        mde_ep = mde_skill(t["n_ep"], p, t["brier_l0"])
        pre = t["verdict"]
        post = pre
        if pre.startswith("KILLED") and mde > 0.05:
            post = "UNDERPOWERED (post-hoc: MDE %.2f > 0.05)" % mde
        rows.append(dict(asset=a, target=tgt, layer=layer, n_rows=len(df), n_episodes=int(t["n_ep"]),
                         n_eff_252=n_eff, n_nonoverlap_252=greedy_nonoverlap(i),
                         mde_skill_nonoverlap=mde_skill(greedy_nonoverlap(i), p, t["brier_l0"]), n_eff_63=int(lab63.max() + 1), base_rate=p, brier_l0=t["brier_l0"],
                         mde_skill_neff252=mde, mde_skill_episodes=mde_ep, observed_skill=t["skill"],
                         preregistered_verdict=pre, posthoc_label=post))
        if layer == "H1":   # every Layer 0 event row (H1 has full coverage): pooled source
            pooled_src.append(pd.DataFrame(dict(asset=a, target=tgt, start=df.index.to_numpy(),
                                                end=window_end_dates(d, i))))
    P = pd.DataFrame(rows)
    P.to_csv(OUT / "power_mde.csv", index=False)
    # pooled: all three assets, overlap on calendar windows; same-date events count once
    pl = []
    for tgt in ev.TARGETS:
        s = pd.concat([x for x in pooled_src if x["target"].iat[0] == tgt]).sort_values("start")
        n_rows = len(s)
        n_dates = s["start"].nunique()
        c, end = 0, pd.Timestamp.min
        for st, en in zip(s["start"], s["end"]):
            if st > end:
                c += 1
                end = en
            else:
                end = max(end, en)
        per = {a: int(P[(P.asset == a) & (P.target == tgt) & (P.layer == "H1")]["n_eff_252"].iat[0]) for a in ev.ASSETS}
        pl.append(dict(target=tgt, rows_all_assets=n_rows, distinct_dates=n_dates, pooled_n_eff_252=c,
                       sum_of_per_asset_n_eff=sum(per.values()), **{f"n_eff_{a}": v for a, v in per.items()}))
    pd.DataFrame(pl).to_csv(OUT / "neff_pooled.csv", index=False)
    return P, pd.DataFrame(pl)


# ------------------------------------------------------------------ hold-out baseline vs constant
def holdout_tables():
    pr = pd.read_csv(R / "holdout_predictions.csv", parse_dates=["date"])
    pr = pr[pr["layer"] == "L0"].copy()
    sel = pd.read_csv(R / "layer0_selection.csv")
    data, _ = ev.build_all()
    rng = np.random.default_rng(SEED)
    pr["const"] = [float(sel[(sel.asset == a) & (sel.target == t)]["base_rate"].iat[0]) for a, t in zip(pr.asset, pr.target)]
    pr["loss_l0"] = (pr["pred"] - pr["y"]) ** 2
    pr["loss_const"] = (pr["const"] - pr["y"]) ** 2
    pr["loss_diff"] = pr["loss_l0"] - pr["loss_const"]      # > 0 means baseline worse
    out = []
    for (a, t), g in pr.groupby(["asset", "target"]):
        d = data[a]["d"]
        i = d.index.get_indexer(g["date"])
        g = g.assign(cluster=clusters(i))
        nrow = len(g)
        diff = g["loss_diff"].mean()

        def boot(col):
            cm = g.groupby(col)["loss_diff"].sum()
            if len(cm) < 5:
                return np.nan, np.nan, np.nan
            b = np.array([cm.sample(len(cm), replace=True, random_state=rng.integers(1 << 31)).sum() / nrow
                          for _ in range(4999)])
            lo, hi = np.quantile(b, [0.05, 0.95])
            return lo, hi, float((b > 0).mean())
        lo_c, hi_c, sh_c = boot("cluster")
        lo_e, hi_e, sh_e = boot("ep")
        n_c = int(g["cluster"].nunique())
        if n_c < 5:
            verdict = f"NOT TESTABLE at N_eff={n_c} (252-session chaining); point estimate {'worse' if diff > 0 else 'not worse'}"
        else:
            verdict = ("worse, 90% CI excludes 0" if lo_c > 0 else
                       "point estimate worse, 90% CI includes 0" if diff > 0 else "not worse")
        verdict += "; episode-cluster CI " + ("excludes 0" if lo_e > 0 else "includes 0" if lo_e == lo_e else "n/a")
        out.append(dict(asset=a, target=t, n_rows=nrow, n_episodes=g["ep"].nunique(), n_eff_252=n_c,
                        n_nonoverlap_252=greedy_nonoverlap(i),
                        brier_l0=g["loss_l0"].mean(), brier_const=g["loss_const"].mean(), diff=diff,
                        ci90_neff_lo=lo_c, ci90_neff_hi=hi_c, ci90_episode_lo=lo_e, ci90_episode_hi=hi_e,
                        share_boot_worse_episode=sh_e, verdict=verdict))
        pr.loc[g.index, "cluster_252"] = g["cluster"]
    pr["ep_label"] = pr["ep"]
    pr[["asset", "target", "date", "type", "ep", "cluster_252", "y", "pred", "const", "loss_l0", "loss_const", "loss_diff"]]\
        .sort_values(["asset", "target", "date"]).to_csv(OUT / "holdout_events.csv", index=False)
    H = pd.DataFrame(out)
    H.to_csv(OUT / "holdout_baseline.csv", index=False)
    return H


# ------------------------------------------------------------------ H5
def h5_table():
    out = []
    for a in ev.ASSETS:
        E = pd.read_csv(R / f"episodes_{a}.csv", parse_dates=["b10_date"])
        E = E[E["reset_type"] != "open"]          # trough not final for open episodes
        for per, g in [("pre-2018", E[E["b10_date"] < "2018-01-01"]), ("2018+", E[E["b10_date"] >= "2018-01-01"])]:
            t1 = g["T1_at_B10"].dropna()
            lo, hi = M.wilson(t1.sum(), len(t1))
            q = g["sessions_to_trough"].quantile([0.25, 0.5, 0.75])
            out.append(dict(asset=a, period=per, n_episodes=len(g),
                            sessions_to_trough_median=q[0.5], sessions_to_trough_iqr=f"{q[0.25]:.0f}-{q[0.75]:.0f}",
                            share_trough_on_b10_day=float((g["sessions_to_trough"] == 0).mean()),
                            median_max_depth=g["max_depth"].median(), n_T1=len(t1), T1_rate=t1.mean(),
                            T1_90ci=f"{lo:.0%}-{hi:.0%}"))
    H = pd.DataFrame(out)
    H.to_csv(OUT / "h5_prepost.csv", index=False)
    return H


# ------------------------------------------------------------------ item 4
def data_checks(data):
    man = pd.read_csv(ROOT / "data" / "raw" / "MANIFEST.csv")
    C = pd.read_parquet(ROOT / "data" / "processed" / "closes.parquet")
    v3raw = man[man.file == "vix3m_daily_2007_2026.csv"].iloc[0]
    vxv = man[man.file == "fred_VXVCLS.csv"].iloc[0]
    sig_min = {a: min([data[a]["d"].index[s["i"]].min() for k, s in data[a]["sig"].items()
                       if k.startswith("H2b") and len(s)]) for a in ev.ASSETS}
    vr_first = {a: data[a]["d"]["vratio"].first_valid_index() for a in ev.ASSETS}
    src = {p.name: p.read_text() for p in (ROOT / "src").glob("*.py") if p.name != "posthoc.py"}
    kr_users = sorted({n for n, s in src.items() if "kr_yoy" in s or "kr_d3" in s})
    L0F_has_kr = any(f.startswith("kr_") for f in ev.L0F)
    live = pd.read_csv(R / "live_frozen.csv")
    rows = [
        ("VIX3M raw file first date (MANIFEST)", str(v3raw["first"]), "Yahoo includes back-calculated 2006-07-17..2007-12-03 rows"),
        ("FRED VXVCLS first date (MANIFEST)", str(vxv["first"]), "official history start"),
        ("VIX3M processed first date (closes.parquet)", str(C["VIX3M"].first_valid_index().date()), "cut in src/ingest.py VIX3M_START; enforced by tests/test_data.py"),
        ("First VIX/VIX3M ratio used, per asset", "; ".join(f"{a} {v.date()}" for a, v in vr_first.items()), ""),
        ("Earliest H2b/H2b095 signal, per asset", "; ".join(f"{a} {v.date()}" for a, v in sig_min.items()), "H2b frames also filtered to >= 2007-12-04 in evaluate.layer_frame"),
        ("Rows of pre-2007-12-04 VIX3M data used anywhere", "0", ""),
        ("Scripts referencing kr_yoy/kr_d3", ", ".join(kr_users), "features.py builds; evaluate.py uses only in H4total_* layers and h4_incremental; live.py only prints the state value"),
        ("Korean exports in Layer 0 features", str(L0F_has_kr), ""),
        ("Korean exports in any live frozen model", str(live["model"].str.contains("kr_").any()), "live layers: L0, H1, H2b, H2c, H3"),
        ("Other monthly series vintage", "latest", "FEDFUNDS, BAA, GS10 are not revised in practice; Korean exports (OECD MEI, SA) are revised and re-seasonally-adjusted"),
    ]
    D = pd.DataFrame(rows, columns=["check", "value", "note"])
    D.to_csv(OUT / "data_checks.csv", index=False)
    return D


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    data, _ = ev.build_all()
    P, PL = power_table(data)
    H = holdout_tables()
    H5 = h5_table()
    D = data_checks(data)
    pd.set_option("display.width", 250)
    print(P.drop(columns=["preregistered_verdict"]).round(3).to_string())
    print(PL.to_string())
    print(H.round(4).to_string())
    print(H5.round(3).to_string())
    print(D.to_string())


if __name__ == "__main__":
    main()
