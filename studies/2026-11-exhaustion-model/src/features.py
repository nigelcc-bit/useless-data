"""Daily features and targets per asset. PREREGISTRATION Part C4, C6; prompt section 4.

All features at t use data observable at the close of t (monthly series lagged m+2,
daily BAA10Y at t-1). Targets use t+1 onward only.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

import episodes as epi

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"
EVENT_START = {"SPX": "1954-09-01", "NDX": "1986-10-01", "SOX": "1995-05-01"}
TRAIN_END = pd.Timestamp("2017-12-31")
HOLD_END = pd.Timestamp("2026-11-20")


def load():
    C = pd.read_parquet(PROC / "closes.parquet")
    M = pd.read_parquet(PROC / "monthly.parquet")
    B = pd.read_parquet(PROC / "baa10y.parquet")["BAA10Y"]
    return C, M, B


def lag_monthly(s: pd.Series, dates: pd.DatetimeIndex, lag_months: int = 2) -> pd.Series:
    """Value for month m usable from the first trading day of month m+lag."""
    s = s.dropna()
    usable_from = s.index + pd.DateOffset(months=lag_months)
    s2 = pd.Series(s.to_numpy(), index=usable_from)
    return s2.reindex(dates, method="ffill")


def lag_monthly_month(s: pd.Series, dates: pd.DatetimeIndex, lag_months: int = 2) -> pd.Series:
    """Month label (m) of the latest usable value at each date."""
    s = s.dropna()
    lab = pd.Series(s.index, index=s.index + pd.DateOffset(months=lag_months))
    return lab.reindex(dates, method="ffill")


def daily_frame(asset: str, C, M, B, thresholds: dict) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    close = C[asset].dropna()
    idx = close.index
    state, E, V = epi.run_engine(close)
    d = pd.DataFrame(index=idx)
    d["close"] = close
    d["P"] = state["P"]
    d["Pi"] = state["Pi"]
    d["in_ep"] = state["in_ep"]
    d["ep"] = state["ep"]
    d["i"] = np.arange(len(idx))
    d["depth"] = close / state["P"] - 1
    d["dist252"] = close / close.rolling(252, min_periods=252).max() - 1
    d["above200"] = (close > close.rolling(200, min_periods=200).mean()).astype(float)
    d.loc[close.rolling(200, min_periods=200).mean().isna(), "above200"] = np.nan
    d["duration"] = d["i"] - state["Pi"]
    d["legs"] = state["legs"].astype(float)
    d["ret63"] = close / close.shift(63) - 1
    lr = np.log(close).diff()
    d["rvol20"] = lr.rolling(20).std() * np.sqrt(252)
    d["rvol_max_prior20"] = d["rvol20"].shift(1).rolling(20).max()
    # market-wide series on this asset's calendar (ffill not allowed: exact dates only)
    vix = C["VIX"].reindex(idx)
    v3 = C["VIX3M"].reindex(idx)
    d["vix"] = vix
    vfull = C["VIX"].dropna()
    p90 = vfull.shift(1).rolling(1260, min_periods=1260).quantile(0.90)
    d["vixhi"] = (vix >= p90.reindex(idx)).astype(float)
    d.loc[p90.reindex(idx).isna() | vix.isna(), "vixhi"] = np.nan
    d["vratio"] = vix / v3
    # monthly, lagged m+2
    ff = M["FEDFUNDS"].dropna()
    ff6 = (ff - ff.shift(6)).dropna()
    ch = lag_monthly(ff6, idx)
    d["fed6m"] = np.where(ch >= 0.50 - 1e-9, 1.0, np.where(ch <= -0.50 + 1e-9, -1.0, 0.0))
    d.loc[ch.isna(), "fed6m"] = np.nan
    sp = M["BAA_GS10"].dropna()
    d["baa_gs10_lag"] = lag_monthly(sp, idx)
    d["baa_gs10_lag_month"] = lag_monthly_month(sp, idx)
    kr = M["KR_EXPORTS_USD_SA"].dropna().loc["1969-01-01":]
    kyoy = (kr / kr.shift(12) - 1).dropna().loc["1970-01-01":]
    kd3 = (kyoy - kyoy.shift(3)).dropna()
    d["kr_yoy"] = lag_monthly(kyoy, idx)
    d["kr_d3"] = lag_monthly(kd3, idx)
    d["baa10y_tm1"] = B.reindex(idx, method="ffill").shift(1)
    # credit change since reference peak (H3)
    peak_month = pd.DatetimeIndex(idx[d["Pi"].to_numpy()]).to_period("M").to_timestamp()
    base_month = peak_month - pd.DateOffset(months=1)
    cur_month = pd.DatetimeIndex(d["baa_gs10_lag_month"])
    base_month = pd.DatetimeIndex(np.minimum(base_month.values, cur_month.values))
    d["baa_base"] = sp.reindex(base_month).to_numpy()
    d["credit_chg"] = d["baa_gs10_lag"] - d["baa_base"]
    d["credit_ratio"] = d["credit_chg"] / d["depth"].abs().clip(lower=1e-4)
    b_before_peak = B.reindex(idx, method="ffill").shift(1).to_numpy()[np.maximum(d["Pi"].to_numpy() - 0, 0)]
    d["credit_chg_daily"] = d["baa10y_tm1"] - b_before_peak
    d["credit_ratio_daily"] = d["credit_chg_daily"] / d["depth"].abs().clip(lower=1e-4)
    # targets (forward only)
    c = close.to_numpy()
    n = len(c)
    fwdmin63 = np.full(n, np.nan)
    for i in range(n - 63):
        fwdmin63[i] = c[i + 1:i + 64].min()
    d["maxdd63"] = fwdmin63 / c - 1
    d["T1"] = np.where(np.isnan(fwdmin63), np.nan, (fwdmin63 > 0.90 * c).astype(float))
    c252 = close.shift(-252)
    d["T2"] = np.where(c252.isna() | d["T1"].isna(), np.nan,
                       ((c252.to_numpy() > c) & (d["T1"] == 1)).astype(float))
    for h in (21, 63, 252):
        d[f"fwd{h}"] = close.shift(-h) / close - 1
    d["date"] = idx
    d.index.name = None
    return d, E, V


def event_rows(asset: str, d: pd.DataFrame, E: pd.DataFrame, V: pd.DataFrame, thr: float) -> pd.DataFrame:
    A = epi.first_shocks(d["close"], thr)
    A = epi.assign_shock_episodes(A, E)
    rows = pd.concat([V[["i", "type", "ep"]], A[["i", "type", "ep"]]], ignore_index=True)
    out = d.iloc[rows["i"].to_numpy()].copy()
    out["type"] = rows["type"].to_numpy()
    out["ep"] = rows["ep"].to_numpy()
    out["shock_ret"] = np.nan
    out.loc[out["type"] == "A", "shock_ret"] = d["close"].pct_change().iloc[out.loc[out["type"] == "A", "i"]].to_numpy()
    out = out[out.index >= pd.Timestamp(EVENT_START[asset])]
    out = out[out.index <= HOLD_END]
    out["sample"] = np.where(out.index <= TRAIN_END, "train", "holdout")
    out["asset"] = asset
    return out.sort_values(["date", "type"])


def signal_dates(d: pd.DataFrame, E: pd.DataFrame, kind: str) -> pd.DataFrame:
    """First qualifying session per episode (after B10, before reset). kind: H2a, H2b, H2b095."""
    sig = np.zeros(len(d), bool)
    if kind == "H2a":
        sig = (d["rvol20"] <= 0.80 * d["rvol_max_prior20"]).to_numpy()
    else:
        thr = 1.00 if kind == "H2b" else 0.95
        vr = d["vratio"].to_numpy()
        run = 0
        for i in range(len(vr)):
            if np.isnan(vr[i]):
                run = 0
                continue
            if vr[i] > thr:
                run += 1
            else:
                if run >= 3:
                    sig[i] = True
                run = 0
    out = []
    for _, e in E.iterrows():
        lo = int(e["b10_i"]) + 1
        hi = int(e["reset_i"]) if e["reset_i"] == e["reset_i"] else len(d)
        w = np.where(sig[lo:hi])[0]
        if len(w):
            out.append(dict(i=lo + w[0], ep=int(e["ep"]), type=kind))
    return pd.DataFrame(out, columns=["i", "ep", "type"])
