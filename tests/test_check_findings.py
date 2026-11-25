"""Tests for scripts/check_findings.py (good file passes; each defect fails)."""

from __future__ import annotations

import datetime as dt
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("check_findings", ROOT / "scripts" / "check_findings.py")
cf = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cf)

TODAY = dt.date(2026, 11, 25)

FINDING = """\
- id: {fid}
  study: studies/{study}
  type: quant
  region: US
  topic: methods
  claim: A short plain claim about the result.
  verdict: {verdict}
  confidence: null
  numbers:
    - "{number}"
  source_file: studies/{study}/RESULTS.md
  run_date: 2026-11-20
  valid_until: {valid_until}
  owner_bot: vera
  links_to: []
  people: []
"""


def section(study: str, findings: str, status: str = "complete") -> str:
    return (
        f"## studies/{study}\n\n"
        f"Status: {status} | Run: 2026-11-20 | Source: RESULTS.md\n\n"
        f"```yaml\n{findings}```\n\n"
    )


def finding(study="2026-11-alpha", fid="ud-alpha-one", number="t 2.41", verdict="supported",
            valid_until="null"):
    return FINDING.format(study=study, fid=fid, number=number, verdict=verdict,
                          valid_until=valid_until)


def make_repo(tmp_path: Path, body: str, studies=("2026-11-alpha",)) -> Path:
    for s in studies:
        d = tmp_path / "studies" / s
        d.mkdir(parents=True)
        (d / "RESULTS.md").write_text("Result: t 2.41, p 0.016 (n = 120).\n", encoding="utf-8")
    tpl = tmp_path / "studies" / "_template"
    tpl.mkdir(parents=True)
    (tpl / "RESULTS.md").write_text("template\n", encoding="utf-8")
    (tmp_path / "FINDINGS.md").write_text(
        "# Findings: test\n\nLast updated: 2026-11-25\n\n"
        "Nothing here is a trading recommendation.\n\n" + body,
        encoding="utf-8",
    )
    return tmp_path


def run(root: Path, today: dt.date = TODAY):
    return cf.check(root, today)


def test_good_file_passes(tmp_path):
    root = make_repo(tmp_path, section("2026-11-alpha", finding()))
    errors, warnings = run(root)
    assert errors == []
    assert warnings == []
    assert cf.main(["--root", str(root), "--today", "2026-11-25"]) == 0


def test_repo_findings_file_passes():
    errors, _ = run(ROOT)
    assert errors == []


def test_missing_number_fails(tmp_path):
    root = make_repo(tmp_path, section("2026-11-alpha", finding(number="t 3.10")))
    errors, _ = run(root)
    assert any("not found verbatim" in e for e in errors)
    assert cf.main(["--root", str(root)]) == 1


def test_rounded_number_fails(tmp_path):
    root = make_repo(tmp_path, section("2026-11-alpha", finding(number="p 0.02")))
    errors, _ = run(root)
    assert any("not found verbatim" in e for e in errors)


def test_duplicate_id_fails(tmp_path):
    body = section("2026-11-alpha", finding() + finding())
    root = make_repo(tmp_path, body)
    errors, _ = run(root)
    assert any("duplicate id" in e for e in errors)


def test_duplicate_section_fails(tmp_path):
    body = section("2026-11-alpha", finding()) + section("2026-11-alpha", finding(fid="ud-alpha-two"))
    root = make_repo(tmp_path, body)
    errors, _ = run(root)
    assert any("duplicate section" in e for e in errors)


def test_missing_section_fails(tmp_path):
    root = make_repo(tmp_path, section("2026-11-alpha", finding()),
                     studies=("2026-11-alpha", "2026-11-beta"))
    errors, _ = run(root)
    assert any("2026-11-beta" in e and "no section" in e for e in errors)


def test_readme_answer_section_requires_findings(tmp_path):
    root = make_repo(tmp_path, section("2026-11-alpha", finding()))
    d = root / "studies" / "2026-11-gamma"
    d.mkdir()
    (d / "README.md").write_text("# Gamma\n\n## Answer\n\n- something\n", encoding="utf-8")
    errors, _ = run(root)
    assert any("2026-11-gamma" in e for e in errors)


def test_template_is_skipped(tmp_path):
    root = make_repo(tmp_path, section("2026-11-alpha", finding()))
    errors, _ = run(root)
    assert not any("_template" in e for e in errors)


def test_missing_field_fails(tmp_path):
    bad = finding().replace("  people: []\n", "")
    root = make_repo(tmp_path, section("2026-11-alpha", bad))
    errors, _ = run(root)
    assert any("missing field" in e and "people" in e for e in errors)


def test_invalid_enum_fails(tmp_path):
    root = make_repo(tmp_path, section("2026-11-alpha", finding(verdict="proven")))
    errors, _ = run(root)
    assert any("verdict" in e for e in errors)


def test_unparseable_yaml_fails(tmp_path):
    root = make_repo(tmp_path, section("2026-11-alpha", "- id: [unclosed\n"))
    errors, _ = run(root)
    assert any("does not parse" in e for e in errors)


def test_unknown_link_fails_but_fw_id_allowed(tmp_path):
    bad = finding().replace("links_to: []", "links_to: [ud-nope, fw-fomc-dec-2026]")
    root = make_repo(tmp_path, section("2026-11-alpha", bad))
    errors, _ = run(root)
    assert any("'ud-nope'" in e for e in errors)
    assert not any("fw-fomc-dec-2026" in e for e in errors)


def test_past_valid_until_warns_only(tmp_path):
    root = make_repo(tmp_path, section("2026-11-alpha", finding(valid_until="2026-11-01")))
    errors, warnings = run(root)
    assert errors == []
    assert any("in the past" in w for w in warnings)
    assert cf.main(["--root", str(root), "--today", "2026-11-25"]) == 0


def test_missing_disclaimer_fails(tmp_path):
    root = make_repo(tmp_path, section("2026-11-alpha", finding()))
    p = root / "FINDINGS.md"
    p.write_text(p.read_text().replace("Nothing here is a trading recommendation.", ""))
    errors, _ = run(root)
    assert any("trading recommendation" in e for e in errors)


@pytest.mark.parametrize("words", [31, 40])
def test_long_claim_fails(tmp_path, words):
    bad = finding().replace("A short plain claim about the result.", " ".join(["word"] * words))
    root = make_repo(tmp_path, section("2026-11-alpha", bad))
    errors, _ = run(root)
    assert any("words" in e for e in errors)
