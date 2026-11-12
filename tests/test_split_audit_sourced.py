"""Split audit: every |ret|>25% needs a sourced reason; no auto-explain."""

from __future__ import annotations

import pandas as pd
import pytest

from core.adjust.splits import (
    ALLOWED_REASON_CATEGORIES,
    audit_large_moves,
    load_large_move_reasons,
)
from core.config_io import ROOT


def test_reasons_catalog_covers_known_critical_moves():
    reasons = load_large_move_reasons()
    # APLD +100% on 2022-07-19: Marathon deal + guidance
    apld = reasons[(reasons["ticker"] == "APLD") & (reasons["date"] == "2022-07-19")]
    assert len(apld) == 1
    assert apld.iloc[0]["category"] == "deal"
    assert "http" in apld.iloc[0]["source"]
    assert "Marathon" in apld.iloc[0]["reason"] or "200" in apld.iloc[0]["reason"]

    # SNDK 2025-02-18: when-issued vs regular-way
    sndk = reasons[(reasons["ticker"] == "SNDK") & (reasons["date"] == "2025-02-18")]
    assert len(sndk) == 1
    assert sndk.iloc[0]["category"] == "ipo_listing"
    assert "when-issued" in sndk.iloc[0]["reason"].lower() or "when issued" in sndk.iloc[0]["reason"].lower()
    assert "http" in sndk.iloc[0]["source"]


def test_all_catalog_categories_allowed_and_sourced():
    reasons = load_large_move_reasons()
    assert len(reasons) >= 1
    for _, r in reasons.iterrows():
        assert r["category"] in ALLOWED_REASON_CATEGORIES
        assert str(r["source"]).startswith("http")
        assert str(r["reason"]).strip()


def test_unexplained_large_move_fails_audit(tmp_path):
    # Synthetic close with a >25% jump and empty raw (no yahoo splits)
    idx = pd.bdate_range("2020-01-01", periods=5)
    close = pd.DataFrame({"FAKE": [10.0, 10.0, 10.0, 15.0, 15.0]}, index=idx)
    gap_log, _split, failures = audit_large_moves(close, tmp_path)
    assert failures, "expected unexplained FAKE move to fail"
    assert any("FAKE" in f and "unexplained" in f for f in failures)
    assert not bool(gap_log.iloc[0]["explained"])


def test_audit_passes_on_prices_parquet_when_catalog_complete():
    prices = ROOT / "data" / "processed" / "prices.parquet"
    if not prices.exists():
        pytest.skip("prices.parquet not present")
    raw_dirs = sorted((ROOT / "data" / "raw").glob("20*"))
    if not raw_dirs:
        pytest.skip("no raw dir")
    raw_dir = raw_dirs[-1]
    close = pd.read_parquet(prices)
    # wide close panel
    if "Close" in close.columns and "ticker" in close.columns:
        wide = close.pivot_table(index="date", columns="ticker", values="Close")
    else:
        wide = close
    gap_log, split_report, failures = audit_large_moves(wide, raw_dir)
    assert not failures, failures[:5]
    if len(gap_log):
        assert bool(gap_log["explained"].all())
