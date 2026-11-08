"""Liquidity controls (H3 regressor 9): log market cap, ADV.

ADV = trailing 21d mean dollar volume (close × volume), using prices/volume ≤ t.
log_mkt_cap requires shares outstanding — not ingested yet → NaN (coverage gap).
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


def load_volume_panel(raw_dir: Path, tickers: list[str]) -> pd.DataFrame:
    """Wide volume panel from Yahoo chart cache (equity tickers only)."""
    cols = {}
    for t in tickers:
        path = raw_dir / f"yahoo_{t}.json"
        if not path.exists():
            continue
        try:
            payload = json.loads(path.read_text())
        except json.JSONDecodeError:
            continue
        result = (payload.get("chart") or {}).get("result") or []
        if not result:
            continue
        block = result[0]
        ts = block.get("timestamp") or []
        quote = ((block.get("indicators") or {}).get("quote") or [{}])[0]
        vol = quote.get("volume") or []
        if not ts or not vol:
            continue
        idx = pd.to_datetime(pd.Series(ts), unit="s", utc=True).dt.tz_convert(None).dt.normalize()
        s = pd.Series(vol, index=idx, dtype="float64")
        s = s[~s.index.duplicated(keep="last")].sort_index()
        cols[t] = s
    if not cols:
        return pd.DataFrame()
    return pd.DataFrame(cols).sort_index()


def adv_dollar(
    close: pd.DataFrame,
    volume: pd.DataFrame,
    window: int = 21,
) -> pd.DataFrame:
    """Trailing mean of close×volume over `window` sessions (no look-ahead)."""
    common = close.columns.intersection(volume.columns)
    if len(common) == 0:
        return pd.DataFrame(index=close.index)
    # Causal ffill on both legs so a single missing bar does not zero the window
    c = close[common].ffill()
    v = volume[common].reindex(close.index).ffill()
    dollar = c * v
    return dollar.rolling(window, min_periods=window).mean()


def log_mkt_cap_placeholder(tickers: list[str]) -> pd.Series:
    """Shares outstanding not loaded — explicit NaN column for coverage."""
    return pd.Series(index=tickers, dtype="float64", name="log_mkt_cap")
