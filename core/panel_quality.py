"""Missing-data and survivorship gates (Pre-P1 revision e)."""

from __future__ import annotations

from typing import Any

import pandas as pd

from core.config_io import episodes, universe


def universe_tickers() -> list[str]:
    u = universe()["layers"]
    tickers: list[str] = []
    for layer in u.values():
        tickers.extend(layer["names"].keys())
    # unique, stable
    seen: set[str] = set()
    out: list[str] = []
    for t in tickers:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


def episode_windows() -> dict[str, tuple[str, str]]:
    eps = episodes()["episodes"]
    return {eid: (meta["window"][0], meta["window"][1]) for eid, meta in eps.items()}


def names_existing_at(
    listing_start: pd.Series,
    asof: pd.Timestamp,
) -> pd.Index:
    """`listing_start` maps ticker → first available close date (NaT if never)."""
    return listing_start[listing_start.notna() & (listing_start <= asof)].index


def episode_missingness_report(
    panel: pd.DataFrame,
    listing_start: pd.Series,
    feature_cols: list[str],
    max_nan_share: float = 0.15,
) -> pd.DataFrame:
    """Per-episode NaN share among names that existed at episode start.

    Gate: mean NaN across feature_cols must be < max_nan_share for each episode.
    Always prints how many of today's universe existed at each episode start.
    """
    rows: list[dict[str, Any]] = []
    for eid, (start, end) in episode_windows().items():
        asof = pd.Timestamp(start)
        existing = names_existing_at(listing_start, asof)
        sub = panel.reindex(existing)
        if len(sub) == 0:
            nan_share = 1.0
        else:
            nan_share = float(sub[feature_cols].isna().mean().mean())
        rows.append(
            {
                "episode": eid,
                "start": start,
                "end": end,
                "n_universe_today": len(listing_start),
                "n_existed_at_start": int(len(existing)),
                "nan_share": nan_share,
                "pass_nan_gate": nan_share < max_nan_share,
            }
        )
    report = pd.DataFrame(rows)
    print(report.to_string(index=False))
    return report


def assert_episode_nan_gates(report: pd.DataFrame) -> None:
    bad = report.loc[~report["pass_nan_gate"], "episode"].tolist()
    if bad:
        raise AssertionError(f"episode NaN gate failed for: {bad}")
