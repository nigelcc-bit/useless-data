"""Thanksgiving week and drawdown at entry. See PREREG.md (frozen 2026-11-26).

Run from this folder:  python3 run.py
Downloads Yahoo ^GSPC and ^NDX daily closes (cached in data/raw/, not committed),
writes small CSVs to data/, tables/charts to outputs/. Seed 7, 10,000 resamples.
"""
from __future__ import annotations

import datetime as dt
import json
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
from scipy import stats
from statsmodels.stats.multitest import multipletests

HERE = Path(__file__).parent
RAW = HERE / "data" / "raw"
DATA = HERE / "data"
OUT = HERE / "outputs"
for d in (RAW, DATA, OUT):
    d.mkdir(parents=True, exist_ok=True)

SEED = 7
N_DRAWS = 10_000
END = "2026-11-25"
GSPC_YEARS = range(1950, 2026)          # 1950-2025
SPLIT = 1987                            # halves: <=1987 vs >=1988
DD_LO, DD_HI = -0.20, -0.10
LOOKBACK = 252
rng = np.random.default_rng(SEED)
TRIALS: list[dict] = []


# ------------------------------------------------------------------ data
def fetch(symbol: str, start: str, end: str) -> pd.Series:
    cache = RAW / f"yahoo_{symbol.replace('^', '_')}.json"
    if not cache.exists():
        p1 = int(pd.Timestamp(start, tz="UTC").timestamp())
        p2 = int((pd.Timestamp(end, tz="UTC") + pd.Timedelta(days=1)).timestamp())
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        for attempt in range(5):
            r = requests.get(url, params={"period1": p1, "period2": p2, "interval": "1d"},
                             headers={"User-Agent": "Mozilla/5.0 (research)"}, timeout=60)
            if r.status_code == 200:
                cache.write_text(r.text)
                break
            time.sleep(2 ** attempt)
        else:
            raise RuntimeError(f"Yahoo fetch failed for {symbol}: {r.status_code}")
    res = json.loads(cache.read_text())["chart"]["result"][0]
    idx = pd.to_datetime(res["timestamp"], unit="s", utc=True).tz_convert("America/New_York")
    s = pd.Series(res["indicators"]["quote"][0]["close"], index=idx.tz_localize(None).normalize(),
                  name=symbol, dtype=float).dropna()
    s = s[~s.index.duplicated(keep="last")].sort_index()
    return s.loc[start:end]


def thanksgiving(year: int) -> pd.Timestamp:
    nov1 = dt.date(year, 11, 1)
    first_thu = 1 + (3 - nov1.weekday()) % 7
    return pd.Timestamp(year, 11, first_thu + 21)


def build_events(close: pd.Series, years) -> pd.DataFrame:
    idx = close.index
    rows = []
    for y in years:
        tg = thanksgiving(y)
        if tg - pd.Timedelta(days=6) > idx[-1]:
            continue
        i_f0 = idx.searchsorted(tg - pd.Timedelta(days=6), side="right") - 1
        i_wb = idx.searchsorted(tg, side="left") - 1
        i_bf = idx.searchsorted(tg, side="right")
        if idx[i_wb] == tg:  # market open on Thanksgiving would break the definition
            raise ValueError(f"trading day on Thanksgiving {tg.date()}")
        if i_bf >= len(idx):
            i_bf = None
        dd = np.nan
        if i_f0 - LOOKBACK + 1 >= 0:
            dd = close.iloc[i_f0] / close.iloc[i_f0 - LOOKBACK + 1: i_f0 + 1].max() - 1
        row = {"year": y, "thanksgiving": tg.date(), "f0": idx[i_f0].date(), "wb": idx[i_wb].date(),
               "dd_entry": dd, "i_f0": i_f0, "i_wb": i_wb,
               "wtd_f0_to_wb": close.iloc[i_wb] / close.iloc[i_f0] - 1,
               "wb_ret": close.iloc[i_wb] / close.iloc[i_wb - 1] - 1}
        if i_bf is not None:
            dec = close[(idx.year == y) & (idx.month == 12)]
            row.update({
                "bf": idx[i_bf].date(), "i_bf": i_bf,
                "week_ret": close.iloc[i_bf] / close.iloc[i_f0] - 1,
                "week_days": i_bf - i_f0,
                "bf_ret": close.iloc[i_bf] / close.iloc[i_bf - 1] - 1,
                "ma_ret": close.iloc[i_bf + 1] / close.iloc[i_bf] - 1 if i_bf + 1 < len(idx) else np.nan,
                "ye_date": dec.index[-1].date() if len(dec) else None,
                "ye_up": float(dec.iloc[-1] > close.iloc[i_bf]) if len(dec) and dec.index[-1].month == 12
                and y < 2026 else np.nan,
            })
        rows.append(row)
    return pd.DataFrame(rows).set_index("year")


# ------------------------------------------------------------------ stats helpers
STAT_FUNCS = {"hit": lambda a: np.mean(a > 0, axis=-1),
              "median": lambda a: np.median(a, axis=-1),
              "mean": lambda a: np.mean(a, axis=-1)}


def emp_p(obs: float, null: np.ndarray) -> float:
    return float(min(1.0, 2 * min(np.mean(null >= obs), np.mean(null <= obs))))


def draw_matrix(pools: list[np.ndarray]) -> np.ndarray:
    """N_DRAWS x n_years matrix: one random element per year per draw."""
    m = np.empty((N_DRAWS, len(pools)))
    for j, pool in enumerate(pools):
        m[:, j] = pool[rng.integers(0, len(pool), N_DRAWS)]
    return m


def seasonal_test(label, index_name, ev, obs_col, pools, years, halves):
    obs = ev.loc[years, obs_col].values
    null = draw_matrix(pools)
    out = []
    for stat, fn in STAT_FUNCS.items():
        o = float(fn(obs))
        nd = fn(null)
        signs = []
        for h in halves:
            mask = np.isin(years, h)
            signs.append(float(fn(obs[mask]) - np.median(fn(null[:, mask]))))
        out.append({"id": f"{label}-{stat}", "claim": label.split("-")[0], "index": index_name,
                    "test": f"{obs_col} {stat} vs one random other per year (empirical)",
                    "n": len(obs), "observed": o, "null_median": float(np.median(nd)),
                    "raw_p": emp_p(o, nd), "effect_half1": signs[0], "effect_half2": signs[1]})
    return out, null


def beta_summary(k: int, n: int):
    a, b = 1 + k, 1 + n - k
    return a / (a + b), stats.beta.ppf(0.05, a, b), stats.beta.ppf(0.95, a, b)


def c3_row(tid, index_name, ok_mask, ye_up, years, halves, note=""):
    dd_up, ot_up = ye_up[ok_mask], ye_up[~ok_mask]
    k1, n1 = int(dd_up.sum()), int(len(dd_up))
    k0, n0 = int(ot_up.sum()), int(len(ot_up))
    p = stats.fisher_exact([[k1, n1 - k1], [k0, n0 - k0]])[1] if n1 and n0 else np.nan
    pm, lo, hi = beta_summary(k1, n1)
    pm0, lo0, hi0 = beta_summary(k0, n0)
    effs = []
    for h in halves:
        m = np.isin(years, h)
        a, b = ye_up[ok_mask & m], ye_up[~ok_mask & m]
        effs.append(float(a.mean() - b.mean()) if len(a) and len(b) else np.nan)
    return {"id": tid, "claim": "C3", "index": index_name,
            "test": "year-end up | drawdown 10-20% vs other (Fisher)" + note,
            "n": n1, "observed": k1 / n1 if n1 else np.nan, "null_median": k0 / n0 if n0 else np.nan,
            "raw_p": float(p), "effect_half1": effs[0], "effect_half2": effs[1],
            "dd_hits": k1, "dd_n": n1, "other_hits": k0, "other_n": n0,
            "post_mean": pm, "ci90_lo": lo, "ci90_hi": hi,
            "other_post_mean": pm0, "other_ci90_lo": lo0, "other_ci90_hi": hi0}


# ------------------------------------------------------------------ main
def main():
    gspc = fetch("^GSPC", "1950-01-03", END)
    ndx = fetch("^NDX", "1985-01-01", END)
    gspc.to_csv(DATA / "gspc_close.csv", header=["close"])
    ndx.to_csv(DATA / "ndx_close.csv", header=["close"])

    years = np.array(list(GSPC_YEARS))
    halves = [years[years <= SPLIT], years[years > SPLIT]]
    ev = build_events(gspc, list(GSPC_YEARS) + [2026])
    ev_test = ev.loc[years]
    ev.drop(columns=["i_f0", "i_wb", "i_bf"], errors="ignore").to_csv(DATA / "gspc_thanksgiving_events.csv")

    idx = gspc.index
    r1 = gspc.pct_change()
    r4 = gspc / gspc.shift(4) - 1

    # pools for C1
    week_pools, wb_pools, bf_pools = [], [], []
    for y in years:
        e = ev.loc[y]
        pos = np.arange(len(idx))
        in_y = idx.year == y
        overlap = (pos - 3 <= e.i_bf) & (pos >= e.i_f0 + 1)
        week_pools.append(r4.values[in_y & ~overlap & ~np.isnan(r4.values)])
        others = in_y & ~np.isnan(r1.values)
        wb_pools.append(r1.values[others & (pos != e.i_wb)])
        bf_pools.append(r1.values[others & (pos != e.i_bf)])

    rows = []
    for label, col, pools in [("C1-week", "week_ret", week_pools), ("C1-WB", "wb_ret", wb_pools),
                              ("C1-BF", "bf_ret", bf_pools)]:
        out, null = seasonal_test(label, "GSPC", ev, col, pools, years, halves)
        rows += out
        if label == "C1-week":
            week_null_hit = STAT_FUNCS["hit"](null)
            week_null_mean = STAT_FUNCS["mean"](null)

    # C2 decay
    wk = ev_test["week_ret"]
    h1, h2 = wk.loc[halves[0]], wk.loc[halves[1]]
    k1, k2 = int((h1 > 0).sum()), int((h2 > 0).sum())
    p_f = stats.fisher_exact([[k1, len(h1) - k1], [k2, len(h2) - k2]])[1]
    p_mw = stats.mannwhitneyu(h1, h2, alternative="two-sided").pvalue
    d_hit = k2 / len(h2) - k1 / len(h1)
    d_med = float(h2.median() - h1.median())
    rows.append({"id": "C2-hit", "claim": "C2", "index": "GSPC",
                 "test": "week hit rate 1950-1987 vs 1988-2025 (Fisher)", "n": len(wk),
                 "observed": k2 / len(h2), "null_median": k1 / len(h1), "raw_p": float(p_f),
                 "effect_half1": d_hit, "effect_half2": d_med})
    rows.append({"id": "C2-median", "claim": "C2", "index": "GSPC",
                 "test": "week return 1950-1987 vs 1988-2025 (Mann-Whitney)", "n": len(wk),
                 "observed": float(h2.median()), "null_median": float(h1.median()), "raw_p": float(p_mw),
                 "effect_half1": d_hit, "effect_half2": d_med})
    roll = (wk > 0).astype(float).rolling(20).mean()
    roll.to_csv(OUT / "c2_rolling20_hit_rate.csv", header=["hit_rate_20y"])

    # C3 drawdown conditioning (years with full 252-day lookback only)
    c3y = ev_test.dropna(subset=["dd_entry"])
    yrs3 = c3y.index.values
    in_dd = ((c3y["dd_entry"] >= DD_LO) & (c3y["dd_entry"] <= DD_HI)).values
    rows.append(c3_row("C3-main", "GSPC", in_dd, c3y["ye_up"].values, yrs3, halves))
    c3y[in_dd][["f0", "dd_entry", "bf", "week_ret", "ye_up"]].to_csv(OUT / "c3_drawdown_years_gspc.csv")

    # C3 control: every Oct-Dec Friday (last trading day of each week)
    s = gspc.to_frame("c")
    s["i"] = np.arange(len(s))
    s["wk"] = s.index.to_period("W-FRI")
    fri = s.groupby("wk").tail(1)
    fri = fri[(fri.index.month >= 10) & (fri.index.year >= 1950) & (fri.index.year <= 2025)]
    crow = []
    for d, r in fri.iterrows():
        i = int(r["i"])
        if i - LOOKBACK + 1 < 0:
            continue
        dec = gspc[(idx.year == d.year) & (idx.month == 12)]
        i_ye = idx.get_loc(dec.index[-1])
        if i + 4 >= i_ye:
            continue
        dd = gspc.iloc[i] / gspc.iloc[i - LOOKBACK + 1: i + 1].max() - 1
        crow.append({"date": d.date(), "year": d.year, "dd": dd,
                     "ye_up": float(gspc.iloc[i_ye] > gspc.iloc[i + 4])})
    ctrl = pd.DataFrame(crow)
    ctrl.to_csv(DATA / "gspc_octdec_fridays.csv", index=False)
    cin = ((ctrl["dd"] >= DD_LO) & (ctrl["dd"] <= DD_HI)).values
    rows.append(c3_row("C3-control", "GSPC", cin, ctrl["ye_up"].values, ctrl["year"].values, halves,
                       note=" [CONTROL: all Oct-Dec Fridays; overlapping, p optimistic]"))

    # C4 liquidity
    for label, col, ev_idx in [("C4-BF", "bf_ret", "i_bf"), ("C4-MA", "ma_ret", None)]:
        special = ev_test[col].abs().values
        pos_special = set(ev_test["i_bf"].astype(int)) if ev_idx else set(ev_test["i_bf"].astype(int) + 1)
        in_years = np.isin(idx.year, years)
        mask = in_years & ~np.isnan(r1.values) & ~np.isin(np.arange(len(idx)), list(pos_special))
        other = np.abs(r1.values[mask])
        ratio = np.median(special) / np.median(other)
        p = stats.mannwhitneyu(special, other, alternative="two-sided").pvalue
        effs = []
        for h in halves:
            sm = np.isin(ev_test.index.values, h)
            om = mask & np.isin(idx.year, h)
            effs.append(float(np.median(special[sm]) / np.median(np.abs(r1.values[om])) - 1))
        rows.append({"id": label, "claim": "C4", "index": "GSPC",
                     "test": f"|{col}| vs |all other days| (Mann-Whitney)", "n": len(special),
                     "observed": float(ratio), "null_median": 1.0, "raw_p": float(p),
                     "effect_half1": effs[0], "effect_half2": effs[1],
                     "median_abs_special": float(np.median(special)), "median_abs_other": float(np.median(other))})

    # Secondary: NDX (years with full lookback, 1986-2025)
    nev = build_events(ndx, range(1985, 2027))
    nyears = np.array([y for y in range(1985, 2026) if not np.isnan(nev.loc[y, "dd_entry"])])
    nh = [nyears[: len(nyears) // 2], nyears[len(nyears) // 2:]]
    nidx = ndx.index
    n4 = ndx / ndx.shift(4) - 1
    npools = []
    for y in nyears:
        e = nev.loc[y]
        pos = np.arange(len(nidx))
        in_y = nidx.year == y
        overlap = (pos - 3 <= e.i_bf) & (pos >= e.i_f0 + 1)
        npools.append(n4.values[in_y & ~overlap & ~np.isnan(n4.values)])
    out, _ = seasonal_test("C1-week", "NDX", nev, "week_ret", npools, nyears, nh)
    for o in out:
        o["id"] = "NDX-" + o["id"]
    rows += out
    nt = nev.loc[nyears]
    nin = ((nt["dd_entry"] >= DD_LO) & (nt["dd_entry"] <= DD_HI)).values
    r = c3_row("NDX-C3-main", "NDX", nin, nt["ye_up"].values, nyears, nh)
    rows.append(r)
    nev.drop(columns=["i_f0", "i_wb", "i_bf"], errors="ignore").to_csv(DATA / "ndx_thanksgiving_events.csv")

    # BH across all p-values
    T = pd.DataFrame(rows)
    T["bh_p"] = multipletests(T["raw_p"].values, method="fdr_bh")[1]
    T["primary"] = T["id"].isin(["C1-week-hit", "C2-hit", "C3-main", "C4-BF"])
    T.to_csv(OUT / "trials.csv", index=False)

    # verdicts (primary tests)
    def same_sign(a, b):
        return bool(np.isfinite(a) and np.isfinite(b) and np.sign(a) == np.sign(b) and a != 0)

    def rule(r):
        """PREREG rule, applied literally: WEAK if raw p < 0.10 OR halves disagree."""
        ss = same_sign(r.effect_half1, r.effect_half2)
        literal = "CONFIRMED" if (r.bh_p < 0.05 and ss) else ("WEAK" if (r.raw_p < 0.10 or not ss) else "KILLED")
        # alternative reading (halves only downgrade an otherwise-significant result); reported, not used
        alt = "CONFIRMED" if (r.bh_p < 0.05 and ss) else (
            "WEAK" if (r.raw_p < 0.10 or r.bh_p < 0.05) else "KILLED")
        if r.claim == "C3" and (r.dd_n < 10 or (r.ci90_lo <= 0.5 <= r.ci90_hi)):
            literal = alt = "INCONCLUSIVE"
        return literal, alt, ss

    T[["verdict_rule", "alt_reading", "same_sign_halves"]] = T.apply(
        lambda r: pd.Series(rule(r)), axis=1)
    T.to_csv(OUT / "trials.csv", index=False)
    verdicts = {r.claim: {"verdict": r.verdict_rule, "alt_reading": r.alt_reading,
                          "same_sign_halves": r.same_sign_halves, "raw_p": r.raw_p, "bh_p": r.bh_p}
                for _, r in T[T["primary"]].iterrows()}

    # 2026 setup (not tested)
    e26 = ev.loc[2026]
    setup = {"f0": str(e26.f0), "wb": str(e26.wb), "dd_entry": float(e26.dd_entry),
             "wtd_f0_to_wb": float(e26.wtd_f0_to_wb),
             "in_10_20_correction": bool(DD_LO <= e26.dd_entry <= DD_HI)}
    ne26 = nev.loc[2026]
    setup_ndx = {"f0": str(ne26.f0), "dd_entry": float(ne26.dd_entry), "wtd_f0_to_wb": float(ne26.wtd_f0_to_wb)}

    summary = {
        "data": {"gspc_first": str(gspc.index[0].date()), "gspc_last": str(gspc.index[-1].date()),
                 "ndx_first": str(ndx.index[0].date()), "ndx_last": str(ndx.index[-1].date()),
                 "gspc_test_years": [int(years[0]), int(years[-1]), int(len(years))],
                 "c3_years": [int(yrs3[0]), int(yrs3[-1]), int(len(yrs3))],
                 "ndx_years": [int(nyears[0]), int(nyears[-1]), int(len(nyears))],
                 "week_days_counts": ev_test["week_days"].value_counts().to_dict(),
                 "control_fridays": int(len(ctrl)), "control_dd_fridays": int(cin.sum())},
        "week_descriptive": {"hit": float((wk > 0).mean()), "median": float(wk.median()),
                             "mean": float(wk.mean()), "n": int(len(wk)),
                             "half1_hit": k1 / len(h1), "half2_hit": k2 / len(h2),
                             "half1_median": float(h1.median()), "half2_median": float(h2.median())},
        "c3_other_years_n": int((~in_dd).sum()),
        "verdicts": verdicts, "setup_2026_gspc": setup, "setup_2026_ndx": setup_ndx,
        "trials": int(len(T)),
    }
    (OUT / "results.json").write_text(json.dumps(summary, indent=2, default=str))

    # charts
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(roll.index, roll.values, color="#2b2b2b")
    ax.axhline(float(np.median(week_null_hit)), color="#d9534f", ls="--", lw=1,
               label="other 4-day windows (null median)")
    ax.set_ylim(0, 1)
    ax.set_ylabel("share of weeks up, trailing 20 years")
    ax.legend(frameon=False, fontsize=8)
    ax.set_title(f"S&P 500 Thanksgiving-week hit rate, rolling 20 years: "
                 f"{k1 / len(h1):.0%} in 1950-87 vs {k2 / len(h2):.0%} in 1988-2025", fontsize=10)
    fig.tight_layout()
    fig.savefig(OUT / "c2_rolling_hit_rate.png", dpi=150)

    fig, ax = plt.subplots(figsize=(9, 4))
    ax.hist(week_null_mean * 100, bins=60, color="#bbbbbb", label="mean of a random other 4-day window per year")
    ax.axvline(wk.mean() * 100, color="#d9534f", lw=2, label="Thanksgiving week mean")
    ax.set_xlabel("mean return across 1950-2025 (%)")
    ax.legend(frameon=False, fontsize=8)
    ax.set_title(f"Thanksgiving-week mean return vs other weeks (p = {T.set_index('id').loc['C1-week-mean','raw_p']:.3f})",
                 fontsize=10)
    fig.tight_layout()
    fig.savefig(OUT / "c1_week_vs_null.png", dpi=150)

    pd.set_option("display.width", 220)
    print(T[["id", "n", "observed", "null_median", "raw_p", "bh_p", "effect_half1", "effect_half2",
             "verdict_rule", "alt_reading"]]
          .round(4).to_string(index=False))
    print(T[T.claim == "C3"][["id", "dd_hits", "dd_n", "other_hits", "other_n", "post_mean",
                              "ci90_lo", "ci90_hi"]].round(4).to_string(index=False))
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
