"""P1 gate: SPEC_LITERAL fixtures must reproduce from ingested prices."""

from __future__ import annotations

import pytest

from src.gates.p1_spec_literal import (
    PRICES_PATH,
    SPEC_LITERAL_CHECKS,
    prices_available,
    run_p1_spec_literal_gate,
)


def test_spec_literal_registry_covers_pass_rows():
    names = {c.name for c in SPEC_LITERAL_CHECKS}
    assert names == {
        "SOXX_5_Nov",
        "SPY_5_Nov",
        "QQQ_5_Nov",
        "SMH_5_Nov",
        "SOXX_six_session",
        "SOXX_log_decline_share_before_nov5",
    }


def test_p1_spec_literal_gate_against_ingested_prices():
    if not prices_available():
        pytest.skip(
            f"P1 ingest not present ({PRICES_PATH}); gate runs when prices.parquet exists"
        )
    report = run_p1_spec_literal_gate()
    assert report["pass"].all()


def test_p1_gate_fails_loud_when_prices_missing(tmp_path):
    missing = tmp_path / "prices.parquet"
    with pytest.raises(FileNotFoundError, match="P1 gate requires"):
        run_p1_spec_literal_gate(path=missing)
