"""yfinance / Yahoo chart download with disk cache."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pandas as pd
import requests

YAHOO_CHART = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; ai-selloff-study/0.1; research)",
    "Accept": "application/json",
}


def _cache_path(raw_dir: Path, symbol: str) -> Path:
    safe = symbol.replace("^", "_").replace("/", "_")
    return raw_dir / f"yahoo_{safe}.json"


def fetch_yahoo_ohlcv(
    symbol: str,
    start: str,
    end: str,
    raw_dir: Path,
    *,
    session: requests.Session | None = None,
    sleep_s: float = 0.35,
    use_cache: bool = True,
) -> pd.DataFrame:
    """Daily OHLCV from Yahoo chart API. end is exclusive in Yahoo period2 semantics
    when using timestamps; we request through end date inclusive via period2=end+1d.
    """
    raw_dir.mkdir(parents=True, exist_ok=True)
    cache = _cache_path(raw_dir, symbol)
    if use_cache and cache.exists():
        payload = json.loads(cache.read_text())
    else:
        start_ts = int(pd.Timestamp(start, tz="UTC").timestamp())
        # inclusive end: add one day
        end_ts = int((pd.Timestamp(end, tz="UTC") + pd.Timedelta(days=1)).timestamp())
        params = {
            "period1": start_ts,
            "period2": end_ts,
            "interval": "1d",
            "events": "div,splits",
            "includePrePost": "false",
        }
        sess = session or requests.Session()
        url = YAHOO_CHART.format(symbol=symbol)
        last_err: Exception | None = None
        for attempt in range(5):
            try:
                r = sess.get(url, params=params, headers=HEADERS, timeout=60)
                if r.status_code == 429:
                    time.sleep(2 ** attempt)
                    continue
                r.raise_for_status()
                payload = r.json()
                cache.write_text(json.dumps(payload))
                time.sleep(sleep_s)
                break
            except Exception as e:  # noqa: BLE001 — retry then raise
                last_err = e
                time.sleep(2 ** attempt)
        else:
            raise RuntimeError(f"Yahoo fetch failed for {symbol}: {last_err}")

    result = (payload.get("chart") or {}).get("result")
    if not result:
        err = (payload.get("chart") or {}).get("error")
        # Soft-fail: empty frame so the rest of the universe still builds
        print(f"  WARN Yahoo empty for {symbol}: {err}", flush=True)
        return pd.DataFrame(
            columns=["Open", "High", "Low", "Close", "Adj Close", "Volume"]
        )
    block = result[0]
    ts = block.get("timestamp") or []
    quote = (block.get("indicators") or {}).get("quote") or [{}]
    q0 = quote[0]
    adj = (block.get("indicators") or {}).get("adjclose") or [{}]
    adj0 = adj[0] if adj else {}
    df = pd.DataFrame(
        {
            "Open": q0.get("open"),
            "High": q0.get("high"),
            "Low": q0.get("low"),
            "Close": q0.get("close"),
            "Adj Close": adj0.get("adjclose") or q0.get("close"),
            "Volume": q0.get("volume"),
        },
        index=pd.to_datetime(ts, unit="s", utc=True).tz_convert(None).normalize(),
    )
    df.index.name = "Date"
    # Drop rows with all-OHLC null
    df = df.dropna(how="all", subset=["Open", "High", "Low", "Close"])
    return df.sort_index()


def fetch_many(
    symbols: list[str],
    start: str,
    end: str,
    raw_dir: Path,
) -> dict[str, pd.DataFrame]:
    sess = requests.Session()
    out: dict[str, pd.DataFrame] = {}
    for i, sym in enumerate(symbols):
        print(f"[{i+1}/{len(symbols)}] Yahoo {sym}", flush=True)
        out[sym] = fetch_yahoo_ohlcv(sym, start, end, raw_dir, session=sess)
    return out
