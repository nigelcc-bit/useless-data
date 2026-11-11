"""Trading-calendar hygiene for H3 price panels.

Source of bad rows (2026-05-25 Memorial Day, 2026-09-07 Labor Day):
Yahoo ^VIX prints on some US equity holidays. ``build_price_frames`` outer-joins
all symbols, so those dates entered ``prices.parquet`` with NaN equity closes.
Fix: drop VIX-only sessions rather than forward-fill.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.config_io import ROOT
from src.ingest.run_p1 import drop_vix_only_sessions

US_EQUITY_HOLIDAY_PLACEHOLDERS = (
    pd.Timestamp("2026-05-25"),
    pd.Timestamp("2026-09-07"),
)


def scrub_processed_price_frames(
    processed: Path | None = None,
) -> dict:
    """Drop VIX-only / US-holiday placeholder rows from processed price frames."""
    processed = processed or (ROOT / "data" / "processed")
    close = pd.read_parquet(processed / "prices.parquet")
    high = pd.read_parquet(processed / "highs.parquet")
    adj = pd.read_parquet(processed / "adj_close.parquet")
    for df in (close, high, adj):
        df.index = pd.to_datetime(df.index).tz_localize(None).normalize()

    before = len(close)
    present_before = {
        d.strftime("%Y-%m-%d"): bool(d in close.index) for d in US_EQUITY_HOLIDAY_PLACEHOLDERS
    }
    close, high, adj = drop_vix_only_sessions(close, high, adj)
    close.to_parquet(processed / "prices.parquet")
    high.to_parquet(processed / "highs.parquet")
    adj.to_parquet(processed / "adj_close.parquet")
    present_after = {
        d.strftime("%Y-%m-%d"): bool(d in close.index) for d in US_EQUITY_HOLIDAY_PLACEHOLDERS
    }
    return {
        "rows_before": before,
        "rows_after": len(close),
        "dropped": before - len(close),
        "holiday_present_before": present_before,
        "holiday_present_after": present_after,
        "source": "Yahoo ^VIX on US equity holidays → outer-join in build_price_frames",
    }
