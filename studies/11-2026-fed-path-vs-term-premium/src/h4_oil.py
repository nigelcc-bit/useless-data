"""H4a / H4b: oil sensitivity of the 10y term premium (weekly).
Robustness R1 (THREEFYTP10 in place of ACMTP10) and R3 (exclude 2020-03-01 to 2020-04-30).
Also writes a rolling 52-week beta (descriptive only, not a test).

    python -m src.h4_oil
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm

from src import load
from src.common import BP, END_2026, OUT, log_run, log_test, one_sided_p, weekly_last

NW_LAGS = 4
START_2026 = pd.Timestamp("2026-01-02")  # first week ending in 2026
COVID = (pd.Timestamp("2020-03-01"), pd.Timestamp("2020-04-30"))


def weekly_panel(tp: pd.Series) -> tuple[pd.DataFrame, list[str]]:
    """Weekly dTP (bp) and dln WTI. Changes using a weekly WTI <= 0 are dropped and logged."""
    wti = weekly_last(load.fred()["DCOILWTICO"])
    tpw = weekly_last(tp)
    bad = wti[wti <= 0]
    dropped = []
    for d in bad.index:
        dropped.append(f"WTI weekly value {wti.loc[d]} on week ending {d.date()}: dropped changes "
                       f"into and out of that week")
    wti_pos = wti.where(wti > 0)
    df = pd.DataFrame({"d_tp_bp": tpw.diff() * BP, "dln_wti": np.log(wti_pos).diff()})
    df = df.dropna()
    df = df[df.index <= END_2026]
    return df, dropped


def nw(y: pd.Series, X: pd.DataFrame):
    return sm.OLS(y, sm.add_constant(X)).fit(cov_type="HAC", cov_kwds={"maxlags": NW_LAGS})


def h4a(df: pd.DataFrame) -> dict:
    d = df[df.index >= START_2026]
    fit = nw(d["d_tp_bp"], d[["dln_wti"]])
    t = float(fit.tvalues["dln_wti"])
    return {"beta": float(fit.params["dln_wti"]), "t": t, "p_one": one_sided_p(t, float(fit.pvalues["dln_wti"])),
            "n": int(fit.nobs), "first_week": d.index.min().date(), "last_week": d.index.max().date()}


def h4b(df: pd.DataFrame) -> dict:
    d = df.copy()
    d["d2026"] = (d.index >= START_2026).astype(float)
    d["inter"] = d["d2026"] * d["dln_wti"]
    fit = nw(d["d_tp_bp"], d[["dln_wti", "d2026", "inter"]])
    t = float(fit.tvalues["inter"])
    return {"b_base": float(fit.params["dln_wti"]), "d_inter": float(fit.params["inter"]), "t": t,
            "p_one": one_sided_p(t, float(fit.pvalues["inter"])), "n": int(fit.nobs),
            "n_2026": int(d["d2026"].sum()), "first_week": d.index.min().date()}


def rolling_beta(df: pd.DataFrame, window: int = 52) -> pd.DataFrame:
    """OLS slope of dTP on dln WTI over trailing `window` consecutive weekly observations."""
    x, y = df["dln_wti"], df["d_tp_bp"]
    cov = x.rolling(window).cov(y)
    var = x.rolling(window).var()
    return pd.DataFrame({"beta_52w": cov / var, "n_obs": window}).dropna()


def main() -> pd.DataFrame:
    a, f = load.acm(), load.fred()
    panels = {}
    issues = []
    for name, s in [("ACM", a["ACMTP10"]), ("KW", f["THREEFYTP10"])]:
        df, dropped = weekly_panel(s)
        panels[name] = df
        issues += [f"{name}: {x}" for x in dropped]
    covid_mask = lambda df: df[~((df.index >= COVID[0]) & (df.index <= COVID[1] + pd.Timedelta(days=6)))]

    specs = [
        ("H4a", "primary", "ACM", False, h4a, "Weekly dACMTP10 on dln WTI, 2026 weeks, NW(4), one-sided b>0"),
        ("H4b", "primary", "ACM", False, h4b, "Pooled weekly dACMTP10 on dln WTI with 2026 dummy x dln WTI, NW(4), one-sided d>0"),
        ("R1-H4a", "robustness", "KW", False, h4a, "H4a with dTHREEFYTP10"),
        ("R1-H4b", "robustness", "KW", False, h4b, "H4b with dTHREEFYTP10"),
        ("R3-H4a", "robustness", "ACM", True, h4a, "H4a excluding weekly changes with an endpoint in 2020-03-01 to 2020-04-30 (weeks ending 2020-03-06 to 2020-05-01)"),
        ("R3-H4b", "robustness", "ACM", True, h4b, "H4b excluding weekly changes with an endpoint in 2020-03-01 to 2020-04-30 (weeks ending 2020-03-06 to 2020-05-01)"),
    ]
    rows, res = [], {}
    for tid, fam, model, excl, fn, desc in specs:
        df = panels[model]
        if excl:
            df = covid_mask(df)
        r = fn(df)
        res[tid] = r
        coef = r.get("beta", r.get("d_inter"))
        rule = "t >= 2" if r["t"] >= 2 else "t < 2"
        status = ("pending BH" if r["t"] >= 2 else "killed: t < 2") if fam == "primary" else rule
        hyp = "H4a" if "H4a" in tid else "H4b"
        log_test(tid, hyp, desc, status, r["p_one"], f"coef {coef:.3f} bp per unit dln WTI, t {r['t']:.2f}",
                 r["n"], f"model {model}; NW lags {NW_LAGS}", fam)
        rows.append({"test_id": tid, "family": fam, "model": model, "exclude_covid": excl, **r})
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "h4_oil.csv", index=False, float_format="%.6g")
    rolling_beta(panels["ACM"]).to_csv(OUT / "h4_rolling_beta.csv", float_format="%.6g", index_label="week_end")
    log_run("src/h4_oil.py", {"nw_lags": NW_LAGS, "start_2026_week": START_2026, "end": END_2026,
                               "covid_excl": [str(c.date()) for c in COVID]}, {"results": res, "issues": issues})
    print(out.to_string())
    print("WTI issues:", issues or "none (no weekly WTI value <= 0)")
    return out


if __name__ == "__main__":
    main()
