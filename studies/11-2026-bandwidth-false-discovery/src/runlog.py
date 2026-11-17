"""Append one row per experiment to out/runs.csv (CLAUDE.md rule)."""

from __future__ import annotations

import csv
import datetime as dt
import json
import subprocess
from pathlib import Path

STUDY_DIR = Path(__file__).resolve().parents[1]
RUNS_CSV = STUDY_DIR / "out" / "runs.csv"
FIELDS = ["timestamp", "script", "params", "bandwidth", "result", "git_hash"]


def git_hash() -> str:
    """Short HEAD hash, suffixed '-dirty' if tracked files under the study, outside out/,
    have uncommitted changes. (Before 16 Nov 2026 12:35 UTC the check also counted out/,
    so runs.csv itself flagged every row after the first in a multi-row run as dirty.)"""
    try:
        h = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=STUDY_DIR,
                           capture_output=True, text=True, check=True).stdout.strip()
        # Outputs under out/ (including runs.csv itself) do not make the code dirty.
        dirty = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no", "--", ".",
                                ":(exclude)out"],
                               cwd=STUDY_DIR, capture_output=True, text=True).stdout.strip()
        return h + ("-dirty" if dirty else "")
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def log_run(script: str, params: dict, bandwidth, result: dict, path: Path = RUNS_CSV) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    new = not path.exists()
    with path.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new:
            w.writeheader()
        w.writerow({
            "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "script": script,
            "params": json.dumps(params, sort_keys=True),
            "bandwidth": bandwidth,
            "result": json.dumps(result, sort_keys=True),
            "git_hash": git_hash(),
        })
