"""Stooq daily closes for index cross-check."""

from __future__ import annotations

import time
from io import StringIO
from pathlib import Path

import pandas as pd
import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; ai-selloff-study/0.1; research)",
}

# Stooq tickers for our indices / ETFs
STOOQ_MAP = {
    "SPY": "spy.us",
    "QQQ": "qqq.us",
    "SOXX": "soxx.us",
    "SMH": "smh.us",
    "^GSPC": "^spx",
    "^IXIC": "^ndq",
    "^SOX": "^sox",  # may be unavailable
    "^VIX": "^vix",
}


def fetch_stooq(
    yahoo_symbol: str,
    raw_dir: Path,
    *,
    session: requests.Session | None = None,
    timeout: int = 12,
) -> pd.DataFrame | None:
    stooq_sym = STOOQ_MAP.get(yahoo_symbol)
    if not stooq_sym:
        return None
    raw_dir.mkdir(parents=True, exist_ok=True)
    safe = yahoo_symbol.replace("^", "_")
    cache = raw_dir / f"stooq_{safe}.csv"
    if cache.exists() and cache.stat().st_size > 100:
        text = cache.read_text()
    else:
        url = f"https://stooq.com/q/d/l/?s={stooq_sym}&i=d"
        sess = session or requests.Session()
        last_err = None
        text = None
        for attempt in range(2):
            try:
                r = sess.get(url, headers=HEADERS, timeout=timeout)
                if r.status_code != 200 or "<html" in r.text[:200].lower():
                    last_err = RuntimeError(f"status={r.status_code} body={r.text[:80]}")
                    time.sleep(1)
                    continue
                text = r.text
                cache.write_text(text)
                break
            except Exception as e:  # noqa: BLE001
                last_err = e
                time.sleep(1)
        if text is None:
            print(f"  Stooq skip {yahoo_symbol}: {last_err}")
            return None
    df = pd.read_csv(StringIO(text))
    if "Date" not in df.columns:
        return None
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.set_index("Date").sort_index()
    return df
