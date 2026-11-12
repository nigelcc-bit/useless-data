#!/usr/bin/env python3
"""Refresh tests_run.csv after P2 review: T001 done, D5/D7 via P1, P2 rows."""

from __future__ import annotations

import pandas as pd

from core.config_io import ROOT, study_outputs


def upsert(df: pd.DataFrame, row: dict) -> pd.DataFrame:
    df = df[df["test_id"] != row["test_id"]]
    return pd.concat([df, pd.DataFrame([row])], ignore_index=True)


def main() -> None:
    path = study_outputs() / "tests_run.csv"
    df = pd.read_csv(path)

    # T001: H1 power check completed in P2 (counts)
    df = upsert(
        df,
        {
            "test_id": "T001",
            "hypothesis": "H1",
            "description": "power check SOX/SMH/IXIC/SPX first-shock cells (counts)",
            "status": "DONE",
            "raw_p": "",
            "bh_p": "",
            "effect": "",
            "n": "",
            "notes": (
                "P2 h1_power_table.csv; N>=8 → TESTABLE_N_GE_8 else "
                "PRIOR_ONLY_NOT_TESTED; SPX 151 control PASS"
            ),
        },
    )

    # D5 / D7 resolved via P1 ingest (note magnitudes SUPERSEDED / UNRECONCILED)
    df = upsert(
        df,
        {
            "test_id": "T010",
            "hypothesis": "D5",
            "description": "name-level YTD and prior-5d unverified",
            "status": "RESOLVED_VIA_P1",
            "raw_p": "",
            "bh_p": "",
            "effect": "",
            "n": "",
            "notes": (
                "Yahoo Close Spearmans computed; note YTD label UNRECONCILED; "
                "see docs/gap_diagnosis.md / P1_D5_D7"
            ),
        },
    )
    df = upsert(
        df,
        {
            "test_id": "T012",
            "hypothesis": "D7",
            "description": "name-level EW / 52w counts lack RAW_FILE",
            "status": "RESOLVED_VIA_P1",
            "raw_p": "",
            "bh_p": "",
            "effect": "",
            "n": "",
            "notes": (
                "prices.parquet RAW_FILE present; EW/52w re-derived; "
                "note magnitudes SUPERSEDED where disagreed"
            ),
        },
    )
    df = upsert(
        df,
        {
            "test_id": "T000b",
            "hypothesis": "meta",
            "description": "Spearman YTD/prior5 fixture gates",
            "status": "RESOLVED_VIA_P1",
            "raw_p": "",
            "bh_p": "",
            "effect": "",
            "n": "",
            "notes": "D5 resolved via P1; calibrated panel remains quarantined",
        },
    )
    df = upsert(
        df,
        {
            "test_id": "T000c",
            "hypothesis": "meta",
            "description": "hyperscaler/supplier EW and 21/23 below 52w",
            "status": "RESOLVED_VIA_P1",
            "raw_p": "",
            "bh_p": "",
            "effect": "",
            "n": "",
            "notes": "D7 resolved via P1 RAW_FILE; see P1_REDERIVE_XS",
        },
    )

    # Split audit policy refresh
    df = upsert(
        df,
        {
            "test_id": "P2_SPLIT_AUDIT",
            "hypothesis": "meta",
            "description": (
                "Every |ret|>25% requires sourced reason "
                "(earnings/deal/ipo_listing/split); no auto-explain"
            ),
            "status": "PASS",
            "raw_p": "",
            "bh_p": "",
            "effect": "",
            "n": "",
            "notes": (
                "config/large_move_reasons.yaml; APLD 2022-07-19=deal (Marathon); "
                "SNDK 2025-02-18=ipo_listing (when-issued→regular-way)"
            ),
        },
    )

    df.to_csv(path, index=False)
    print(f"refreshed {path} rows={len(df)}")
    print(df[["test_id", "status"]].to_string(index=False))


if __name__ == "__main__":
    main()
