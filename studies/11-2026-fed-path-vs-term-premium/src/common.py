"""Shared helpers: run log, test ledger, differencing, weekly sampling, trading-day windows.

Units: the data are in percentage points; changes are reported in basis points (x100).
No forward-filling anywhere.
"""
from __future__ import annotations

import csv
import datetime as dt
import json
import math
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd

STUDY_DIR = Path(__file__).resolve().parents[1]
OUT = STUDY_DIR / "out"
RUNS_CSV = OUT / "runs.csv"
TESTS_CSV = OUT / "tests_run.csv"
RUN_FIELDS = ["timestamp", "script", "params", "result", "git_hash"]
TEST_FIELDS = ["test_id", "hypothesis", "description", "status", "raw_p", "bh_p",
               "effect", "n", "notes", "raw_p_num", "family"]

END_2026 = pd.Timestamp("2026-11-13")
BP = 100.0


# --- logging -----------------------------------------------------------------

def git_hash() -> str:
    """Short HEAD hash, '-dirty' if tracked study files outside out/ have uncommitted changes."""
    try:
        h = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=STUDY_DIR,
                           capture_output=True, text=True, check=True).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no", "--", ".",
                                ":(exclude)out"], cwd=STUDY_DIR, capture_output=True, text=True).stdout.strip()
        return h + ("-dirty" if dirty else "")
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _clean(x):
    if isinstance(x, (np.floating, float)):
        return None if math.isnan(x) else round(float(x), 6)
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (pd.Timestamp, dt.date)):
        return str(pd.Timestamp(x).date())
    if isinstance(x, dict):
        return {k: _clean(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_clean(v) for v in x]
    return x


def log_run(script: str, params: dict, result: dict, path: Path = RUNS_CSV) -> None:
    """Append one row to out/runs.csv."""
    path.parent.mkdir(parents=True, exist_ok=True)
    new = not path.exists()
    with path.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=RUN_FIELDS, lineterminator="\n")
        if new:
            w.writeheader()
        w.writerow({
            "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "script": script,
            "params": json.dumps(_clean(params), sort_keys=True),
            "result": json.dumps(_clean(result), sort_keys=True),
            "git_hash": git_hash(),
        })


def log_test(test_id: str, hypothesis: str, description: str, status: str, raw_p: float | None,
             effect: str, n: int, notes: str, family: str, path: Path = TESTS_CSV) -> None:
    """Append one row to out/tests_run.csv.

    Append-only: if test_id already has a row (a re-run), the earlier row is kept and
    its notes are prefixed "SUPERSEDED by re-run <timestamp>"; src/fdr.py uses the
    latest row per test_id. bh_p is written by src/fdr.py.
    """
    rows = []
    if path.exists():
        with path.open() as f:
            rows = list(csv.DictReader(f))
    ts = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    for r in rows:
        if r["test_id"] == test_id and not r["notes"].startswith("SUPERSEDED"):
            r["notes"] = f"SUPERSEDED by re-run {ts}; " + r["notes"]
    rows.append({
        "test_id": test_id, "hypothesis": hypothesis, "description": description, "status": status,
        "raw_p": "" if raw_p is None else f"{raw_p:.4g}", "bh_p": "", "effect": effect, "n": n,
        "notes": notes, "raw_p_num": "" if raw_p is None else repr(float(raw_p)), "family": family,
    })
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=TEST_FIELDS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


# --- differencing ------------------------------------------------------------

def own_diff(s: pd.Series) -> pd.Series:
    """Change from the previous date on which this series is published (no fill)."""
    return s.dropna().diff().dropna()


def pairwise_diff(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """Each series differenced on its own published dates, then kept only on days
    where every series has a change (present on t and on its own previous date)."""
    return pd.concat({c: own_diff(df[c]) for c in cols}, axis=1, sort=True).dropna()


def weekly_last(s: pd.Series) -> pd.Series:
    """Last available business-day value of each Mon-Fri week, labelled by the Friday.
    Weeks with no observation stay NaN, so differences never span a gap."""
    s = s.dropna()
    s = s[s.index.dayofweek < 5]
    return s.resample("W-FRI").last()


def weekly_diff(s: pd.Series) -> pd.Series:
    """Week-on-week change of weekly_last; NaN where either week is missing."""
    return weekly_last(s).diff()


# --- trading-day windows -----------------------------------------------------

def window(index: pd.DatetimeIndex, t0: pd.Timestamp, before: int, after: int,
           cap: pd.Timestamp | None = None) -> dict:
    """Window from `before` trading days before t0 to `after` trading days after t0,
    counted on `index` (a model's own calendar). If `cap` is given the end is the
    last date <= cap. Raises if t0 is not a trading day or history is too short."""
    index = pd.DatetimeIndex(index).sort_values()
    if t0 not in index:
        raise KeyError(f"t0 {t0.date()} not in calendar")
    pos = index.get_loc(t0)
    if pos - before < 0:
        raise IndexError(f"not enough history before {t0.date()}")
    end_pos = pos + after
    truncated = False
    if end_pos >= len(index):
        end_pos, truncated = len(index) - 1, True
    if cap is not None and index[end_pos] > cap:
        end_pos = int(index.searchsorted(cap, side="right")) - 1
        truncated = True
    return {"start": index[pos - before], "t0": t0, "end": index[end_pos],
            "end_offset": end_pos - pos, "truncated": truncated}


def share(d_tp: float, d_y: float, min_abs_bp: float = 25.0) -> float:
    """dTP / dy, NaN if |dy| < min_abs_bp (both in bp)."""
    return float("nan") if abs(d_y) < min_abs_bp else d_tp / d_y


def d1_share(d_tp: float, d_rny: float) -> float:
    """D1: |dTP| / (|dTP| + |dRNY|); NaN if both are zero."""
    den = abs(d_tp) + abs(d_rny)
    return float("nan") if den == 0 else abs(d_tp) / den


def one_sided_p(t: float, p_two: float) -> float:
    """One-sided p for H1: coefficient > 0, from a symmetric two-sided test."""
    return p_two / 2 if t > 0 else 1 - p_two / 2
