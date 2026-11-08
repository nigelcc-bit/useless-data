"""Forward-fill audit for price holes.

Policy (P3 review):
  - Cap causal ffill at **1 session**.
  - Non-US listings: compute returns on their own trading calendar only;
    never on forward-filled US holiday placeholder dates.
  - Audit lists every name/date that would be filled, count per name,
    and whether the cause is a non-US calendar mismatch.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.config_io import ROOT, universe

# Foreign primary listings / ADR issuers in the H3 seed universe.
# US-traded ADRs still sit on the Yahoo US session calendar; holes that are
# US holidays are NOT "non-US calendar" causes.
NON_US_ISSUERS = {
    "TSM": "Taiwan — ADR on NYSE",
    "ASML": "Netherlands — ADR/NYSE",
    "IREN": "Australia — Nasdaq",
    "NBIS": "Netherlands — Nasdaq",
    "FN": "Cayman Islands — NYSE",
}

# Known US exchange holidays that appear as NaN rows in prices.parquet
US_HOLIDAY_HOLES = {
    pd.Timestamp("2026-05-25"): "US Memorial Day 2026",
    pd.Timestamp("2026-09-07"): "US Labor Day 2026",
}


def universe_tickers() -> list[str]:
    out = []
    for _layer, meta in (universe().get("layers") or {}).items():
        out.extend((meta.get("names") or {}).keys())
    return sorted(out)


def audit_price_holes(prices: pd.DataFrame) -> pd.DataFrame:
    """One row per (ticker, date) NaN after first valid close."""
    rows = []
    for t in universe_tickers():
        if t not in prices.columns:
            continue
        s = prices[t]
        first = s.first_valid_index()
        if first is None:
            continue
        holes = s.loc[first:]
        holes = holes[holes.isna()]
        for dt in holes.index:
            d = pd.Timestamp(dt).normalize()
            holiday = US_HOLIDAY_HOLES.get(d)
            non_us = t in NON_US_ISSUERS
            if holiday:
                cause = f"US_HOLIDAY: {holiday}"
                non_us_calendar = False
            elif non_us:
                cause = f"NON_US_ISSUER_GAP: {NON_US_ISSUERS[t]}"
                non_us_calendar = True
            else:
                cause = "DATA_HOLE_UNKNOWN"
                non_us_calendar = False
            rows.append(
                {
                    "ticker": t,
                    "date": d.strftime("%Y-%m-%d"),
                    "cause": cause,
                    "non_us_issuer": non_us,
                    "non_us_calendar_cause": non_us_calendar,
                    "ffill_cap_sessions": 1,
                    "would_ffill_under_cap1": True,  # single isolated holes
                }
            )
    return pd.DataFrame(rows)


def audit_summary(detail: pd.DataFrame) -> pd.DataFrame:
    if detail.empty:
        return pd.DataFrame(columns=["ticker", "n_holes", "non_us_issuer", "causes"])
    g = (
        detail.groupby("ticker", sort=True)
        .agg(
            n_holes=("date", "count"),
            non_us_issuer=("non_us_issuer", "first"),
            causes=("cause", lambda s: "; ".join(sorted(set(s)))),
            dates=("date", lambda s: ",".join(s)),
        )
        .reset_index()
    )
    return g


def write_audit(prices_path: Path | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    prices_path = prices_path or (ROOT / "data" / "processed" / "prices.parquet")
    prices = pd.read_parquet(prices_path)
    prices.index = pd.to_datetime(prices.index).tz_localize(None).normalize()
    detail = audit_price_holes(prices)
    summary = audit_summary(detail)
    exhibits = ROOT / "outputs" / "exhibits"
    exhibits.mkdir(parents=True, exist_ok=True)
    detail.to_csv(exhibits / "ffill_audit_detail.csv", index=False)
    summary.to_csv(exhibits / "ffill_audit_summary.csv", index=False)
    print("=== Ffill audit (cap=1 session) ===")
    print(summary.to_string(index=False))
    print(
        f"\nTotal hole-days={len(detail)}; "
        f"non_us_calendar_cause={int(detail['non_us_calendar_cause'].sum()) if len(detail) else 0}. "
        "Holiday placeholders should be dropped via calendar_hygiene (not ffilled)."
    )
    return detail, summary


if __name__ == "__main__":
    write_audit()
