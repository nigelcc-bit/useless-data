"""Data loading.

Primary NDX/SPX loads require Study 1 validated splices in data/clean/:
  ndx_1985_2026.csv, spx_1950_2026.csv

Yahoo downloads go through core.ingest.yahoo (disk-cached under data/raw/).
Missing clean files for a primary NDX/SPX load raise FileNotFoundError —
there is no silent Yahoo fallback for those series.

Closing prices only (price index, no dividends), matching Study 1.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from core.ingest.yahoo import fetch_yahoo_ohlcv

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "data" / "clean"
RAW = ROOT / "data" / "raw"

STUDY1_FILES = {"NDX": "ndx_1985_2026.csv", "SPX": "spx_1950_2026.csv"}
STUDY1_TICKERS = {"NDX": "^NDX", "SPX": "^GSPC"}

# Study D universe. Start dates are what Yahoo carries; the loader
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
    close_col = next(
        (c for c in df.columns if c.lower() in ("close", "price", "adj close", "close_price")),
        None,
    )
    if close_col is None:
        raise ValueError(f"No close column in {path}: {list(df.columns)}")
    s = df[[date_col, close_col]].copy()
    s[date_col] = pd.to_datetime(s[date_col])
    if s[close_col].dtype == object:
        s[close_col] = s[close_col].astype(str).str.replace(",", "").astype(float)
    s = s.dropna().drop_duplicates(date_col).sort_values(date_col).set_index(date_col)[close_col]
    s.name = path.stem
    return s.astype(float)


def fetch_yahoo(ticker: str, refresh: bool = False, start: str = "1950-01-01") -> pd.Series:
    """Download (or load cache) via core.ingest.yahoo; return a Close series."""
    RAW.mkdir(parents=True, exist_ok=True)
    end = (pd.Timestamp.today() + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    df = fetch_yahoo_ohlcv(ticker, start, end, RAW, use_cache=not refresh)
    if df.empty or "Close" not in df.columns:
        raise RuntimeError(f"Yahoo returned no Close data for {ticker}")
    s = df["Close"].dropna().astype(float)
    s.index = pd.DatetimeIndex(s.index).tz_localize(None).normalize()
    s = s[~s.index.duplicated(keep="last")].sort_index()
    s.name = ticker
    return s


def load_index(name: str, refresh: bool = False, *, require_clean: bool = True) -> pd.Series:
    """NDX or SPX from Study 1 clean files. Fails loudly if clean file is missing.

    When the clean file exists, newer bars may be appended from Yahoo (explicit
    extension, not a substitute for the validated splice).
    """
    if name not in STUDY1_FILES:
        raise KeyError(f"load_index primary names are {list(STUDY1_FILES)}; got {name!r}")
    f = CLEAN / STUDY1_FILES[name]
    if not f.exists():
        raise FileNotFoundError(
            f"Missing Study 1 clean file: {f}. "
            f"Copy {STUDY1_FILES[name]} into data/clean/ before a primary run. "
            f"Yahoo is not a silent fallback for NDX/SPX."
        )
    del require_clean  # API retained; missing clean always raises (no silent fallback)
    s = _read_close_csv(f)
    src = f"clean:{f.name}"
    try:
        y = drop_incomplete_last_bar(fetch_yahoo(STUDY1_TICKERS[name], refresh))
        new = y[y.index > s.index[-1]]
        overlap = y.reindex(s.index[-20:]).dropna()
        if len(overlap):
            gap = float((overlap / s.reindex(overlap.index) - 1).abs().max())
            if gap > 0.002:
                print(
                    f"[data] WARNING {name}: Yahoo vs clean differ by {gap:.3%} "
                    f"on overlap; not extending"
                )
                new = new.iloc[0:0]
        if len(new):
            s = pd.concat([s, new])
            src += f"+yahoo({len(new)} bars to {new.index[-1].date()})"
    except Exception as e:  # noqa: BLE001
        print(f"[data] {name}: could not extend with Yahoo ({e}); using clean file only")
    s.attrs["source"] = src
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
                # FileNotFoundError must propagate — no silent skip/fallback for NDX/SPX
                s = load_index(name, refresh)
            else:
                s = fetch_yahoo(tk, refresh)
            s = drop_incomplete_last_bar(s)
            s = s[s > 0]
        except FileNotFoundError:
            raise
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
