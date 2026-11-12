"""Study data pin — H1–H5 results are frozen to this as-of date.

Monitor refresh writes a *separate* dated snapshot under
`data/processed/monitor_snapshots/`. It must never overwrite the
study-processed panels used by H1–H5.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from core.config_io import ROOT

STUDY_ASOF = pd.Timestamp("2026-11-05")
STUDY_PIN_META = ROOT / "data" / "processed" / "study_pin.json"
PROCESSED = ROOT / "data" / "processed"
MONITOR_SNAPSHOTS = PROCESSED / "monitor_snapshots"


def study_price_max_date(path: Path | None = None) -> pd.Timestamp:
    """Max calendar date in the study-pinned adj_close / prices panel."""
    p = path or (PROCESSED / "adj_close.parquet")
    idx = pd.read_parquet(p).index
    return pd.Timestamp(pd.to_datetime(idx).max()).tz_localize(None).normalize()


def assert_study_pinned_to_asof(asof: pd.Timestamp = STUDY_ASOF) -> None:
    """Hard gate: study processed prices must end on STUDY_ASOF."""
    mx = study_price_max_date()
    if mx.normalize() != pd.Timestamp(asof).normalize():
        raise AssertionError(
            f"Study prices end on {mx.date()}, expected pin {pd.Timestamp(asof).date()}. "
            "Monitor refresh must not mutate data/processed/{{adj_close,prices,panel}}.parquet."
        )


def write_pin_meta() -> None:
    import json

    meta = {
        "study_asof": str(STUDY_ASOF.date()),
        "adj_close_max": str(study_price_max_date().date()),
        "note": (
            "H1–H5 results are pinned to this as-of. "
            "Monitor snapshots live under data/processed/monitor_snapshots/."
        ),
    }
    STUDY_PIN_META.write_text(json.dumps(meta, indent=2))
