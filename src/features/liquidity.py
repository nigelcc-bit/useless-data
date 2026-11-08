"""Liquidity controls (H3): log market cap, ADV.

ADV = trailing 21d mean dollar volume on each name's native calendar.
log_mkt_cap from EDGAR shares outstanding × close (filing-lagged shares).
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
    """Trailing mean of close×volume on each name's native calendar (no ffill)."""
    common = list(close.columns.intersection(volume.columns))
    if not common:
        return pd.DataFrame(index=close.index)
    out = {}
    for t in common:
        c = close[t].dropna()
        v = volume[t].reindex(c.index)
        # drop days with missing volume rather than ffill across calendars
        ok = c.notna() & v.notna()
        c, v = c[ok], v[ok]
        if len(c) < window:
            out[t] = pd.Series(dtype="float64")
            continue
        dollar = c * v
        out[t] = dollar.rolling(window, min_periods=window).mean()
    return pd.DataFrame(out).reindex(close.index)


def log_mkt_cap_from_shares(
    close: pd.Series,
    shares: float | None,
) -> float:
    if shares is None or not np.isfinite(shares) or shares <= 0:
        return float("nan")
    if close is None or not np.isfinite(close) or close <= 0:
        return float("nan")
    return float(np.log(close * shares))


def log_mkt_cap_placeholder(tickers: list[str]) -> pd.Series:
    return pd.Series(index=tickers, dtype="float64", name="log_mkt_cap")
