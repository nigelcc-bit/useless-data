"""Study results stay pinned to 2026-11-05; monitor snapshots are separate."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from core.config_io import ROOT
from src.study_pin import (
    MONITOR_SNAPSHOTS,
    STUDY_ASOF,
    assert_study_pinned_to_asof,
    study_price_max_date,
)


def test_study_prices_pinned_to_2026_11_05():
    assert study_price_max_date().normalize() == STUDY_ASOF.normalize()
    assert_study_pinned_to_asof()


def test_panel_and_prices_share_study_pin():
    for name in ("adj_close.parquet", "prices.parquet"):
        p = ROOT / "data" / "processed" / name
        assert p.exists()
        mx = pd.Timestamp(pd.read_parquet(p).index.max()).normalize()
        assert mx == STUDY_ASOF.normalize(), f"{name} ends {mx.date()}, not pin"


def test_monitor_snapshot_may_extend_past_pin_without_mutating_study():
    """If a monitor snapshot exists, it can be newer; study files unchanged."""
    study_max = study_price_max_date()
    latest = MONITOR_SNAPSHOTS / "LATEST"
    if not latest.exists():
        return  # no snapshot yet — pin test still passes
    snap = MONITOR_SNAPSHOTS / latest.read_text().strip()
    adj = snap / "adj_close.parquet"
    if not adj.exists():
        return
    snap_max = pd.Timestamp(pd.read_parquet(adj).index.max()).normalize()
    assert snap_max >= study_max
    # Study file still pinned
    assert study_price_max_date() == STUDY_ASOF.normalize()
