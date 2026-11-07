"""FRED series download (CSV graph endpoint — no API key required)."""

from __future__ import annotations

from io import StringIO
from pathlib import Path

import pandas as pd
import requests

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; ai-selloff-study/0.1; research)"}
SERIES = ("BAMLH0A0HYM2", "DGS10", "FEDFUNDS", "VIXCLS")


def fetch_fred_series(series_id: str, raw_dir: Path) -> pd.Series:
    raw_dir.mkdir(parents=True, exist_ok=True)
    cache = raw_dir / f"fred_{series_id}.csv"
    if cache.exists() and cache.stat().st_size > 50:
        text = cache.read_text()
    else:
        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
        r = requests.get(url, headers=HEADERS, timeout=60)
        r.raise_for_status()
        text = r.text
        cache.write_text(text)
    df = pd.read_csv(StringIO(text))
    # columns: observation_date, SERIES
    date_col = df.columns[0]
    val_col = df.columns[1]
    s = df.set_index(pd.to_datetime(df[date_col]))[val_col]
    s = pd.to_numeric(s, errors="coerce")
    s.name = series_id
    return s.sort_index()


def fetch_all_fred(raw_dir: Path) -> pd.DataFrame:
    cols = {sid: fetch_fred_series(sid, raw_dir) for sid in SERIES}
    return pd.DataFrame(cols)
