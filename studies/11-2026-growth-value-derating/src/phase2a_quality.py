"""Phase 2A (run only if Phase 1 selects it): A (earnings catch-up) vs B (inflated estimates), top-15 Growth names.
Rules frozen in PREREG.md."""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from common import OUT, RAW

MIN_NAMES = 8  # protocol rule 6


def top15_weights() -> pd.Series:
    t = pd.read_csv(RAW / "row5_IVW_top15_weights_end2025_vs_now.csv")
    t = t[t["in_top15_now"].astype(str) == "True"].copy()
    t["key"] = t.ticker.replace({"GOOG": "GOOGL"})  # Alphabet: both share classes, one set of cash flows
    return t.groupby("key")["weight_pct_2026-11-25"].sum()


def ttm_metrics(cf: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for tk, g in cf.groupby("ticker"):
        g = g.sort_values("fiscal_quarter_end").reset_index(drop=True)
        if len(g) < 8:
            continue
        for label, sl in (("latest", g.iloc[-4:]), ("year_earlier", g.iloc[-8:-4])):
            def s(c):
                v = sl[c]
                return np.nan if v.isna().any() else float(v.sum())
            ocf, capex, dep, ni, sbc = s("ocf"), s("capex"), s("dep_amort"), s("net_income"), s("sbc")
            rows.append(dict(ticker=tk, period=label, quarter_end=str(sl.fiscal_quarter_end.iloc[-1]), ocf=ocf, capex=capex, dep=dep, ni=ni, sbc=sbc,
                             capex_to_ocf=capex / ocf if ocf else np.nan,
                             fcf_sbc_to_ni=(ocf - capex - sbc) / ni if ni else np.nan,
                             capex_to_dep=capex / dep if dep else np.nan,
                             ocf_to_ni=ocf / ni if ni else np.nan))
    return pd.DataFrame(rows)


def wmean(df: pd.DataFrame, col: str, w: pd.Series):
    d = df.set_index("ticker")[col].dropna()
    ww = w.reindex(d.index).dropna()
    d = d.reindex(ww.index)
    return (float((d * ww).sum() / ww.sum()) if len(d) else np.nan), list(d.index)


def wratio(df: pd.DataFrame, num, den, w: pd.Series):
    d = df.set_index("ticker")
    x = pd.DataFrame({"n": num(d), "d": den(d)}).dropna()
    ww = w.reindex(x.index).dropna()
    x = x.reindex(ww.index)
    return (float((x.n * ww).sum() / (x.d * ww).sum()) if len(x) else np.nan), list(x.index)


def holdings_weights(path, kind):
    h = pd.read_csv(path)
    h = h[h.assetClass == "Equity"]
    return h.groupby("ticker")["marketWeight"].sum()


def run(ledger) -> dict:
    w = top15_weights()
    cf = pd.read_csv(RAW / "row6_top15_quarterly_cashflows_SEC_XBRL_USDm.csv")
    cf = cf[cf.ticker.isin(w.index)]
    M = ttm_metrics(cf)
    M.to_csv(OUT / "phase2a_ttm_by_company.csv", index=False, float_format="%.4f")
    lat, prev = M[M.period == "latest"], M[M.period == "year_earlier"]
    out = {"weights_pct": w.to_dict(), "metrics": {}}
    for col in ("capex_to_ocf", "fcf_sbc_to_ni", "capex_to_dep", "ocf_to_ni"):
        # same companies in both periods
        both = sorted(set(lat.dropna(subset=[col]).ticker) & set(prev.dropna(subset=[col]).ticker))
        a, na = wmean(lat[lat.ticker.isin(both)], col, w)
        b, _ = wmean(prev[prev.ticker.isin(both)], col, w)
        out["metrics"][col] = dict(latest=a, year_earlier=b, change=a - b, n=len(both), names=both, prior_only=len(both) < MIN_NAMES)
        ledger.trial("2A", f"{col} (weighted mean of company ratios)", "primary", "latest / year earlier / change", len(both), f"{a:.3f} / {b:.3f} / {a - b:+.3f}")
    # robustness: ratio of weighted sums
    rs = {
        "fcf_sbc_to_ni": (lambda d: d.ocf - d.capex - d.sbc, lambda d: d.ni),
        "capex_to_dep": (lambda d: d.capex, lambda d: d.dep),
        "capex_to_ocf": (lambda d: d.capex, lambda d: d.ocf),
        "ocf_to_ni": (lambda d: d.ocf, lambda d: d.ni),
    }
    out["robust_ratio_of_sums"] = {}
    for col, (num, den) in rs.items():
        both = out["metrics"][col]["names"]
        a, _ = wratio(lat[lat.ticker.isin(both)], num, den, w)
        b, _ = wratio(prev[prev.ticker.isin(both)], num, den, w)
        out["robust_ratio_of_sums"][col] = dict(latest=a, year_earlier=b, change=a - b)
        ledger.trial("2A", f"{col} (ratio of weighted sums)", "robustness", "latest / year earlier / change", len(both), f"{a:.3f} / {b:.3f} / {a - b:+.3f}")

    # revisions: breadth snapshot (row8) and FY1 90-day change (row9), Growth vs Value
    br = pd.read_csv(RAW / "row8_revision_breadth_growth_vs_value_snapshot_20261128.csv").set_index("metric")
    out["breadth_snapshot"] = br.to_dict()
    up, dn = float(br.loc["up30_count", "growth"]), float(br.loc["down30_count", "growth"])
    out["growth_breadth_net_positive"] = up > dn
    ledger.trial("2A", "revision breadth snapshot (row8)", "Growth up30 vs down30", "count", int(br.loc["n_names", "growth"]), f"up {up:.0f}, down {dn:.0f}")
    c = pd.read_csv(RAW / "row9_constituent_consensus_eps_yahoo_snapshot_20261128.csv").set_index("ticker")
    chg = (c.fy1_cur / c.fy1_d90 - 1).replace([np.inf, -np.inf], np.nan)
    fy1 = {}
    for side, path in (("growth", RAW / "row5_IVW_holdings_20261125.csv"), ("value", RAW / "row5_IVE_holdings_20261125.csv")):
        hw = holdings_weights(path, side)
        x = pd.DataFrame({"chg": chg.reindex(hw.index), "w": hw}).dropna()
        fy1[side] = dict(chg=float((x.chg * x.w).sum() / x.w.sum()), n=len(x), weight_covered=float(x.w.sum()))
        ledger.trial("2A", "FY1 consensus change over 90 days (row9)", side, "weight-weighted mean", len(x), f"{fy1[side]['chg']:+.2%}")
    out["fy1_90d"] = fy1

    m = out["metrics"]
    fs, cd = m["fcf_sbc_to_ni"], m["capex_to_dep"]
    chg_pp = fs["change"] * 100
    if fs["prior_only"] or cd["prior_only"]:
        verdict = "INCONCLUSIVE (prior only: fewer than 8 names)"
    elif chg_pp < -15 and cd["latest"] > 2.0:
        verdict = "B supported"
    elif chg_pp >= -10 and out["growth_breadth_net_positive"]:
        verdict = "A supported"
    else:
        verdict = "INCONCLUSIVE"
    out["verdict"] = verdict
    out["rule_inputs"] = dict(fcf_sbc_to_ni_change_pp=chg_pp, capex_to_dep_latest=cd["latest"], breadth_net_positive=out["growth_breadth_net_positive"])
    ledger.trial("2A", "A vs B verdict rule", "primary", "FCF-SBC/NI change pp; capex/dep latest; breadth", fs["n"],
                 f"{chg_pp:+.1f}pp; {cd['latest']:.2f}; net positive={out['growth_breadth_net_positive']} -> {verdict}")
    ledger.test("A", "A", "Earnings catch-up: FCF-minus-SBC/NI change >= -10pp and breadth net positive",
                "CONFIRMED" if verdict == "A supported" else ("KILLED" if verdict == "B supported" else "INCONCLUSIVE"),
                effect=f"{chg_pp:+.1f}pp", n=fs["n"])
    ledger.test("B", "B", "Inflated estimates: FCF-minus-SBC/NI down > 15pp and capex/dep > 2.0",
                "CONFIRMED" if verdict == "B supported" else ("KILLED" if verdict == "A supported" else "INCONCLUSIVE"),
                effect=f"{chg_pp:+.1f}pp, capex/dep {cd['latest']:.2f}", n=fs["n"])
    pd.DataFrame([dict(metric=k, **{kk: vv for kk, vv in v.items() if kk != "names"}, names=";".join(v["names"])) for k, v in m.items()]).to_csv(
        OUT / "phase2a_quality.csv", index=False, float_format="%.4f")
    (OUT / "phase2a_results.json").write_text(json.dumps(out, indent=1, default=float))
    return out
