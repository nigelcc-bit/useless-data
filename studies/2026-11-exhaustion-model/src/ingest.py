"""Clean raw files into data/processed/. Closes only. No outcome statistics here.

Outputs
- closes.parquet : SPX, NDX, SOX closes (each on its own trading calendar, NaN elsewhere),
                   VIX and VIX3M closes on the SPX calendar.
- monthly.parquet: FEDFUNDS, BAA, GS10, BAA_GS10, KR_EXPORTS_USD_SA (month-start index, unlagged).
- baa10y.parquet : daily FRED BAA10Y.
Point-in-time lagging of monthly series is done in features.py (value for month m usable
from the first trading day of month m+2, for every monthly series).
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"

SPX_START = "1950-01-03"
VIX3M_START = "2007-12-04"   # official Cboe VIX3M history start (prompt section 2)


def _close(name: str) -> pd.Series:
    d = pd.read_csv(RAW / name, parse_dates=["date"])
    s = d.set_index("date")["close"].astype(float)
    return s[~s.index.duplicated(keep="last")].sort_index()


def _fred(name: str) -> pd.Series:
    d = pd.read_csv(RAW / name, parse_dates=["date"], na_values=["."])
    return d.set_index("date")["value"].astype(float).dropna().sort_index()


def load_closes() -> pd.DataFrame:
    spx = _close("spx_1950_2026.csv").loc[SPX_START:].dropna()
    ndx = _close("ndx_1985_2026.csv").dropna()
    sox = _close("sox_daily_1994_2026.csv").dropna()
    cal = spx.index
    vix = _close("vix_daily_1990_2026.csv").dropna()
    vix = vix[vix.index.isin(cal)]            # drop holiday-dated rows not on the SPX calendar
    v3 = _close("vix3m_daily_2007_2026.csv").loc[VIX3M_START:].dropna()
    v3 = v3[v3.index.isin(cal)]
    df = pd.concat({"SPX": spx, "NDX": ndx, "SOX": sox, "VIX": vix, "VIX3M": v3}, axis=1, sort=True)
    return df.sort_index()


def load_monthly() -> pd.DataFrame:
    m = pd.concat({
        "FEDFUNDS": _fred("fred_FEDFUNDS.csv"),
        "BAA": _fred("fred_BAA.csv"),
        "GS10": _fred("fred_GS10.csv"),
        "KR_EXPORTS_USD_SA": _fred("fred_XTEXVA01KRM667S.csv"),
    }, axis=1, sort=True)
    m["BAA_GS10"] = m["BAA"] - m["GS10"]
    return m.loc["1950-01-01":]


def main() -> None:
    PROC.mkdir(parents=True, exist_ok=True)
    load_closes().to_parquet(PROC / "closes.parquet")
    load_monthly().to_parquet(PROC / "monthly.parquet")
    _fred("fred_BAA10Y.csv").to_frame("BAA10Y").to_parquet(PROC / "baa10y.parquet")
    print("processed written")


if __name__ == "__main__":
    main()
