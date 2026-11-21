"""Fetch raw inputs from public sources (Yahoo chart API, FRED fredgraph CSV).

The files named in the study prompt (section 2) were not attached to the
session, so every raw file here is rebuilt from a public source. Each file is
written once to data/raw/ exactly as parsed, and a provenance row is appended
to data/raw/MANIFEST.csv (source URL, pull timestamp UTC, rows, first/last date,
sha256). Raw files are never edited afterwards.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
UA = {"User-Agent": "Mozilla/5.0 (research script)"}

YAHOO = {
    "spx_1950_2026.csv": "^GSPC",
    "ndx_1985_2026.csv": "^NDX",
    "sox_daily_1994_2026.csv": "^SOX",
    "vix_daily_1990_2026.csv": "^VIX",
    "vix3m_daily_2007_2026.csv": "^VIX3M",
}
FRED = {
    "fred_FEDFUNDS.csv": "FEDFUNDS",
    "fred_BAA.csv": "BAA",
    "fred_GS10.csv": "GS10",
    "fred_BAA10Y.csv": "BAA10Y",
    "fred_VIXCLS.csv": "VIXCLS",
    "fred_VXVCLS.csv": "VXVCLS",
    "fred_NASDAQ100.csv": "NASDAQ100",
    "fred_SP500.csv": "SP500",
    "fred_XTEXVA01KRM667S.csv": "XTEXVA01KRM667S",  # Korea exports, value, USD, SA (OECD MEI)
}


def _get(url: str, tries: int = 5, headers: dict | None = None) -> requests.Response:
    for k in range(tries):
        try:
            r = requests.get(url, headers=headers or {}, timeout=60)
            if r.status_code == 200:
                return r
        except requests.RequestException:
            pass
        time.sleep(2 ** (k + 1))
    raise RuntimeError(f"fetch failed after {tries} tries: {url}")


def yahoo(symbol: str) -> tuple[pd.DataFrame, str]:
    p2 = int(time.time()) + 86400
    url = (f"https://query2.finance.yahoo.com/v8/finance/chart/{requests.utils.quote(symbol)}"
           f"?period1=-1325635200&period2={p2}&interval=1d&events=history")
    j = _get(url, headers=UA).json()  # Yahoo needs a browser UA; FRED rejects it["chart"]["result"][0]
    q = j["indicators"]["quote"][0]
    tz = j["meta"]["exchangeTimezoneName"]
    idx = pd.to_datetime(j["timestamp"], unit="s", utc=True).tz_convert(tz).normalize().tz_localize(None)
    df = pd.DataFrame({"date": idx.date, "open": q["open"], "high": q["high"],
                       "low": q["low"], "close": q["close"]})
    return df, url


def fred(series: str) -> tuple[pd.DataFrame, str]:
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}"
    df = pd.read_csv(io.StringIO(_get(url).text))
    df.columns = ["date", "value"]
    return df, url


def write(name: str, df: pd.DataFrame, url: str) -> None:
    path = RAW / name
    df.to_csv(path, index=False)
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    man = RAW / "MANIFEST.csv"
    new = not man.exists()
    with man.open("a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["file", "source_url", "pulled_utc", "rows", "first", "last", "sha256"])
        w.writerow([name, url, datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    len(df), df["date"].iloc[0], df["date"].iloc[-1], sha])
    print(name, len(df), df["date"].iloc[0], df["date"].iloc[-1])


def main(which: list[str]) -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    if "yahoo" in which:
        for name, sym in YAHOO.items():
            df, url = yahoo(sym)
            write(name, df, url)
            time.sleep(2)
    if "fred" in which:
        for name, s in FRED.items():
            df, url = fred(s)
            write(name, df, url)
            time.sleep(1)


if __name__ == "__main__":
    main(sys.argv[1:] or ["yahoo", "fred"])
