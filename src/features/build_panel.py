"""P3 — Build H3 feature panel and coverage table.

Snapshots features at each episode *start* using prices/volume ≤ start only.
First deliverable: coverage table (names × episodes × block, % non-missing).
Stop after coverage — no H3 regression in this phase.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.config_io import ROOT, episodes, universe
from src.features import (
    BLOCK_COLS,
    adv_dollar,
    ai_revenue_exposure,
    distance_from_high,
    empty_funding,
    empty_valuation,
    layer_assignments,
    load_volume_panel,
    log_mkt_cap_placeholder,
    prior_return,
    realised_vol,
    short_interest_pct_float,
)


def universe_tickers() -> list[str]:
    rows = layer_assignments()
    return sorted(rows["ticker"].tolist())


def equity_close(prices: pd.DataFrame, tickers: list[str]) -> pd.DataFrame:
    cols = [t for t in tickers if t in prices.columns]
    return prices[cols].sort_index()


def asof_loc(index: pd.DatetimeIndex, dt: pd.Timestamp) -> pd.Timestamp | None:
    """Last index date ≤ dt."""
    if len(index) == 0:
        return None
    pos = index.searchsorted(pd.Timestamp(dt), side="right") - 1
    if pos < 0:
        return None
    return index[pos]


def episode_return(
    close: pd.Series, start: pd.Timestamp, end: pd.Timestamp
) -> float:
    """Close-to-close return over [start, end] using available bars."""
    s = asof_loc(close.dropna().index, start)
    e = asof_loc(close.dropna().index, end)
    if s is None or e is None or e <= s:
        return float("nan")
    c0, c1 = float(close.loc[s]), float(close.loc[e])
    if c0 <= 0 or not np.isfinite(c0) or not np.isfinite(c1):
        return float("nan")
    return c1 / c0 - 1.0


def features_through(
    close: pd.DataFrame,
    volume: pd.DataFrame,
    asof: pd.Timestamp,
) -> pd.DataFrame:
    """Feature cross-section at `asof` using only data dated ≤ asof.

    Look-ahead gate: caller must pass close/volume already truncated to asof,
    or this function truncates defensively.
    """
    close_t = close.loc[:asof]
    volume_t = volume.loc[:asof] if len(volume) else volume
    tickers = list(close_t.columns)

    mom = prior_return(close_t, 63)
    dist = distance_from_high(close_t, 252)
    vol = realised_vol(close_t, 21)
    adv = adv_dollar(close_t, volume_t, 21) if len(volume_t) else pd.DataFrame()

    if asof not in close_t.index:
        asof = asof_loc(close_t.index, asof)
        if asof is None:
            return pd.DataFrame(index=tickers)

    row = pd.DataFrame(index=tickers)
    row["prior_63d_return"] = mom.loc[asof] if asof in mom.index else np.nan
    row["dist_252d_high"] = dist.loc[asof] if asof in dist.index else np.nan
    row["realised_vol_21d"] = vol.loc[asof] if asof in vol.index else np.nan
    row["short_interest_pct_float"] = short_interest_pct_float(tickers)
    row = row.join(empty_valuation(tickers), how="left")
    row = row.join(empty_funding(tickers), how="left")
    row["log_mkt_cap"] = log_mkt_cap_placeholder(tickers)
    if len(adv) and asof in adv.index:
        row["adv"] = adv.loc[asof].reindex(tickers)
    else:
        row["adv"] = np.nan

    layers = layer_assignments().set_index("ticker")
    row = row.join(layers[["layer", "layer_ambiguous", "layer_alternate_JUDGMENT"]], how="left")
    row["ai_revenue_exposure_0_3_JUDGMENT"] = ai_revenue_exposure().reindex(tickers)
    row["feature_asof"] = asof
    return row


def build_panel(
    prices_path: Path | None = None,
    raw_dir: Path | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (panel long, coverage long)."""
    prices_path = prices_path or (ROOT / "data" / "processed" / "prices.parquet")
    raw_dir = raw_dir or (ROOT / "data" / "raw" / "2026-11-07")
    prices = pd.read_parquet(prices_path)
    prices.index = pd.to_datetime(prices.index).tz_localize(None).normalize()
    tickers = universe_tickers()
    close = equity_close(prices, tickers)
    volume = load_volume_panel(raw_dir, tickers)

    eps = episodes()["episodes"]
    rows = []
    for eid, meta in eps.items():
        start = pd.Timestamp(meta["window"][0])
        end = pd.Timestamp(meta["window"][1])
        asof = asof_loc(close.index, start)
        if asof is None:
            continue
        # Hard truncation before feature compute (look-ahead audit)
        feats = features_through(close.loc[:asof], volume.loc[:asof] if len(volume) else volume, asof)
        for ticker, fr in feats.iterrows():
            if ticker not in close.columns:
                continue
            ep_ret = episode_return(close[ticker], start, end)
            listed = bool(close[ticker].loc[:asof].notna().any())
            rows.append(
                {
                    "episode": eid,
                    "episode_start": start,
                    "episode_end": end,
                    "ticker": ticker,
                    "listed_at_start": listed,
                    "episode_return": ep_ret,
                    "role": meta.get("role"),
                    "character": meta.get("character"),
                    **fr.to_dict(),
                }
            )
    panel = pd.DataFrame(rows)
    coverage = coverage_table(panel)
    return panel, coverage


def coverage_table(panel: pd.DataFrame) -> pd.DataFrame:
    """names × episodes × block → % non-missing among block columns."""
    records = []
    for (ep, ticker), g in panel.groupby(["episode", "ticker"], sort=True):
        row = g.iloc[0]
        for block, cols in BLOCK_COLS.items():
            present = [c for c in cols if c in g.columns]
            if not present:
                pct = 0.0
            else:
                vals = row[present]
                # layer string counts as present if non-null / non-empty
                n_ok = 0
                for c in present:
                    v = vals[c]
                    if c == "layer":
                        n_ok += int(isinstance(v, str) and len(v) > 0)
                    else:
                        n_ok += int(pd.notna(v))
                pct = 100.0 * n_ok / len(present)
            records.append(
                {
                    "ticker": ticker,
                    "episode": ep,
                    "block": block,
                    "pct_non_missing": pct,
                    "n_cols": len(present),
                    "listed_at_start": bool(row.get("listed_at_start", False)),
                }
            )
    return pd.DataFrame(records)


def coverage_summary(coverage: pd.DataFrame) -> pd.DataFrame:
    """Mean % non-missing by episode × block (across names listed at start)."""
    sub = coverage.loc[coverage["listed_at_start"]]
    return (
        sub.groupby(["episode", "block"], sort=True)["pct_non_missing"]
        .mean()
        .reset_index()
        .rename(columns={"pct_non_missing": "mean_pct_non_missing"})
    )


def run() -> dict:
    exhibits = ROOT / "outputs" / "exhibits"
    exhibits.mkdir(parents=True, exist_ok=True)
    processed = ROOT / "data" / "processed"
    processed.mkdir(parents=True, exist_ok=True)

    print("=== P3 H3 panel build (coverage only) ===")
    panel, coverage = build_panel()
    panel_path = processed / "panel.parquet"
    panel.to_parquet(panel_path, index=False)
    coverage.to_csv(exhibits / "h3_feature_coverage.csv", index=False)
    summary = coverage_summary(coverage)
    summary.to_csv(exhibits / "h3_feature_coverage_summary.csv", index=False)

    print(f"panel → {panel_path}  rows={len(panel)}  cols={len(panel.columns)}")
    print("\n=== Coverage summary (mean % non-missing | listed at start) ===")
    pivot = summary.pivot(index="episode", columns="block", values="mean_pct_non_missing")
    print(pivot.round(1).to_string())
    print("\n=== Coverage detail sample (first 20 rows) ===")
    print(coverage.head(20).to_string(index=False))

    # listed counts per episode
    listed = (
        panel.groupby("episode")["listed_at_start"]
        .agg(n_universe="size", n_listed="sum")
        .reset_index()
    )
    print("\n=== Listed at episode start ===")
    print(listed.to_string(index=False))

    # log tests_run
    tests_path = ROOT / "outputs" / "tests_run.csv"
    tests = pd.read_csv(tests_path)
    tests = tests[tests["test_id"] != "P3_H3_COVERAGE"]
    extra = pd.DataFrame(
        [
            {
                "test_id": "P3_H3_COVERAGE",
                "hypothesis": "H3",
                "description": "Feature coverage table names×episodes×block (% non-missing)",
                "status": "PASS",
                "raw_p": "",
                "bh_p": "",
                "effect": "",
                "n": len(coverage),
                "notes": (
                    "panel.parquet written; valuation/funding/SI/mktcap NaN pending ingest; "
                    "layer from universe.yaml; crowding+ADV from prices/volume"
                ),
            }
        ]
    )
    pd.concat([tests, extra], ignore_index=True).to_csv(tests_path, index=False)
    return {"panel": panel, "coverage": coverage, "summary": summary}


def main() -> None:
    run()


if __name__ == "__main__":
    main()
