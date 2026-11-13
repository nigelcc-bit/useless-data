"""Data loading.

Priority for the two Study 1 indices:
  1. data/clean/ndx_1985_2026.csv and data/clean/spx_1950_2026.csv  (the validated Study 1 splices)
  2. Yahoo Finance via yfinance (^NDX, ^GSPC), cached to data/raw/

Everything else (Study D panel) comes from yfinance and is cached. Run
`python -m src.data --refresh` to re-download.

Closing prices only (price index, no dividends), matching Study 1.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "data" / "clean"
RAW = ROOT / "data" / "raw"

STUDY1_FILES = {"NDX": "ndx_1985_2026.csv", "SPX": "spx_1950_2026.csv"}
STUDY1_TICKERS = {"NDX": "^NDX", "SPX": "^GSPC"}

# Study D universe. Start dates are what I believe Yahoo carries; the loader
# reports actual coverage, so treat these as unverified until the first run.
PANEL_PRIMARY = {             # broad equity indices (primary, pre-registered)
    "SPX": "^GSPC", "NDX": "^NDX", "RUT": "^RUT",
    "DAX": "^GDAXI", "CAC": "^FCHI", "FTSE": "^FTSE", "STOXX50": "^STOXX50E",
    "N225": "^N225", "HSI": "^HSI", "KOSPI": "^KS11", "ASX200": "^AXJO",
    "TSX": "^GSPTSE",
}
PANEL_SECONDARY = {           # descriptive only (DJI excluded from primary: near-duplicate of SPX)
    "DJI": "^DJI",
    "XLB": "XLB", "XLE": "XLE", "XLF": "XLF", "XLI": "XLI", "XLK": "XLK",
    "XLP": "XLP", "XLU": "XLU", "XLV": "XLV", "XLY": "XLY",
    "GOLD": "GC=F", "BTC": "BTC-USD",
}


def _read_close_csv(path: Path) -> pd.Series:
    df = pd.read_csv(path)
    date_col = next(c for c in df.columns if "date" in c.lower())
    close_col = next((c for c in df.columns if c.lower() in ("close", "price", "adj close", "close_price")), None)
    if close_col is None:
        raise ValueError(f"No close column in {path}: {list(df.columns)}")
    s = df[[date_col, close_col]].copy()
    s[date_col] = pd.to_datetime(s[date_col])
    if s[close_col].dtype == object:
        s[close_col] = s[close_col].astype(str).str.replace(",", "").astype(float)
    s = s.dropna().drop_duplicates(date_col).sort_values(date_col).set_index(date_col)[close_col]
    s.name = path.stem
    return s.astype(float)


def fetch_yahoo(ticker: str, refresh: bool = False) -> pd.Series:
    RAW.mkdir(parents=True, exist_ok=True)
    cache = RAW / f"{ticker.replace('^', '').replace('=', '_')}.csv"
    if cache.exists() and not refresh:
        return _read_close_csv(cache)
    import yfinance as yf
    h = yf.Ticker(ticker).history(period="max", auto_adjust=False, actions=False)
    if h.empty:
        raise RuntimeError(f"yfinance returned no data for {ticker}")
    h.index = pd.DatetimeIndex(h.index).tz_localize(None).normalize()
    out = h[["Close"]].rename_axis("Date").reset_index()
    out.to_csv(cache, index=False)
    return _read_close_csv(cache)


def load_index(name: str, refresh: bool = False, allow_yahoo: bool = True) -> pd.Series:
    """NDX or SPX: prefer the Study 1 clean file, else yfinance."""
    f = CLEAN / STUDY1_FILES[name]
    if f.exists():
        s = _read_close_csv(f)
        src = f"clean:{f.name}"
        if allow_yahoo:   # append any newer bars (needed to track the live Nov 2026 event)
            try:
                y = drop_incomplete_last_bar(fetch_yahoo(STUDY1_TICKERS[name], refresh))
                new = y[y.index > s.index[-1]]
                overlap = y.reindex(s.index[-20:]).dropna()
                if len(overlap):
                    gap = float((overlap / s.reindex(overlap.index) - 1).abs().max())
                    if gap > 0.002:
                        print(f"[data] WARNING {name}: Yahoo vs clean differ by {gap:.3%} on overlap; not extending")
                        new = new.iloc[0:0]
                if len(new):
                    s = pd.concat([s, new])
                    src += f"+yahoo({len(new)} bars to {new.index[-1].date()})"
            except Exception as e:  # noqa: BLE001
                print(f"[data] {name}: could not extend with Yahoo ({e}); using clean file only")
        s.attrs["source"] = src
        return s
    if not allow_yahoo:
        raise FileNotFoundError(f)
    s = fetch_yahoo(STUDY1_TICKERS[name], refresh)
    s.attrs["source"] = f"yahoo:{STUDY1_TICKERS[name]}"
    return s


def drop_incomplete_last_bar(s: pd.Series, asof: pd.Timestamp | None = None) -> pd.Series:
    """Drop today's bar if the run happens before the close (Yahoo serves partial bars)."""
    asof = asof or pd.Timestamp.now(tz="America/New_York")
    today = asof.tz_localize(None).normalize() if asof.tzinfo else asof.normalize()
    if len(s) and s.index[-1] >= today and asof.hour < 17:
        return s.iloc[:-1]
    return s


def validate(s: pd.Series, name: str) -> dict:
    r = np.log(s).diff().dropna()
    gaps = s.index.to_series().diff().dt.days.dropna()
    stale = (s.diff() == 0).astype(int)
    longest_stale = int(stale.groupby((stale == 0).cumsum()).sum().max()) if len(stale) else 0
    return dict(
        name=name, start=s.index[0].date(), end=s.index[-1].date(), days=len(s),
        max_abs_ret=float(r.abs().max()), n_abs_ret_gt_15pct=int((r.abs() > np.log(1.15)).sum()),
        max_gap_days=int(gaps.max()) if len(gaps) else 0, longest_flat_run=longest_stale,
        duplicates=int(s.index.duplicated().sum()),
    )


def load_panel(universe: dict, refresh=False, min_years=15) -> dict[str, pd.Series]:
    out, report = {}, []
    for name, tk in universe.items():
        try:
            if name in STUDY1_FILES:
                s = load_index(name, refresh)
            else:
                s = fetch_yahoo(tk, refresh)
            s = drop_incomplete_last_bar(s)
            s = s[s > 0]
        except Exception as e:  # noqa: BLE001
            print(f"[data] {name} ({tk}) failed: {e}")
            continue
        v = validate(s, name)
        report.append(v)
        if len(s) < min_years * 252:
            print(f"[data] {name}: only {len(s)} days, excluded (min_years={min_years})")
            continue
        out[name] = s
    rep = pd.DataFrame(report)
    if len(rep):
        print(rep.to_string(index=False))
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true")
    a = ap.parse_args()
    for n in STUDY1_FILES:
        s = load_index(n, a.refresh)
        print(n, s.attrs.get("source"), validate(s, n))
    load_panel({**PANEL_PRIMARY, **PANEL_SECONDARY}, refresh=a.refresh, min_years=0)
