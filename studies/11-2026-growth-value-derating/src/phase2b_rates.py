"""Phase 2B (run only if Phase 1 selects it): C (fundamental de-rating) vs D (discount-rate shock).
Weekly d[ln PE_G - ln PE_V] on d(DFII10), d(T10YIE); Newey-West 4 lags. Rules frozen in PREREG.md."""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
import statsmodels.api as sm

from common import END, OUT, RAW, RECON, bh_adjust, fred_on_grid, weekly_panel


def reg(df):
    X = sm.add_constant(df[["dDFII10", "dT10YIE"]])
    f = sm.OLS(df["dy"], X).fit(cov_type="HAC", cov_kwds={"maxlags": 4})
    return f


def run(ledger, peak: pd.Timestamp) -> dict:
    w = weekly_panel()
    f = fred_on_grid(w.index)
    y = np.log(w.pe_g) - np.log(w.pe_v)
    d = pd.DataFrame({"dy": y.diff(), "dDFII10": f.DFII10.diff(), "dT10YIE": f.T10YIE.diff()}).dropna()
    d = d.loc["2024-01-05":"2026-11-27"]
    in_recon = (d.index >= RECON[0]) & (d.index <= RECON[1])
    specs = {"full 2024-01 to 2026-11 (primary)": d, "2026 only": d.loc["2026-01-01":], "full, excluding recon window": d[~in_recon]}
    out = {"regressions": {}}
    pvals, labels = [], []
    for name, dd in specs.items():
        fit = reg(dd)
        r = {k: dict(coef=float(fit.params[k]), t=float(fit.tvalues[k]), p=float(fit.pvalues[k])) for k in ("dDFII10", "dT10YIE")}
        r["n"], r["r2"] = int(fit.nobs), float(fit.rsquared)
        out["regressions"][name] = r
        for k in ("dDFII10", "dT10YIE"):
            pvals.append(r[k]["p"])
            labels.append((name, k))
            ledger.trial("2B", f"coefficient on {k}", name, "coef / t / p (NW 4 lags)", r["n"], f"{r[k]['coef']:+.4f} / {r[k]['t']:+.2f} / {r[k]['p']:.3f}")
    bh = bh_adjust(np.array(pvals))
    for (name, k), b, p in zip(labels, bh, pvals):
        out["regressions"][name][k]["bh_p"] = float(b)
        ledger.test(f"D-{'real' if k == 'dDFII10' else 'be'}-{name.split()[0]}", "D", f"{k} coefficient, {name}",
                    "tested", raw_p=p, effect=f"{out['regressions'][name][k]['coef']:+.4f}", n=out["regressions"][name]["n"], family="phase2b")
    prim = out["regressions"]["full 2024-01 to 2026-11 (primary)"]["dDFII10"]
    cum_real = float(f.DFII10[END] - f.DFII10[peak])
    cum_rel = float(y[END] - y[peak])
    explained = prim["coef"] * cum_real / cum_rel if cum_rel != 0 else np.nan
    d_ok = prim["coef"] < 0 and abs(prim["t"]) > 2 and prim["bh_p"] < 0.10 and explained >= 0.5
    verdict = "D supported" if d_ok else "C by elimination (WEAK)"
    out.update(cum_real_yield_change_pp=cum_real, cum_rel_log_pe_change=cum_rel, real_yield_explained_share=explained,
               verdict=verdict, peak=str(peak.date()), fred_last_date_used=str(f.index[-1].date()))
    ledger.trial("2B", "D vs C rule", "primary", "coef<0, |t|>2, BH p<0.10, explained share>=0.5", out["regressions"]["full 2024-01 to 2026-11 (primary)"]["n"],
                 f"coef {prim['coef']:+.4f}, t {prim['t']:+.2f}, BH p {prim['bh_p']:.3f}, explained {explained:.0%} -> {verdict}")
    ledger.test("D", "D", "Discount-rate shock explains >= half of the relative P/E move", "CONFIRMED" if d_ok else "KILLED",
                effect=f"explained {explained:.0%}", n=out["regressions"]["full 2024-01 to 2026-11 (primary)"]["n"])
    rows = [dict(spec=s, regressor=k, **v) for s, r in out["regressions"].items() for k, v in r.items() if isinstance(v, dict)]
    pd.DataFrame(rows).to_csv(OUT / "phase2b_rates.csv", index=False, float_format="%.6f")
    (OUT / "phase2b_results.json").write_text(json.dumps(out, indent=1, default=float))
    return out


def credit_sidecheck(ledger, peak: pd.Timestamp) -> dict:
    c = pd.read_csv(RAW / "row10_fallback_fred_IG_spreads_weekly_2025_now.csv", parse_dates=["week_ending"]).set_index("week_ending").sort_index()
    pos = c.index.searchsorted(peak, side="right") - 1
    start = c.index[max(pos, 0)]
    last = c.dropna(subset=["BAMLC0A0CM", "BAA10Y"]).index[-1]
    out = {k: dict(start=float(c.at[start, k]), end=float(c.at[last, k]), change=float(c.at[last, k] - c.at[start, k])) for k in ("BAMLC0A0CM", "BAA10Y")}
    out.update(start_week=str(start.date()), end_week=str(last.date()), note="No tech-specific spread in the data pack.")
    for k in ("BAMLC0A0CM", "BAA10Y"):
        ledger.trial("credit", f"{k} change, peak week to last week (descriptive)", "", "pp", 2, f"{out[k]['start']:.2f} -> {out[k]['end']:.2f} ({out[k]['change']:+.2f})")
    (OUT / "credit_sidecheck.json").write_text(json.dumps(out, indent=1))
    return out
