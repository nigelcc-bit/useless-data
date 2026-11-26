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
  hypothesis: The signal predicts returns.
  verdict: {verdict}
  finding: {finding_text}
  key_stats:
    - "{stat}"
  confidence: null
  numbers:
    - "{number}"
  source_file: studies/{study}/RESULTS.md
  run_date: 2026-11-20
  valid_until: {valid_until}
  owner: {owner}
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
            valid_until="null", owner="fx-115",
            finding_text="The signal predicted returns, with a test score of 2.41.",
            stat="test score 2.41"):
    return FINDING.format(study=study, fid=fid, number=number, verdict=verdict,
                          valid_until=valid_until, owner=owner, finding_text=finding_text,
                          stat=stat)


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
    root = make_repo(tmp_path, section("2026-11-alpha", finding(
        number="t 3.10", finding_text="The signal predicted returns, score 3.10.", stat="score 3.10")))
    errors, _ = run(root)
    assert any("not found verbatim" in e for e in errors)
    assert cf.main(["--root", str(root)]) == 1


def test_rounded_number_fails(tmp_path):
    root = make_repo(tmp_path, section("2026-11-alpha", finding(
        number="p 0.02", finding_text="The signal predicted returns.", stat="p-value 0.02")))
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
def test_long_finding_fails(tmp_path, words):
    bad = finding(finding_text=" ".join(["word"] * words))
    root = make_repo(tmp_path, section("2026-11-alpha", bad))
    errors, _ = run(root)
    assert any("words" in e for e in errors)


@pytest.mark.parametrize("field", ["hypothesis", "finding", "key_stats", "owner"])
def test_each_new_field_is_required(tmp_path, field):
    lines = finding().splitlines(keepends=True)
    out, skip = [], False
    for ln in lines:
        if ln.startswith(f"  {field}:"):
            skip = True
            continue
        if skip and ln.startswith("    - "):
            continue
        skip = False
        out.append(ln)
    root = make_repo(tmp_path, section("2026-11-alpha", "".join(out)))
    errors, _ = run(root)
    assert any("missing field" in e and field in e for e in errors)


@pytest.mark.parametrize("owner", ["vera", "tilly", "fx-1150", "FX-115", "bot-115"])
def test_owner_must_be_bot_id(tmp_path, owner):
    root = make_repo(tmp_path, section("2026-11-alpha", finding(owner=owner)))
    errors, _ = run(root)
    assert any("owner" in e for e in errors)


@pytest.mark.parametrize("owner", ["fx-117", "cx-042"])
def test_owner_bot_ids_accepted(tmp_path, owner):
    root = make_repo(tmp_path, section("2026-11-alpha", finding(owner=owner)))
    errors, _ = run(root)
    assert errors == []


def test_old_field_names_fail(tmp_path):
    old = finding().replace("  owner: fx-115", "  owner_bot: vera").replace("  hypothesis:", "  claim:")
    root = make_repo(tmp_path, section("2026-11-alpha", old))
    errors, _ = run(root)
    assert any("missing field" in e and "owner" in e and "hypothesis" in e for e in errors)


def test_number_in_finding_missing_from_numbers_fails(tmp_path):
    root = make_repo(tmp_path, section("2026-11-alpha", finding(
        finding_text="The signal predicted returns, with a test score of 2.4.")))
    errors, _ = run(root)
    assert any("'2.4'" in e and "not in numbers" in e for e in errors)


def test_number_in_key_stats_missing_from_numbers_fails(tmp_path):
    root = make_repo(tmp_path, section("2026-11-alpha", finding(stat="won 7 of 10 times")))
    errors, _ = run(root)
    assert any("not in numbers" in e for e in errors)


def test_markdown_in_key_stats_fails(tmp_path):
    root = make_repo(tmp_path, section("2026-11-alpha", finding(stat="test score **2.41**")))
    errors, _ = run(root)
    assert any("markdown" in e for e in errors)


def test_too_many_key_stats_fails(tmp_path):
    many = finding().replace('    - "test score 2.41"\n', '    - "test score 2.41"\n' * 4)
    root = make_repo(tmp_path, section("2026-11-alpha", many))
    errors, _ = run(root)
    assert any("key_stats must be" in e for e in errors)
