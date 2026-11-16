"""Download raw daily OHLCV for current S&P 500 constituents plus SPY.

Scope (see PREREG.md / CLAUDE.md): data download and quality control only.
This script computes no analysis returns, signals or statistics. The only
price-derived quantity is the QC flag for |Adj Close day-over-day change| > 40%,
and it is computed on the development sample only (<= 2025-12-31), so the
2026 holdout is stored on disk but not summarised beyond structural counts
(rows, last date, duplicates, gaps, missing cells).

Usage (from the repository root):
    python3 studies/11-2026-bandwidth-false-discovery/src/get_data.py
"""

from __future__ import annotations

import datetime as dt
import io
import time
from pathlib import Path

import pandas as pd
import requests
import yfinance as yf

STUDY_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = STUDY_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
OUT_DIR = STUDY_DIR / "out"

WIKI_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
START = "2000-01-01"
DEV_END = pd.Timestamp("2025-12-31")  # last day of the development sample
EXTRA_TICKERS = ["SPY"]
BATCH_SIZE = 50
PRICE_COLS = ["Open", "High", "Low", "Close", "Adj Close", "Volume"]

GAP_DAYS = 5          # flag gaps longer than this many calendar days
JUMP_THRESHOLD = 0.40  # flag |Adj Close change| above this (QC only)
LATE_START_AFTER = pd.Timestamp("2000-01-03")  # first NYSE session of 2000


def get_constituents(today: dt.date) -> pd.DataFrame:
    """Read the current S&P 500 table from Wikipedia and save it with today's date."""
    headers = {"User-Agent": "Mozilla/5.0 (research data download)"}
    resp = requests.get(WIKI_URL, headers=headers, timeout=30)
    resp.raise_for_status()
    tables = pd.read_html(io.StringIO(resp.text), attrs={"id": "constituents"})
    df = tables[0].copy()
    df["Symbol"] = df["Symbol"].astype(str).str.strip()
    df["yf_ticker"] = df["Symbol"].str.replace(".", "-", regex=False)
    df.insert(0, "list_date", today.isoformat())
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / f"constituents_{today.isoformat()}.csv"
    df.to_csv(path, index=False)
    print(f"Saved {len(df)} constituents to {path.relative_to(STUDY_DIR)}")
    return df


def _split_download(raw: pd.DataFrame, tickers: list[str]) -> dict[str, pd.DataFrame]:
    """Split a multi-ticker yfinance frame into one clean frame per ticker."""
    frames: dict[str, pd.DataFrame] = {}
    if raw is None or raw.empty:
        return frames
    top = raw.columns.get_level_values(0)
    for t in tickers:
        if t not in top:
            continue
        df = raw[t].copy()
        df = df[[c for c in PRICE_COLS if c in df.columns]]
        # Batch downloads align all tickers on the union of dates; rows that are
        # entirely empty for this ticker are not observations for it.
        df = df.dropna(how="all")
        if df.empty or df["Close"].isna().all():
            continue
        df.index = pd.to_datetime(df.index)
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)
        df.index.name = "Date"
        df.columns.name = None
        frames[t] = df.sort_index()
    return frames


def download_batch(tickers: list[str], end: str) -> dict[str, pd.DataFrame]:
    raw = yf.download(
        tickers,
        start=START,
        end=end,
        interval="1d",
        auto_adjust=False,
        actions=False,
        group_by="ticker",
        threads=True,
        progress=False,
    )
    if not isinstance(raw.columns, pd.MultiIndex):  # single-ticker shape
        raw = pd.concat({tickers[0]: raw}, axis=1)
    return _split_download(raw, tickers)


def download_all(tickers: list[str], end: str) -> tuple[dict[str, pd.DataFrame], list[str]]:
    got: dict[str, pd.DataFrame] = {}
    for i in range(0, len(tickers), BATCH_SIZE):
        batch = tickers[i : i + BATCH_SIZE]
        got.update(download_batch(batch, end))
        print(f"  batch {i // BATCH_SIZE + 1}: {len(got)}/{min(i + BATCH_SIZE, len(tickers))} ok")
        time.sleep(1)
    failed = [t for t in tickers if t not in got]
    if failed:
        print(f"Retrying {len(failed)} failed tickers once: {failed}")
        time.sleep(5)
        for i in range(0, len(failed), BATCH_SIZE):
            got.update(download_batch(failed[i : i + BATCH_SIZE], end))
    failed = [t for t in tickers if t not in got]
    return got, failed


def qc_ticker(t: str, df: pd.DataFrame) -> dict:
    idx = df.index
    dev = df[idx <= DEV_END]
    gaps = pd.Series(idx[1:] - idx[:-1], index=idx[1:]).dt.days if len(idx) > 1 else pd.Series(dtype=float)
    long_gaps = gaps[gaps > GAP_DAYS]
    # QC-only flag, development sample only. Not used for analysis.
    adj = dev["Adj Close"]
    chg = adj / adj.shift(1) - 1
    jumps = chg[chg.abs() > JUMP_THRESHOLD]
    return {
        "ticker": t,
        "rows": len(df),
        "rows_dev": len(dev),
        "rows_holdout": len(df) - len(dev),
        "first_date": idx.min().date().isoformat(),
        "last_date": idx.max().date().isoformat(),
        "dup_dates": int(idx.duplicated().sum()),
        "gaps_gt5d": int(len(long_gaps)),
        "max_gap_days": int(gaps.max()) if len(gaps) else 0,
        "jumps_gt40pct_dev": int(len(jumps)),
        "jump_dates_dev": ";".join(d.date().isoformat() for d in jumps.index[:5]),
        "missing_cells": int(df[PRICE_COLS].isna().sum().sum()),
    }


def write_qc(qc: pd.DataFrame, failed: list[str], n_requested: int, today: dt.date) -> Path:
    late = qc[pd.to_datetime(qc["first_date"]) > LATE_START_AFTER]
    lines = [
        "# Data QC: raw daily OHLCV",
        "",
        f"Generated {today.isoformat()} by `src/get_data.py`. Source: yfinance, `auto_adjust=False` "
        f"(Close and Adj Close both kept), start {START}.",
        "",
        "The 2026 holdout rows are stored on disk but only counted here (rows_holdout, last_date, "
        "duplicates, gaps, missing cells). The >40% Adj Close change flag is computed on the "
        "development sample (<= 2025-12-31) only.",
        "",
        "## Summary",
        "",
        f"- Tickers requested: **{n_requested}** (S&P 500 constituents plus SPY)",
        f"- Tickers downloaded: **{len(qc)}**",
        f"- Tickers failed (after one retry): **{len(failed)}**" + (f": {', '.join(failed)}" if failed else ""),
        f"- Tickers starting after 2000-01-03: **{len(late)}**",
        f"- Tickers with duplicate dates: **{int((qc['dup_dates'] > 0).sum())}**",
        f"- Tickers with a gap > {GAP_DAYS} calendar days: **{int((qc['gaps_gt5d'] > 0).sum())}**",
        f"- Tickers with |Adj Close change| > 40% (dev sample): **{int((qc['jumps_gt40pct_dev'] > 0).sum())}**",
        f"- Tickers with any missing cell: **{int((qc['missing_cells'] > 0).sum())}**",
        f"- Total rows: **{int(qc['rows'].sum()):,}** (dev {int(qc['rows_dev'].sum()):,}, "
        f"holdout {int(qc['rows_holdout'].sum()):,})",
        "",
        "## Tickers starting after 2000",
        "",
        ", ".join(f"{r.ticker} ({r.first_date})" for r in late.sort_values("first_date").itertuples()) or "None",
        "",
        "## Per ticker",
        "",
        qc.to_markdown(index=False) if _has_tabulate() else _md_table(qc),
        "",
    ]
    path = OUT_DIR / "qc.md"
    path.write_text("\n".join(lines))
    return path


def _has_tabulate() -> bool:
    try:
        import tabulate  # noqa: F401
        return True
    except ImportError:
        return False


def _md_table(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    out = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for row in df.itertuples(index=False):
        out.append("| " + " | ".join(str(v) for v in row) + " |")
    return "\n".join(out)


def main() -> None:
    today = dt.date.today()
    end = (today + dt.timedelta(days=1)).isoformat()  # yfinance end is exclusive
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    cons = get_constituents(today)
    tickers = list(dict.fromkeys(cons["yf_ticker"].tolist() + EXTRA_TICKERS))
    print(f"Downloading {len(tickers)} tickers, {START} to {today.isoformat()}")

    frames, failed = download_all(tickers, end)
    for t, df in frames.items():
        df.to_parquet(RAW_DIR / f"{t}.parquet")
    print(f"Wrote {len(frames)} Parquet files to {RAW_DIR.relative_to(STUDY_DIR)}; failed: {failed}")

    qc = pd.DataFrame([qc_ticker(t, frames[t]) for t in tickers if t in frames])
    path = write_qc(qc, failed, len(tickers), today)
    print(f"QC written to {path.relative_to(STUDY_DIR)}")


if __name__ == "__main__":
    main()
