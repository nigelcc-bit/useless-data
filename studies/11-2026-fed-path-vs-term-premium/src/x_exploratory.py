"""Exploratory checks X1 and X2 (NOT in the BH family; family=exploratory). Writes E11 and E12.

X1  Model mechanics: daily dTP10 on dY10 (OLS, HC1), Kim-Wright and ACM, 1990-2026 and 2026 only.
X2  Par vs zero gap over 2025-12-31 to 2026-11-13: why dDGS10 (+97bp) exceeds dACMY10 (+87bp).
    Builds the 10y par yield implied by the ACM 1-10y zero curve and splits
        dDGS10 - dACMY10 = d(ACM par - ACM zero)  [curve shape / par-vs-zero, incl. compounding]
                         + d(DGS10 - ACM par)     [residual: CMT vs fitted curve]
    and checks for a date mismatch (levels on both end dates, lead/lag correlation of daily changes).

    python -m src.x_exploratory
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm

from src import load
from src.common import BP, END_2026, OUT, log_run, log_test, pairwise_diff
from src.exhibits import AQUA, BLUE, INK, INK2, MUTED, ORANGE, PULLED, SRC_ACM, SRC_FRED, EX, fig_ax, finish

START = pd.Timestamp("2025-12-31")
MATS = np.arange(1, 11)
COUPON_T = np.arange(1, 21) / 2  # semiannual coupon dates of a 10y bond


# --- X1 ------------------------------------------------------------------------

def x1() -> pd.DataFrame:
    a, kw = load.acm(), load.kim_wright()
    df = pd.DataFrame({"acm_tp": a["ACMTP10"], "acm_y": a["ACMY10"], "kw_tp": kw["KWTP10"], "kw_y": kw["KWY10"]})
    rows = []
    for model, tp, y in [("KW", "kw_tp", "kw_y"), ("ACM", "acm_tp", "acm_y")]:
        d = pairwise_diff(df, [tp, y]) * BP
        d = d[d.index <= END_2026]
        for sample, g in [("1990-2026", d), ("2026", d.loc["2026"])]:
            fit = sm.OLS(g[tp], sm.add_constant(g[y])).fit(cov_type="HC1")
            rows.append({"model": model, "sample": sample, "beta": float(fit.params[y]), "t": float(fit.tvalues[y]),
                         "p_two": float(fit.pvalues[y]), "r2": float(fit.rsquared), "n": int(fit.nobs),
                         "first": g.index.min().date(), "last": g.index.max().date()})
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "x1_tp_on_yield.csv", index=False, float_format="%.6g")
    for r in out.itertuples():
        log_test(f"X1-{r.model}-{r.sample}", "X1", f"Daily d{r.model} TP10 on d{r.model} Y10, OLS HC1, {r.sample}",
                 "exploratory, descriptive", r.p_two, f"beta {r.beta:.3f}, R2 {r.r2:.3f}, t {r.t:.1f}", r.n,
                 "not in BH family", "exploratory")
    return out


# --- X2 ------------------------------------------------------------------------

def par_from_zero(zero_pct: pd.Series, compounding: str = "continuous") -> float:
    """10y semiannual par yield (%) implied by annual-node zero yields 1..10y (%).
    Linear interpolation between nodes, flat below 1y."""
    y = np.interp(COUPON_T, MATS, zero_pct.values / 100)
    p = np.exp(-y * COUPON_T) if compounding == "continuous" else (1 + y) ** (-COUPON_T)
    return float(2 * (1 - p[-1]) / p.sum() * 100)


def x2() -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    a, f, kw = load.acm(), load.fred(), load.kim_wright()
    zcols = [f"ACMY{n:02d}" for n in MATS]
    dates = [START, END_2026]
    missing = [(c, d.date()) for d in dates for c, s in
               [("DGS10", f["DGS10"]), ("DGS2", f["DGS2"]), ("ACMY10", a["ACMY10"]), ("KWY10", kw["KWY10"])]
               if pd.isna(s.get(d, np.nan))]
    lev = []
    for d in dates:
        r = {"date": d.date(), "DGS10": f.loc[d, "DGS10"], "DGS2": f.loc[d, "DGS2"], "ACMY10": a.loc[d, "ACMY10"],
             "KWY10": kw.loc[d, "KWY10"]}
        for comp in ("continuous", "annual"):
            r[f"ACM_par10_{comp}"] = par_from_zero(a.loc[d, zcols], comp)
        r["slope_2s10s_bp"] = (r["DGS10"] - r["DGS2"]) * BP
        r["ACM_zero_minus_DGS10_bp"] = (r["ACMY10"] - r["DGS10"]) * BP
        r["KW_zero_minus_DGS10_bp"] = (r["KWY10"] - r["DGS10"]) * BP
        lev.append(r)
    lev = pd.DataFrame(lev).set_index("date")
    s, e = lev.iloc[0], lev.iloc[1]
    d_dgs, d_acm, d_kw = (e.DGS10 - s.DGS10) * BP, (e.ACMY10 - s.ACMY10) * BP, (e.KWY10 - s.KWY10) * BP
    split = {}
    for comp in ("continuous", "annual"):
        pc = f"ACM_par10_{comp}"
        shape = ((e[pc] - e.ACMY10) - (s[pc] - s.ACMY10)) * BP
        resid = ((e.DGS10 - e[pc]) - (s.DGS10 - s[pc])) * BP
        split[comp] = {"curve_shape_bp": shape, "residual_cmt_vs_fitted_bp": resid, "d_acm_par_bp": (e[pc] - s[pc]) * BP}

    # date-mismatch check: lead/lag correlation of daily changes in 2026
    dz = a["ACMY10"].dropna().diff()
    dp = f["DGS10"].dropna().diff()
    j = pd.concat({"z": dz, "p": dp}, axis=1, sort=True).dropna()
    j = j[(j.index >= "2026-01-01") & (j.index <= END_2026)]
    lags = {L: float(j.z.corr(j.p.shift(L))) for L in (-1, 0, 1)}

    # in-sample fit of the par construction, 2026 daily
    za = a[zcols].dropna()
    za = za[(za.index >= "2026-01-01") & (za.index <= END_2026)]
    par_ts = pd.DataFrame({comp: za.apply(lambda r: par_from_zero(r, comp), axis=1) for comp in ("continuous", "annual")})
    err = par_ts.sub(f["DGS10"], axis=0).dropna() * BP
    fit_err = {comp: {"mean_bp": float(err[comp].mean()), "median_abs_bp": float(err[comp].abs().median())}
               for comp in err}

    summary = {"d_dgs10_bp": d_dgs, "d_acmy10_bp": d_acm, "d_kwy10_bp": d_kw, "gap_dgs10_minus_acm_bp": d_dgs - d_acm,
               "gap_dgs10_minus_kw_bp": d_dgs - d_kw, "split": split, "lag_corr_2026": lags,
               "par_fit_err_2026": fit_err, "missing_levels": missing}
    comp_rows = pd.DataFrame([
        {"component": "dDGS10 (par, CMT)", "bp": d_dgs},
        {"component": "less: residual DGS10 vs ACM-implied par", "bp": -split["continuous"]["residual_cmt_vs_fitted_bp"]},
        {"component": "less: curve shape (ACM par minus ACM zero)", "bp": -split["continuous"]["curve_shape_bp"]},
        {"component": "dACMY10 (zero, fitted)", "bp": d_acm},
        {"component": "memo: dKWY10 (zero, fitted)", "bp": d_kw},
        {"component": "memo: curve shape if ACM yields were annual-compounded", "bp": split["annual"]["curve_shape_bp"]},
        {"component": "memo: residual if ACM yields were annual-compounded", "bp": split["annual"]["residual_cmt_vs_fitted_bp"]},
    ])
    lev.to_csv(OUT / "x2_levels.csv", float_format="%.6g")
    comp_rows.to_csv(OUT / "x2_gap_split.csv", index=False, float_format="%.6g")
    c = split["continuous"]
    log_test("X2", "X2", "dDGS10 vs dACMY10 gap, 2025-12-31 to 2026-11-13: curve shape vs residual vs date mismatch",
             "exploratory, descriptive", None,
             f"gap {d_dgs - d_acm:.1f}bp = curve shape {c['curve_shape_bp']:.1f} + residual {c['residual_cmt_vs_fitted_bp']:.1f}; "
             f"lag corr -1/0/+1: {lags[-1]:.2f}/{lags[0]:.2f}/{lags[1]:.2f}", 2,
             "ACM yields treated as continuously compounded (annual-compounding split in out/x2_gap_split.csv)",
             "exploratory")
    return lev, comp_rows, summary


# --- exhibits --------------------------------------------------------------------

def e11(t: pd.DataFrame) -> str:
    fig, ax = fig_ax(8.5, 4.8)
    groups = ["1990-2026", "2026"]
    x = np.arange(len(groups))
    w = 0.34
    for i, (model, color, lab) in enumerate([("ACM", BLUE, "ACM"), ("KW", ORANGE, "Kim-Wright")]):
        m = t[t.model == model].set_index("sample").loc[groups]
        bars = ax.bar(x + (i - 0.5) * w, m.r2, w - 0.03, color=color, label=lab)
        for b, (r2, beta) in zip(bars, zip(m.r2, m.beta)):
            ax.annotate(f"R² {r2:.2f}\nβ {beta:.2f}", (b.get_x() + b.get_width() / 2, r2), xytext=(0, 3),
                        textcoords="offset points", ha="center", fontsize=8, color=INK)
    ax.set_xticks(x, ["1990-2026 (daily)", "2026 to 13 Nov (daily)"])
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("R-squared of daily dTP10 on daily dY10", color=INK, fontsize=9)
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    return finish(fig, "E11_x1_tp_tracks_yield", "E11. How much of each model's daily term-premium move is just the yield move (X1, exploratory)",
                  f"OLS of daily change in TP10 on daily change in the model's own 10y zero yield, HC1. β = bp of TP per bp of yield. "
                  f"Exploratory, not in the BH family. Source: {SRC_ACM}; FRED THREEFY10, THREEFYTP10. {PULLED}",
                  t.set_index(["model", "sample"]))


def e12(comp: pd.DataFrame, summary: dict) -> str:
    main = comp.iloc[:4].reset_index(drop=True)
    fig, ax = fig_ax(9, 4.8)
    labels = ["Change in DGS10\n(par, CMT)", "CMT vs fitted\ncurve (residual)", "Curve shape\n(par vs zero)",
              "Change in ACMY10\n(zero, fitted)"]
    run = main.bp.iloc[0]
    bottoms, heights, colors = [0], [run], [INK2]
    for v in main.bp.iloc[1:3]:
        bottoms.append(run + v if v < 0 else run)
        heights.append(abs(v))
        colors.append(MUTED if v < 0 else AQUA)
        run += v
    bottoms.append(0)
    heights.append(main.bp.iloc[3])
    colors.append(BLUE)
    bars = ax.bar(range(4), heights, bottom=bottoms, color=colors, width=0.6)
    vals = [main.bp.iloc[0], main.bp.iloc[1], main.bp.iloc[2], main.bp.iloc[3]]
    for b, v in zip(bars, vals):
        ax.annotate(f"{v:+.1f}", (b.get_x() + b.get_width() / 2, b.get_y() + b.get_height()), xytext=(0, 3),
                    textcoords="offset points", ha="center", fontsize=8.5, color=INK)
    ax.set_xticks(range(4), labels)
    ax.set_ylabel("Change, 31 Dec 2025 to 13 Nov 2026, bp", color=INK, fontsize=9)
    ax.set_ylim(0, 110)
    lc = summary["lag_corr_2026"]
    ax.annotate(f"Kim-Wright zero (THREEFY10): {summary['d_kwy10_bp']:+.1f}bp\n"
                f"Date check: daily-change correlation lag -1 / 0 / +1 = {lc[-1]:.2f} / {lc[0]:.2f} / {lc[1]:.2f}",
                (0.98, 0.97), xycoords="axes fraction", ha="right", va="top", fontsize=8, color=INK)
    return finish(fig, "E12_x2_par_vs_zero_gap", "E12. Why the 10-year par yield rose 10bp more than the ACM zero yield (X2, exploratory)",
                  "ACM par = 10y semiannual par yield implied by ACM 1-10y zero yields (treated as continuously compounded; "
                  "linear interpolation, flat below 1y). Curve shape = change in (ACM par minus ACM zero). Residual = change in "
                  f"(DGS10 minus ACM par). Source: {SRC_ACM}; {SRC_FRED}. {PULLED}", comp)


def main() -> None:
    EX.mkdir(parents=True, exist_ok=True)
    t1 = x1()
    lev, comp, summary = x2()
    made = [e11(t1), e12(comp, summary)]
    log_run("src/x_exploratory.py", {"x1": "daily dTP10 on dY10, HC1, <= 2026-11-13", "x2_window": [START, END_2026],
                                      "par_build": "semiannual 10y, linear interp, flat < 1y"},
            {"x1": t1[["model", "sample", "beta", "r2", "n"]].to_dict("records"), "x2": summary, "exhibits": made})
    print(t1.to_string())
    print(lev.T.to_string())
    print(comp.to_string())
    print(summary)


if __name__ == "__main__":
    main()
