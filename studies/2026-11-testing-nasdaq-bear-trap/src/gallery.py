"""N03: event gallery helpers (descriptive only; no tests).

Two sources:
  * Study 1 event lists (tests/fixtures), always available: per-event outcome
    profiles at entry, 20, 60 and 120 days, plus sweep depth and drawdown.
  * Close series (data/clean/*.csv), optional: price windows around each
    break, rebased to the broken support level.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .data import CLEAN, STUDY1_FILES, _read_close_csv
from .power import load_study1_events, HORIZONS

PROFILE_DAYS = (0,) + tuple(HORIZONS)


def gallery_frame(index: str) -> pd.DataFrame:
    """Study 1 events with gallery labels and an outcome category."""
    ev = load_study1_events(index).copy()
    ev["label"] = ev.apply(lambda r: f"#{int(r['n'])} {r['break_date']:%b %Y}", axis=1)
    ev["outcome"] = np.select(
        [~ev["reclaimed"], ev["retest"] == True, ev["retest"] == False],  # noqa: E712
        ["not reclaimed", "reclaimed, retested", "reclaimed, held"],
        default="reclaimed, retest n/a")
    return ev


def outcome_profiles(ev: pd.DataFrame) -> pd.DataFrame:
    """Long frame: one row per event and day in PROFILE_DAYS, return from entry close.

    Day 0 is 0 by definition; missing horizons stay NaN (no partial windows).
    """
    rows = []
    for _, r in ev.iterrows():
        for d in PROFILE_DAYS:
            rows.append(dict(n=int(r["n"]), label=r["label"], outcome=r["outcome"], day=d,
                             ret=0.0 if d == 0 else r[f"r{d}"]))
    return pd.DataFrame(rows)


def outcome_summary(ev: pd.DataFrame) -> pd.DataFrame:
    """Counts and median outcomes per outcome category."""
    g = ev.groupby("outcome")
    out = pd.DataFrame({
        "events": g.size(),
        "median_sweep_vs_level": g["sweep_vs_level"].median(),
        "median_dd_at_break": g["dd_at_break"].median(),
        **{f"median_r{h}": g[f"r{h}"].median() for h in HORIZONS},
        "median_worst60": g["worst60"].median(),
    })
    return out.reset_index()


def grid_shape(k: int, ncols: int = 6) -> tuple[int, int]:
    ncols = max(1, min(ncols, k))
    return int(np.ceil(k / ncols)), ncols


# ----------------------------------------------------------------------------
# Optional price windows
# ----------------------------------------------------------------------------
def load_clean_close(index: str) -> pd.Series | None:
    """Study 1 clean close series if present, else None (no network fallback)."""
    f = CLEAN / STUDY1_FILES[index]
    return _read_close_csv(f) if f.exists() else None


def price_window(close: pd.Series, break_date, level: float,
                 pre: int = 40, post: int = 120) -> pd.DataFrame:
    """Closes from `pre` days before to `post` days after the break, rebased to the level.

    Columns: day (0 = break day), rel (close / level - 1). Truncated at data end.
    """
    pos = close.index.get_indexer([pd.Timestamp(break_date)])[0]
    if pos < 0:
        raise KeyError(f"break date {break_date} not in close series")
    lo, hi = max(0, pos - pre), min(len(close) - 1, pos + post)
    seg = close.iloc[lo:hi + 1]
    return pd.DataFrame({"day": np.arange(lo, hi + 1) - pos,
                         "rel": seg.to_numpy(float) / level - 1}, index=seg.index)
