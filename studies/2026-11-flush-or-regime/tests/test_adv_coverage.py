"""ADV regression guard: listed names must have ≥90% ADV coverage in the panel.

Broke in commit 2902f6f when volume was loaded from data/raw/2026-11-08
(SEC/FINRA folder with no yahoo_{TICKER}.json equity caches).
"""

from __future__ import annotations

import pandas as pd
import pytest

from core.config_io import ROOT
from core.features.liquidity import load_volume_panel, resolve_yahoo_raw_dir
from core.features.layer import layer_assignments


def test_yahoo_volume_dir_resolves_to_equity_caches():
    d = resolve_yahoo_raw_dir(ROOT / "data" / "raw" / "2026-11-08")
    if not any((ROOT / "data" / "raw").glob("*/yahoo_AAPL.json")):
        pytest.skip("yahoo equity caches not on disk (gitignored; restore via ingest)")
    assert (d / "yahoo_AAPL.json").exists(), f"no equity yahoo caches under {d}"
    sec_only = ROOT / "data" / "raw" / "2026-11-08"
    if not (sec_only / "yahoo_AAPL.json").exists():
        assert d != sec_only


def test_adv_coverage_listed_names_ge_90_percent():
    path = ROOT / "data" / "processed" / "panel.parquet"
    if not path.exists():
        pytest.skip("panel.parquet not built")
    panel = pd.read_parquet(path)
    listed = panel.loc[panel["listed_at_start"]]
    assert len(listed) > 0
    pct = float(listed["adv"].notna().mean() * 100.0)
    assert pct >= 90.0, f"ADV coverage for listed names is {pct:.1f}% (< 90%)"


def test_load_volume_panel_nonempty_for_universe():
    if not any((ROOT / "data" / "raw").glob("*/yahoo_AAPL.json")):
        pytest.skip("yahoo equity caches not on disk (gitignored; restore via ingest)")
    tickers = sorted(layer_assignments()["ticker"].tolist())
    vol = load_volume_panel(ROOT / "data" / "raw" / "2026-11-08", tickers)
    assert len(vol) > 0 and len(vol.columns) >= 30
