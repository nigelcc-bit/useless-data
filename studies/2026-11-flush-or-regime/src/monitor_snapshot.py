"""Ingest closes through the latest US close into a dated monitor snapshot.

Does NOT overwrite study-processed panels (pinned to STUDY_ASOF=2026-11-05).
"""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd

from core.config_io import ROOT
from src.run_p1 import all_symbols, build_price_frames
from core.ingest.yahoo import fetch_yahoo_ohlcv
from src.study_pin import (
    MONITOR_SNAPSHOTS,
    STUDY_ASOF,
    assert_study_pinned_to_asof,
    write_pin_meta,
)


def ingest_monitor_snapshot(
    *,
    end: str | None = None,
    start_from_pin: str | None = None,
) -> Path:
    """Fetch Yahoo OHLCV through `end` (inclusive) and write a dated snapshot.

    Extends the study-pinned adj_close/close/high by re-fetching from
    `start_from_pin` (default STUDY_ASOF - a few days for continuity) through
    the latest available US close.
    """
    assert_study_pinned_to_asof(STUDY_ASOF)
    write_pin_meta()

    end_ts = pd.Timestamp(end) if end else pd.Timestamp(datetime.now(tz=timezone.utc).date())
    # Pull a short overlap from the pin so joins are clean
    start = pd.Timestamp(start_from_pin or (STUDY_ASOF - pd.Timedelta(days=14)))

    today = date.today().isoformat()
    raw_dir = ROOT / "data" / "raw" / f"monitor_{today}"
    raw_dir.mkdir(parents=True, exist_ok=True)

    symbols = all_symbols()
    ohlcv: dict[str, pd.DataFrame] = {}
    for sym in symbols:
        try:
            df = fetch_yahoo_ohlcv(
                sym,
                start.strftime("%Y-%m-%d"),
                end_ts.strftime("%Y-%m-%d"),
                raw_dir,
                use_cache=False,
            )
            if len(df):
                ohlcv[sym] = df
                print(f"  {sym}: {df.index.min().date()} → {df.index.max().date()} ({len(df)})")
            else:
                print(f"  {sym}: EMPTY")
        except Exception as e:  # noqa: BLE001
            print(f"  {sym}: FAIL {e}")

    close_new, high_new, adj_new = build_price_frames(ohlcv)

    # Merge onto study pin (study wins for dates ≤ STUDY_ASOF)
    close_pin = pd.read_parquet(ROOT / "data" / "processed" / "prices.parquet")
    high_pin = pd.read_parquet(ROOT / "data" / "processed" / "highs.parquet")
    adj_pin = pd.read_parquet(ROOT / "data" / "processed" / "adj_close.parquet")
    for df in (close_pin, high_pin, adj_pin, close_new, high_new, adj_new):
        df.index = pd.to_datetime(df.index).normalize()

    def _extend(pin: pd.DataFrame, new: pd.DataFrame) -> pd.DataFrame:
        # Keep pin through STUDY_ASOF; append strictly later dates from new
        pin_cut = pin.loc[:STUDY_ASOF]
        add = new.loc[new.index > STUDY_ASOF]
        # Align columns
        cols = sorted(set(pin_cut.columns) | set(add.columns))
        out = pd.concat([pin_cut.reindex(columns=cols), add.reindex(columns=cols)])
        return out[~out.index.duplicated(keep="last")].sort_index()

    close = _extend(close_pin, close_new)
    high = _extend(high_pin, high_new)
    adj = _extend(adj_pin, adj_new)

    snap_asof = pd.Timestamp(adj.dropna(how="all").index.max()).normalize()
    snap_dir = MONITOR_SNAPSHOTS / snap_asof.strftime("%Y-%m-%d")
    snap_dir.mkdir(parents=True, exist_ok=True)
    close.to_parquet(snap_dir / "prices.parquet")
    high.to_parquet(snap_dir / "highs.parquet")
    adj.to_parquet(snap_dir / "adj_close.parquet")
    meta = {
        "snapshot_asof": str(snap_asof.date()),
        "study_asof_pin": str(STUDY_ASOF.date()),
        "n_symbols": len(adj.columns),
        "n_rows": int(len(adj)),
        "raw_dir": str(raw_dir.relative_to(ROOT)),
        "label": "MONITOR_SNAPSHOT — does not mutate study results",
        "pulled_at_utc": datetime.now(tz=timezone.utc).isoformat(),
    }
    (snap_dir / "meta.json").write_text(json.dumps(meta, indent=2))
    # Pointer to latest
    (MONITOR_SNAPSHOTS / "LATEST").write_text(str(snap_asof.date()) + "\n")
    print(json.dumps(meta, indent=2))
    # Re-assert study pin untouched
    assert_study_pinned_to_asof(STUDY_ASOF)
    return snap_dir


def latest_snapshot_dir() -> Path | None:
    latest = MONITOR_SNAPSHOTS / "LATEST"
    if latest.exists():
        d = MONITOR_SNAPSHOTS / latest.read_text().strip()
        if d.is_dir():
            return d
    if not MONITOR_SNAPSHOTS.exists():
        return None
    dated = sorted(p for p in MONITOR_SNAPSHOTS.iterdir() if p.is_dir())
    return dated[-1] if dated else None


def main() -> None:
    ingest_monitor_snapshot()


if __name__ == "__main__":
    main()
