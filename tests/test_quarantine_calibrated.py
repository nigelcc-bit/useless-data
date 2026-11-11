"""Fail the build if any src/ module reads CALIBRATED-tagged data."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.config_io import ROOT

FORBIDDEN = ("CALIBRATED_CIRCULAR", "CALIBRATED", "ytd_source", "prior5_source")
SRC = ROOT / "src"
DATA = ROOT / "data"
CONFIG = ROOT / "config"


def test_data_and_config_contain_no_calibrated_values():
    hits: list[str] = []
    for root in (DATA, CONFIG):
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.name == ".gitkeep":
                continue
            text = path.read_text(errors="replace")
            for token in ("CALIBRATED_CIRCULAR", "CALIBRATED"):
                if token in text:
                    hits.append(f"{path.relative_to(ROOT)}: contains {token}")
    assert hits == [], "fabricated calibrated data must not live under data/ or config/:\n" + "\n".join(hits)


def test_src_modules_do_not_reference_calibrated_columns_or_files():
    hits: list[str] = []
    for path in SRC.rglob("*.py"):
        text = path.read_text()
        for token in FORBIDDEN:
            if token in text:
                hits.append(f"{path.relative_to(ROOT)}: references {token}")
        # Explicit ban on the quarantined panel filename if reintroduced with calibrated cols
        if "nov5_cross_section" in text and "CALIBRATED" in text:
            hits.append(f"{path.relative_to(ROOT)}: reads quarantined panel")
    assert hits == [], "src/ must not read CALIBRATED columns/files:\n" + "\n".join(hits)


def test_quarantined_panel_file_absent():
    panel = DATA / "processed" / "nov5_cross_section.csv"
    assert not panel.exists(), (
        f"{panel} must remain deleted; calibrated values live only in "
        "docs/reconstruction_audit.md"
    )
