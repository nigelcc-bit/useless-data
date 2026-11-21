"""Training-period evaluation (default) and the single hold-out run (--holdout).

python src/evaluate.py            -> training verdicts, ledger.csv, results/*
python src/evaluate.py --holdout  -> hold-out scorecard (run once; see PREREGISTRATION Part D)
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import fisher_exact

sys.path.insert(0, str(Path(__file__).resolve().parent))
import episodes as epi  # noqa: E402
import features as F  # noqa: E402
import models as M  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results"
ASSETS = ["SPX", "NDX", "SOX"]
TARGETS = ["T1", "T2"]
L0F = ["depth", "dist252", "above200", "duration", "legs"]
NPERM = 999
SEED = 20261121
SPLIT_SPX = pd.Timestamp("1990-01-01")
# layer name -> (feature column, kind, layer number)
LAYERS = {
    "H1": ("fed6m", "col", 1),
    "H2a": ("is_signal", "aug", 2),
    "H2b": ("is_signal", "aug", 2),
    "H2b095": ("is_signal", "aug", 2),
    "H2c": ("vixhi", "col", 2),
    "H3": ("credit_nc", "col", 3),
    "H3daily": ("credit_nc_daily", "col", 3),
    "H4total_yoy": ("kr_yoy", "col", 3),
    "H4total_d3": ("kr_d3", "col", 3),
}
VERDICT_LAYERS = ["H1", "H2a", "H2b", "H2b095", "H2c", "H3", "H4total_yoy", "H4total_d3"]
STAMP = datetime.now(timezone.utc).isoformat(timespec="seconds")


def git_hash():
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT).decode().strip()
    except Exception:
        return "unknown"


# ---------------------------------------------------------------- build
def thresholds(C):
    p = epi.shock_threshold_pct(C["SPX"].dropna())
    out = {"pct": p, "SPX": -0.04}
    for a in ["NDX", "SOX"]:
        out[a] = float(np.quantile(C[a].dropna().pct_change().dropna(), p))
    return out


def build_all():
    C, Mo, B = F.load()
    thr = thresholds(C)
    data = {}
    for a in ASSETS:
        d, E, V = F.daily_frame(a, C, Mo, B, thr)
        rows = F.event_rows(a, d, E, V, thr[a])
        sig = {k: F.signal_dates(d, E, k) for k in ["H2a", "H2b", "H2b095"]}
        data[a] = dict(d=d, E=E, rows=rows, sig=sig)
    return data, thr


def add_credit_flags(rows, train_mask, col, newcol):
    med = rows.loc[train_mask, col].median()
    rows[newcol] = np.where(rows[col].isna(), np.nan, (rows[col] < med).astype(float))
    return med


# ---------------------------------------------------------------- permutation helpers
def block_perm_col(df, col, rng):
    """C7: whole-episode blocks among episodes with identical row-type structure; the rest
    permuted within row type."""
    new = df[col].to_numpy().copy()
    sig = df.groupby("ep")["type"].apply(lambda s: tuple(s))
    pos = {e: np.where(df["ep"].to_numpy() == e)[0] for e in sig.index}
    leftovers = []
    for structure, eps in sig.groupby(sig).groups.items():
        eps = list(eps)
        if len(eps) < 2:
            leftovers += eps
            continue
        donors = rng.permutation(eps)
        vals = {e: df[col].to_numpy()[pos[e]] for e in eps}
        for e, dnr in zip(eps, donors):
            new[pos[e]] = vals[dnr]
    if leftovers:
        li = np.concatenate([pos[e] for e in leftovers])
        types = df["type"].to_numpy()[li]
        for t in np.unique(types):
            ii = li[types == t]
            new[ii] = df[col].to_numpy()[rng.permutation(ii)]
    return new


# ---------------------------------------------------------------- one layer test
def layer_test(job):
    """job: dict with X dataframe etc. Returns result dict. Runs in a worker."""
    df, feat, target, kind, best, best2, extra = (job[k] for k in
                                                  ["df", "feat", "target", "kind", "best", "best2", "extra"])
    rng = np.random.default_rng(job["seed"])
    y = df[target].to_numpy(float)
    g = df["ep"].to_numpy()
    X0 = df[list(best)].to_numpy(float)
    b0 = M.brier(M.loeo(X0, y, g), y)
    cols = list(best2) + [feat]
    Xk = df[cols].to_numpy(float)
    pk = M.loeo(Xk, y, g)
    bk = M.brier(pk, y)
    skill = 1 - bk / b0
    coef = M.coef(Xk, y)[-1]
    # permutation null
    null = np.empty(NPERM)
    if kind == "col":
        for r in range(NPERM):
            Xp = Xk.copy()
            Xp[:, -1] = block_perm_col(df, feat, rng)
            null[r] = 1 - M.brier(M.loeo(Xp, y, g), y) / b0
    else:
        # timing null: each signal row moved to a random in-episode session (same episode)
        dd, windows = extra["d"], extra["windows"]
        sig_idx = np.where(df["is_signal"].to_numpy() == 1)[0]
        base = df.copy()
        for r in range(NPERM):
            dp = base.copy()
            for k in sig_idx:
                lo, hi = windows[int(dp["ep"].iat[k])]
                j = rng.integers(lo, hi)
                for c in list(best) + list(best2) + [target]:
                    dp.iat[k, dp.columns.get_loc(c)] = dd[c].iat[j]
            yp = dp[target].to_numpy(float)
            b0p = M.brier(M.loeo(dp[list(best)].to_numpy(float), yp, g), yp)
            bkp = M.brier(M.loeo(dp[cols].to_numpy(float), yp, g), yp)
            null[r] = 1 - bkp / b0p
    p = (1 + np.sum(null >= skill)) / (NPERM + 1)
    return dict(skill=skill, brier_l0=b0, brier_k=bk, coef=coef, p=p, pred=pk)


def halves_signs(df, cols, target, split):
    out = []
    for part in (df[df["date"] < split], df[df["date"] >= split]):
        y = part[target].to_numpy(float)
        X = part[cols].to_numpy(float)
        if len(part) < 4 or len(np.unique(y)) < 2 or np.nanstd(X[:, -1]) == 0:
            out.append(np.nan)
        else:
            out.append(np.sign(M.coef(X, y)[-1]))
    return out


def episode_windows(E, d, target, last_date):
    w = {}
    for _, e in E.iterrows():
        lo = int(e["b10_i"]) + 1
        hi = int(e["reset_i"]) if e["reset_i"] == e["reset_i"] else len(d)
        ok = np.where(d[target].iloc[lo:hi].notna().to_numpy() & (d.index[lo:hi] <= last_date))[0]
        if len(ok):
            w[int(e["ep"])] = (lo + ok[0], lo + ok[-1] + 1)
        else:
            w[int(e["ep"])] = (lo, lo + 1)
    return w


# ---------------------------------------------------------------- dataset per layer
def layer_frame(a, data, layer, target, sample="train"):
    rows = data[a]["rows"]
    base = rows[(rows["sample"] == sample)].copy()
    base["is_signal"] = 0.0
    feat, kind, _ = LAYERS[layer]
    if kind == "aug":
        s = data[a]["sig"][layer]
        d = data[a]["d"]
        sr = d.iloc[s["i"].to_numpy()].copy() if len(s) else d.iloc[[]].copy()
        sr["type"] = layer
        sr["ep"] = s["ep"].to_numpy()
        sr["is_signal"] = 1.0
        sr["sample"] = np.where(sr.index <= F.TRAIN_END, "train", "holdout")
        sr["asset"] = a
        sr = sr[(sr["sample"] == sample) & (sr.index >= pd.Timestamp(F.EVENT_START[a]))]
        if layer.startswith("H2b"):
            base = base[base.index >= pd.Timestamp("2007-12-04")]
            sr = sr[sr.index >= pd.Timestamp("2007-12-04")]
        base = pd.concat([base, sr])
    need = L0F + [target] + ([] if kind == "aug" else [feat])
    return base.dropna(subset=need).sort_values("date")


def power(df, feat, kind):
    n_ep = df["ep"].nunique()
    vals = df[feat]
    binary = set(np.unique(vals.dropna())) <= {0.0, 1.0}
    if binary:
        n1 = int((vals == 1).sum())
        n0 = int((vals == 0).sum())
        under = n_ep < 8 or min(n0, n1) < 8
    else:
        n1 = n0 = None
        under = n_ep < 8
    return n_ep, n0, n1, under


# ---------------------------------------------------------------- inherited tests
def inherited(a, rows, target="T1"):
    tr = rows[(rows["sample"] == "train")].dropna(subset=[target])
    first = tr.sort_values("date").groupby("ep").head(1)
    A = tr[tr["type"] == "A"]
    out = []

    def fx(mask, df, name, hyp, src):
        k1 = int(df.loc[mask, target].sum()); n1 = int(mask.sum())
        k0 = int(df.loc[~mask, target].sum()); n0 = int((~mask).sum())
        if n1 == 0 or n0 == 0:
            p, orr = np.nan, np.nan
        else:
            orr, p = fisher_exact([[k1, n1 - k1], [k0, n0 - k0]])
        out.append(dict(test_id=f"{name}_{a}_{target}", hypothesis=hyp, asset=a, sample="train",
                        statistic=(k1 / n1 if n1 else np.nan) - (k0 / n0 if n0 else np.nan),
                        p_value=p, n_events=n1 + n0, inherited_from=src, target=target,
                        detail=f"{k1}/{n1} vs {k0}/{n0}"))
    fx((A["dist252"] >= -0.05).to_numpy(), A, "I1",
       "First shock within 5% of 252-session high is contained (T1) more often", "Blue Tsunami Flush (6 Nov 2026)")
    fx((A["dist252"] < -0.10).to_numpy(), A, "I2",
       "First shock >10% below 252-session high is contained less often (fell further 10%+)", "Blue Tsunami Flush (6 Nov 2026)")
    f2 = first.dropna(subset=["vix"])
    fx((f2["vix"] >= 35).to_numpy(), f2, "I3",
       "VIX >= 35 at the first event of an episode changes T1 rate", "JPM VIX 35 level via Blue Tsunami desk color")
    return out


# ---------------------------------------------------------------- main training run
def run_training():
    RES.mkdir(exist_ok=True)
    data, thr = build_all()
    json.dump(thr, open(RES / "thresholds.json", "w"), indent=1)
    meds = {}
    for a in ASSETS:
        r = data[a]["rows"]
        tm = r["sample"] == "train"
        meds[a] = dict(
            credit=add_credit_flags(r, tm, "credit_ratio", "credit_nc"),
            credit_daily=add_credit_flags(r, tm, "credit_ratio_daily", "credit_nc_daily"))
        for k in ["H2a", "H2b", "H2b095"]:
            pass
    json.dump(meds, open(RES / "credit_medians.json", "w"), indent=1)
    save_episode_tables(data)
    jobs, meta = [], []
    l0 = {}
    for a in ASSETS:
        for t in TARGETS:
            base = layer_frame(a, data, "H1", t).dropna(subset=L0F + [t])
            base = data[a]["rows"][data[a]["rows"]["sample"] == "train"].dropna(subset=L0F + [t])
            sel = M.select_subsets(base, L0F, t, base["ep"].to_numpy())
            best = sel[0][1]
            best2 = [s for b, s in sel if len(s) == 2][0]
            best1 = [s for b, s in sel if len(s) == 1][0]
            l0[(a, t)] = dict(best=best, best2=best2, best1=best1, brier=sel[0][0], n=len(base),
                              n_ep=base["ep"].nunique(), base_rate=base[t].mean(),
                              brier_clim=float(np.mean((base[t] - base[t].mean()) ** 2)))
            for layer in LAYERS:
                feat, kind, _ = LAYERS[layer]
                df = layer_frame(a, data, layer, t)
                if len(df) == 0 or df["ep"].nunique() < 3:
                    meta.append(dict(a=a, t=t, layer=layer, skip="no data"))
                    continue
                n_ep, n0, n1, under = power(df, feat, kind)
                if (kind == "col" and df[feat].nunique() < 2) or (kind == "aug" and n1 == 0):
                    meta.append(dict(a=a, t=t, layer=layer, skip="no variation"))
                    continue
                s = M.select_subsets(df, L0F, t, df["ep"].to_numpy()) if len(df) != len(base) else sel
                bst = s[0][1]
                bst2 = [x for b, x in s if len(x) == 2][0]
                extra = {}
                if kind == "aug":
                    extra = dict(d=data[a]["d"], windows=episode_windows(data[a]["E"], data[a]["d"], t, F.TRAIN_END))
                jobs.append(dict(df=df, feat=feat, target=t, kind=kind, best=bst, best2=bst2, extra=extra,
                                 seed=SEED + len(jobs)))
                meta.append(dict(a=a, t=t, layer=layer, n=len(df), n_ep=n_ep, n0=n0, n1=n1,
                                 under=under, best=bst, best2=bst2, job=len(jobs) - 1,
                                 start=df["date"].min()))
    with Pool(4) as pool:
        res = pool.map(layer_test, jobs)
    # H4 incremental value check over ret63
    h4inc = []
    for a in ASSETS:
        for t in TARGETS:
            for feat in ["kr_yoy", "kr_d3"]:
                df = data[a]["rows"][data[a]["rows"]["sample"] == "train"].dropna(subset=L0F + [t, feat, "ret63"])
                if len(df) < 10:
                    continue
                y = df[t].to_numpy(float); g = df["ep"].to_numpy()
                b1 = list(l0[(a, t)]["best1"])
                bb = M.brier(M.loeo(df[b1 + ["ret63"]].to_numpy(float), y, g), y)
                bf = M.brier(M.loeo(df[b1 + ["ret63", feat]].to_numpy(float), y, g), y)
                rx = np.polyfit(df["ret63"], df[feat], 1); ry = np.polyfit(df["ret63"], y, 1)
                ex = df[feat] - np.polyval(rx, df["ret63"]); ey = y - np.polyval(ry, df["ret63"])
                h4inc.append(dict(asset=a, target=t, feature=feat, partial_corr=float(np.corrcoef(ex, ey)[0, 1]),
                                  brier_base=bb, brier_with=bf, brier_gain=1 - bf / bb, n=len(df), n_ep=df["ep"].nunique()))
    pd.DataFrame(h4inc).to_csv(RES / "h4_incremental.csv", index=False)
    # assemble
    out = []
    for m in meta:
        if "skip" in m:
            out.append(dict(asset=m["a"], target=m["t"], layer=m["layer"], skip=m["skip"]))
            continue
        r = res[m["job"]]
        df = jobs[m["job"]]["df"]
        split = SPLIT_SPX if m["a"] == "SPX" else df.groupby("ep")["date"].min().median()
        cols = list(m["best2"]) + [LAYERS[m["layer"]][0]]
        hs = halves_signs(df, cols, m["t"], split)
        out.append(dict(asset=m["a"], target=m["t"], layer=m["layer"], n_rows=m["n"], n_ep=m["n_ep"],
                        n0=m["n0"], n1=m["n1"], underpowered=m["under"], sample_start=str(m["start"].date()),
                        l0_model="+".join(m["best"]), base2="+".join(m["best2"]),
                        brier_l0=r["brier_l0"], brier_k=r["brier_k"], skill=r["skill"], coef=r["coef"],
                        sign_h1=hs[0], sign_h2=hs[1], split=str(pd.Timestamp(split).date()), p_perm=r["p"]))
    L = pd.DataFrame(out)
    # cross-asset sign agreement
    def agree(row):
        if pd.isna(row.get("coef")):
            return np.nan
        others = L[(L["layer"] == row["layer"]) & (L["target"] == row["target"]) & (L["asset"] != row["asset"])]
        return int(1 + (np.sign(others["coef"].dropna()) == np.sign(row["coef"])).sum())
    L["n_assets_same_sign"] = L.apply(agree, axis=1)
    inh = []
    for a in ASSETS:
        for t in ["T1"]:
            inh += inherited(a, data[a]["rows"], t)
    # ledger
    led = []
    for _, r in L.iterrows():
        if pd.isna(r.get("skill")):
            continue
        led.append(dict(test_id=f"{r['layer']}_{r['asset']}_{r['target']}", hypothesis=HYP[r["layer"]], asset=r["asset"],
                        sample=f"train {r['sample_start']}..2017-12-31", statistic=r["skill"],
                        p_value=np.nan if r["underpowered"] else r["p_perm"], n_events=r["n_ep"],
                        inherited_from=INH.get(r["layer"], ""), target=r["target"],
                        detail=f"rows={r['n_rows']} perm_p={r['p_perm']:.3f}" + (" UNDERPOWERED" if r["underpowered"] else "")))
    for x in inh:
        x["sample"] = "train first-event rows"
        led.append(x)
    LED = pd.DataFrame(led)
    LED["run_timestamp"] = STAMP
    LED["p_bh"] = M.bh(LED["p_value"].to_numpy())
    LED = LED[["test_id", "hypothesis", "asset", "sample", "statistic", "p_value", "n_events", "run_timestamp",
               "inherited_from", "target", "p_bh", "detail"]]
    LED.to_csv(ROOT / "ledger.csv", index=False)
    pbh = dict(zip(LED["test_id"], LED["p_bh"]))
    L["p_bh"] = [pbh.get(f"{r.layer}_{r.asset}_{r.target}", np.nan) for r in L.itertuples()]

    def verdict(r):
        if isinstance(r.get("skip"), str):
            return "NOT RUN (" + r["skip"] + ")"
        if r["layer"] == "H3daily":
            return "ROBUSTNESS ONLY"
        if r["underpowered"]:
            return "UNDERPOWERED (prior only)"
        fails = []
        if not r["skill"] >= 0.02: fails.append(f"skill {r['skill']:+.3f}<0.02")
        if not r["n_assets_same_sign"] >= 2: fails.append("sign not shared by 2 of 3 assets")
        if not (r["sign_h1"] == r["sign_h2"] == np.sign(r["coef"])): fails.append("sign flips across halves")
        if not r["p_bh"] <= 0.10: fails.append(f"BH p {r['p_bh']:.2f}>0.10")
        return "SURVIVES" if not fails else "KILLED: " + "; ".join(fails)
    L["verdict"] = L.apply(verdict, axis=1)
    L.to_csv(RES / "layer_tests_train.csv", index=False)
    pd.DataFrame([dict(asset=a, target=t, **{k: ("+".join(v) if isinstance(v, tuple) else v) for k, v in d.items()})
                  for (a, t), d in l0.items()]).to_csv(RES / "layer0_selection.csv", index=False)
    exhibits_train(data, l0)
    log_run("evaluate.py (training)")
    print(L[["asset", "target", "layer", "n_ep", "skill", "p_perm", "p_bh", "verdict"]].to_string())
    print(LED[LED["inherited_from"].str.len() > 0][["test_id", "statistic", "p_value", "p_bh", "detail"]].to_string())


HYP = {
    "H1": "Fed stance (6m FEDFUNDS change, lagged) adds skill over Layer 0",
    "H2a": "Realised-vol roll-over date is a better entry than episode events",
    "H2b": "VIX/VIX3M term-structure exit (1.00) date is a better entry",
    "H2b095": "VIX/VIX3M exit at 0.95 (alternative threshold)",
    "H2c": "VIX >= 90th pct of prior 5y at t adds skill",
    "H3": "Credit not confirming (Baa-GS10 change per unit depth below median) adds skill",
    "H3daily": "H3 with daily BAA10Y (robustness)",
    "H4total_yoy": "Korea total exports YoY (substitute for non-semis) adds skill",
    "H4total_d3": "Korea total exports YoY 3m change adds skill",
}
INH = {"H1": "Midterm Cycle note (Fed rule)", "H3": "v14 credit composite", "H3daily": "v14 credit composite",
       "H2b": "v16 episode-state flag desk color", "H2c": "Fear Cycle / VIX levels"}


def log_run(what):
    p = ROOT / "results" / "runs.csv"
    new = not p.exists()
    with p.open("a") as f:
        if new:
            f.write("timestamp,script,git_hash\n")
        f.write(f"{STAMP},{what},{git_hash()}\n")


# ---------------------------------------------------------------- exhibits
def save_episode_tables(data):
    for a in ASSETS:
        E = data[a]["E"].copy()
        d = data[a]["d"]
        r = data[a]["rows"]
        b10 = r[r["type"] == "B10"].set_index("ep")
        E["T1_at_B10"] = E["ep"].map(b10["T1"])
        E["T2_at_B10"] = E["ep"].map(b10["T2"])
        E["fwd63_at_B10"] = E["ep"].map(b10["fwd63"])
        E["fwd252_at_B10"] = E["ep"].map(b10["fwd252"])
        E["deepest_rung"] = E["max_depth"].apply(lambda x: "B30" if x <= -0.30 else "B20" if x <= -0.20 else "B15" if x <= -0.15 else "B10")
        E["sample"] = np.where(E["b10_date"] <= F.TRAIN_END, "train", "holdout")
        E = E[E["b10_date"] >= pd.Timestamp(F.EVENT_START[a])]
        keep = ["ep", "peak_date", "peak", "b10_date", "trough_date", "trough", "max_depth", "sessions_to_trough",
                "reset_date", "reset_type", "legs_at_start", "deepest_rung", "T1_at_B10", "T2_at_B10",
                "fwd63_at_B10", "fwd252_at_B10", "sample"]
        E[keep].to_csv(RES / f"episodes_{a}.csv", index=False)
        cols = ["date", "type", "ep", "sample", "close", "shock_ret", "depth", "dist252", "above200", "duration", "legs",
                "vix", "fed6m", "credit_ratio", "kr_yoy", "T1", "T2", "fwd21", "fwd63", "fwd252", "maxdd63"]
        r[cols].to_csv(RES / f"events_{a}.csv", index=False)


def bucket(x):
    return pd.cut(x, [-np.inf, -0.30, -0.20, -0.15, -0.10, np.inf],
                  labels=["<=-30%", "-30..-20%", "-20..-15%", "-15..-10%", ">-10%"], right=True)


def fmt_rate(k, n):
    if n == 0:
        return ""
    if n < 8:
        return f"{int(k)}/{int(n)} (n<8)"
    lo, hi = M.wilson(k, n)
    return f"{k / n:.0%} [{lo:.0%},{hi:.0%}] n={int(n)}"


def exhibits_train(data, l0):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    # Layer 0 conditional tables (training, all rows; clustering noted)
    lines = []
    for a in ASSETS:
        r = data[a]["rows"]
        tr = r[r["sample"] == "train"].dropna(subset=["T1"])
        tr = tr.assign(bucket=bucket(tr["depth"]), trend=np.where(tr["above200"] == 1, "above 200d", "below 200d"))
        for t in TARGETS:
            sub = tr.dropna(subset=[t])
            g = sub.groupby(["bucket", "trend"], observed=False)[t].agg(["sum", "count"])
            tab = g.apply(lambda s: fmt_rate(s["sum"], s["count"]), axis=1).unstack()
            lines.append(f"\n### {a} {t} (training rows; depth bucket x trend)\n\n" + tab.to_markdown())
    (RES / "layer0_tables.md").write_text("# Layer 0 conditional frequency tables (training)\n"
                                         "Rates with 90% Wilson intervals; cells with n<8 show counts only. Rows from the same "
                                         "episode are not independent.\n" + "\n".join(lines))
    # escalation ladder
    lad = []
    for a in ASSETS:
        r = data[a]["rows"]
        E = data[a]["E"]
        E = E[E["b10_date"] >= pd.Timestamp(F.EVENT_START[a])]
        for samp in ["train", "holdout", "all"]:
            rr = r if samp == "all" else r[r["sample"] == samp]
            EE = E if samp == "all" else E[np.where(E["b10_date"] <= F.TRAIN_END, "train", "holdout") == samp]
            for rung, nxt, lvl in [("B10", "B15", -0.15), ("B15", "B20", -0.20), ("B20", "B30", -0.30), ("B30", None, None)]:
                x = rr[rr["type"] == rung]
                n_ep_r = int((EE["max_depth"] <= {"B10": -0.10, "B15": -0.15, "B20": -0.20, "B30": -0.30}[rung]).sum())
                n_next = int((EE["max_depth"] <= lvl).sum()) if lvl else np.nan
                x1 = x.dropna(subset=["T1"]); x2 = x.dropna(subset=["T2"])
                lad.append(dict(asset=a, sample=samp, rung=rung, episodes_reaching=n_ep_r,
                                p_reach_next=(n_next / n_ep_r) if lvl and n_ep_r else np.nan,
                                T1=fmt_rate(x1["T1"].sum(), len(x1)), T2=fmt_rate(x2["T2"].sum(), len(x2)),
                                med_fwd63=x["fwd63"].median(), med_fwd252=x["fwd252"].median(),
                                med_maxdd63=x["maxdd63"].median()))
    pd.DataFrame(lad).to_csv(RES / "escalation_ladder.csv", index=False)
    # calibration of Layer 0 (LOEO, training)
    fig, axes = plt.subplots(1, 3, figsize=(12, 4), sharey=True)
    for ax, a in zip(axes, ASSETS):
        for t, mk in zip(TARGETS, ["o", "s"]):
            base = data[a]["rows"][data[a]["rows"]["sample"] == "train"].dropna(subset=L0F + [t])
            y = base[t].to_numpy(float)
            p = M.loeo(base[list(l0[(a, t)]["best"])].to_numpy(float), y, base["ep"].to_numpy())
            q = pd.qcut(p, 4, duplicates="drop")
            cal = pd.DataFrame(dict(p=p, y=y, q=q)).groupby("q", observed=True).mean()
            ax.plot(cal["p"], cal["y"], marker=mk, label=f"{t} ({'+'.join(l0[(a, t)]['best'])})")
        ax.plot([0, 1], [0, 1], color="grey", lw=0.8, ls="--")
        ax.set_title(f"{a} Layer 0, LOEO (training)")
        ax.set_xlabel("predicted"); ax.legend(fontsize=7)
    axes[0].set_ylabel("observed (quartile bins)")
    fig.tight_layout(); fig.savefig(RES / "fig_calibration_layer0.png", dpi=150); plt.close(fig)


# ---------------------------------------------------------------- hold-out
def run_holdout():
    data, thr = build_all()
    meds = json.load(open(RES / "credit_medians.json"))
    L = pd.read_csv(RES / "layer_tests_train.csv")
    sel = pd.read_csv(RES / "layer0_selection.csv")
    out, preds = [], []
    for a in ASSETS:
        r = data[a]["rows"]
        for col, newcol, key in [("credit_ratio", "credit_nc", "credit"), ("credit_ratio_daily", "credit_nc_daily", "credit_daily")]:
            r[newcol] = np.where(r[col].isna(), np.nan, (r[col] < meds[a][key]).astype(float))
        for t in TARGETS:
            for layer in ["L0"] + list(LAYERS):
                if layer == "L0":
                    s = sel[(sel.asset == a) & (sel.target == t)].iloc[0]
                    best = s["best"].split("+")
                    tr = r[r["sample"] == "train"].dropna(subset=L0F + [t])
                    ho = r[r["sample"] == "holdout"].dropna(subset=L0F + [t])
                    p, _ = M.fit_predict(tr[best].to_numpy(float), tr[t].to_numpy(float), ho[best].to_numpy(float))
                    out.append(dict(asset=a, target=t, layer="L0", model="+".join(best), n_rows=len(ho), n_ep=ho["ep"].nunique(),
                                    brier=M.brier(p, ho[t].to_numpy(float)), brier_l0=np.nan, skill=np.nan,
                                    base_rate_train=tr[t].mean(), brier_clim=M.brier(np.full(len(ho), tr[t].mean()), ho[t].to_numpy(float))))
                    preds.append(ho.assign(pred=p, layer="L0", target=t)[["asset", "date", "type", "ep", "layer", "target", t, "pred"]].rename(columns={t: "y"}))
                    continue
                row = L[(L.asset == a) & (L.target == t) & (L.layer == layer)]
                if row.empty or pd.isna(row.iloc[0].get("skill")):
                    continue
                row = row.iloc[0]
                feat = LAYERS[layer][0]
                tr = layer_frame(a, data, layer, t, "train")
                ho = layer_frame(a, data, layer, t, "holdout")
                if len(ho) == 0:
                    continue
                best = row["l0_model"].split("+"); cols = row["base2"].split("+") + [feat]
                y_tr, y_ho = tr[t].to_numpy(float), ho[t].to_numpy(float)
                p0, _ = M.fit_predict(tr[best].to_numpy(float), y_tr, ho[best].to_numpy(float))
                pk, _ = M.fit_predict(tr[cols].to_numpy(float), y_tr, ho[cols].to_numpy(float))
                b0, bk = M.brier(p0, y_ho), M.brier(pk, y_ho)
                out.append(dict(asset=a, target=t, layer=layer, model="+".join(cols), n_rows=len(ho), n_ep=ho["ep"].nunique(),
                                brier=bk, brier_l0=b0, skill=1 - bk / b0 if b0 > 0 else np.nan,
                                train_verdict=row["verdict"]))
                preds.append(ho.assign(pred=pk, layer=layer, target=t)[["asset", "date", "type", "ep", "layer", "target", t, "pred"]].rename(columns={t: "y"}))
    H = pd.DataFrame(out)
    H.to_csv(RES / "holdout_scorecard.csv", index=False)
    pd.concat(preds).to_csv(RES / "holdout_predictions.csv", index=False)
    log_run("evaluate.py --holdout (single run)")
    print(H.to_string())


if __name__ == "__main__":
    if "--holdout" in sys.argv:
        run_holdout()
    else:
        run_training()
