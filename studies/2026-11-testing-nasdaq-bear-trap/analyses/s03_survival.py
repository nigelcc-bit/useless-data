"""Study C: Survival analysis of retests and recoveries.

Turns the static "72% retest within 60 days" into a hazard curve that updates
each day a reclaim survives, compares it with the block-bootstrap null, fits a
Cox model with break-time covariates, and applies both to the live Nov 2026
Nasdaq event. See PREREG/C_survival.md.

    python studies/s03_survival.py
    python studies/s03_survival.py --null-paths 0     # skip the null overlay
"""
from __future__ import annotations

import argparse
import warnings
import numpy as np
import pandas as pd
from lifelines import KaplanMeierFitter, CoxPHFitter
from lifelines.statistics import logrank_test, proportional_hazard_test

from common import out_dir, style, plt, SERIES, INK2, NEUTRAL, md_table, write_json
from bear_trap.data import load_index
from bear_trap.events import detect_events, PRIMARY
from bear_trap.nulls import make_block

CAP = 120                       # analysis horizon (trading days)
CHECKPOINTS = [0, 5, 10, 20, 30, 40]
STUDY1_END = "2026-11-09"


def spells(ev: pd.DataFrame, kind: str) -> pd.DataFrame:
    """Durations from the entry close, censored at CAP or data end."""
    d = ev[ev["reclaimed"] == True].copy()  # noqa: E712
    T, E = (d["t_retest"], d["e_retest"]) if kind == "retest" else (d["t_high"], d["e_high"])
    d["T"] = np.minimum(T.astype(float), CAP)
    d["E"] = ((E == 1) & (T <= CAP)).astype(int)
    d = d[d["T"] > 0]
    return d


def km_table(kmf: KaplanMeierFitter, horizon=60) -> pd.DataFrame:
    S = lambda t: float(kmf.survival_function_at_times(t).iloc[0])  # noqa: E731
    rows = []
    for d in CHECKPOINTS:
        sd, sh = S(d), S(horizon)
        rows.append(dict(days_survived=d, S=sd, p_event_by_h_given_none_yet=1 - sh / sd if sd > 0 else np.nan))
    return pd.DataFrame(rows)


def null_spells(s: pd.Series, n_paths: int, seed: int) -> pd.DataFrame:
    lr = np.diff(np.log(s.to_numpy(float)))
    sim = make_block(lr)
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(n_paths):
        P = pd.Series(sim(len(s), rng))
        ev = detect_events(P, PRIMARY)
        if len(ev):
            out.append(ev)
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--indices", default="NDX,SPX")
    ap.add_argument("--null-paths", type=int, default=200)
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()
    out = out_dir("C_survival")
    style()
    idxs = a.indices.split(",")
    fig, axes = plt.subplots(len(idxs), 2, figsize=(10, 3.4 * len(idxs)), squeeze=False)
    tables, pooled, live = [], [], {}
    for i, ix in enumerate(idxs):
        full = load_index(ix)
        hist = full[full.index <= STUDY1_END]
        ev_full = detect_events(full, PRIMARY)
        ev = ev_full[ev_full["break_date"] < "2026-11-01"]      # fit sample excludes the live event
        nul = null_spells(hist, a.null_paths, a.seed) if a.null_paths else pd.DataFrame()
        for j, kind in enumerate(["retest", "high"]):
            d = spells(ev, kind)
            kmf = KaplanMeierFitter().fit(d["T"], d["E"], label=f"{ix} observed (n={len(d)})")
            tab = km_table(kmf)
            tab.insert(0, "event", "retest of sweep low" if kind == "retest" else "regain 120d high")
            tab.insert(0, "index", ix)
            ax = axes[i, j]
            kmf.plot_survival_function(ax=ax, color=SERIES[0], ci_show=True, ci_alpha=0.15)
            if len(nul):
                dn = spells(nul, kind)
                kmn = KaplanMeierFitter().fit(dn["T"], dn["E"], label=f"block-bootstrap null (n={len(dn)})")
                kmn.plot_survival_function(ax=ax, color=NEUTRAL, ci_show=False, linestyle="--")
                lr = logrank_test(d["T"], dn["T"], d["E"], dn["E"])
                tab["logrank_p_vs_null"] = lr.p_value
                nt = km_table(kmn)
                tab["null_p_event_by_60_given_none_yet"] = nt["p_event_by_h_given_none_yet"].to_numpy()
            tables.append(tab)
            ax.set_xlim(0, CAP)
            ax.set_ylim(0, 1.02)
            ax.set_xlabel("trading days after reclaim")
            ax.set_ylabel("share with no event yet")
            ax.set_title(f"{ix}: time to {'retest of sweep low' if kind == 'retest' else 'regaining 120d high'}",
                         fontsize=10)
            ax.legend(fontsize=8)
            d = d.assign(index=ix, kind=kind)
            pooled.append(d)
        # ---- live event
        cur = ev_full[ev_full["break_date"] >= "2026-11-01"]
        if len(cur) and bool(cur.iloc[0]["reclaimed"]):
            c = cur.iloc[0]
            live[ix] = dict(break_date=c.break_date, reclaim_date=c.entry_date, sweep_low=c.sweep_low,
                            level=c.level, high_120=c.high_120, last_date=full.index[-1],
                            days_since_reclaim=int(c.follow_days),
                            retested=bool(c.e_retest == 1), regained_high=bool(c.e_high == 1),
                            sweep_depth=-c.sweep_vs_level, dd_abs=-c.dd_at_break, rv20=c.rv20_at_break)
    fig.text(0.01, -0.01, f"Shaded: 95% CI. Dashed: same rule on {a.null_paths} block-bootstrap paths (primary null).",
             color=INK2, fontsize=8.5)
    fig.tight_layout()
    fig.savefig(out / "c1_km_curves.png")
    plt.close(fig)

    tab = pd.concat(tables, ignore_index=True)
    tab.to_csv(out / "km_tables.csv", index=False)

    # ---- Cox model, pooled across indices, stratified by index, clustered by year
    P = pd.concat(pooled, ignore_index=True)
    cox_out = {}
    for kind in ["retest", "high"]:
        d = P[P.kind == kind].copy()
        d["sweep_depth"] = -d["sweep_vs_level"]
        d["dd_abs"] = -d["dd_at_break"]
        d["rv20"] = d["rv20_at_break"]
        d["year"] = pd.to_datetime(d["break_date"]).dt.year
        X = d[["T", "E", "sweep_depth", "dd_abs", "rv20", "index", "year"]].dropna()
        mu, sd = X[["sweep_depth", "dd_abs", "rv20"]].mean(), X[["sweep_depth", "dd_abs", "rv20"]].std()
        Z = X.copy()
        Z[["sweep_depth", "dd_abs", "rv20"]] = (X[["sweep_depth", "dd_abs", "rv20"]] - mu) / sd
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            cph = CoxPHFitter(penalizer=0.05).fit(Z, "T", "E", strata=["index"], cluster_col="year")
        try:   # proportional-hazards diagnostics (PREREG kill criterion)
            pht = proportional_hazard_test(cph, Z, time_transform="rank")
            ph_ok = bool((pht.summary["p"] >= 0.05).all())
        except Exception as e:  # noqa: BLE001
            print(f"[cox] PH check failed to run: {e}")
            ph_ok = None
        summ = cph.summary[["exp(coef)", "exp(coef) lower 95%", "exp(coef) upper 95%", "p"]].reset_index()
        summ.columns = ["covariate (per 1 sd)", "hazard_ratio", "hr_lo", "hr_hi", "p"]
        summ.insert(0, "event", kind)
        cox_out[kind] = dict(model=cph, mu=mu, sd=sd, summary=summ, n=len(Z),
                             concordance=cph.concordance_index_, ph_ok=ph_ok)
        summ.to_csv(out / f"cox_{kind}.csv", index=False)

    # ---- apply to the live event
    live_rows = []
    for ix, L in live.items():
        dnow = min(L["days_since_reclaim"], CAP)
        km = tab[(tab["index"] == ix)]
        for kind, label in [("retest", "retest of sweep low by day 60"), ("high", "regain 120d high by day 60")]:
            if (kind == "retest" and L["retested"]) or (kind == "high" and L["regained_high"]):
                live_rows.append(dict(index=ix, outcome=label, status="already happened"))
                continue
            d = P[(P["index"] == ix) & (P.kind == kind)]
            kmf = KaplanMeierFitter().fit(d["T"], d["E"])
            s0, s60 = (float(kmf.survival_function_at_times(t).iloc[0]) for t in (dnow, 60))
            co = cox_out[kind]
            x = pd.DataFrame([{"sweep_depth": L["sweep_depth"], "dd_abs": L["dd_abs"], "rv20": L["rv20"],
                               "index": ix}])
            x[["sweep_depth", "dd_abs", "rv20"]] = (x[["sweep_depth", "dd_abs", "rv20"]] - co["mu"]) / co["sd"]
            sf = co["model"].predict_survival_function(x, times=[dnow, 60]).iloc[:, 0]
            live_rows.append(dict(index=ix, outcome=label, status=f"not yet, {dnow} trading days after reclaim",
                                  km_conditional=1 - s60 / s0 if s0 > 0 else np.nan,
                                  cox_conditional=1 - sf.loc[60] / sf.loc[dnow] if sf.loc[dnow] > 0 else np.nan))
    live_df = pd.DataFrame(live_rows)
    live_df.to_csv(out / "live_event.csv", index=False)
    write_json(live, out / "live_event_state.json")

    lines = ["# Study C results", "",
             "## Kaplan-Meier: P(event by day 60 | none by day d)", "", md_table(tab), "",
             "## Cox proportional hazards (pooled, stratified by index, SEs clustered by year)", ""]
    for kind, co in cox_out.items():
        ph_lab = {True: "not rejected", False: "REJECTED: report KM only", None: "untested"}[co["ph_ok"]]
        lines += [f"**{kind}** (n = {co['n']}, concordance {co['concordance']:.3f}, PH assumption {ph_lab})", "",
                  md_table(co["summary"]), ""]
    state = pd.DataFrame(live).T.reset_index().rename(columns={"index": "idx"}) if live else pd.DataFrame()
    lines += ["## Live event", "", md_table(state) if len(state) else "_none_", "",
              md_table(live_df) if len(live_df) else "_no live reclaimed event detected_", ""]
    (out / "results.md").write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
