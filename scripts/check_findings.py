#!/usr/bin/env python3
"""Validate FINDINGS.md against the study sources.

Usage:
    python scripts/check_findings.py [--root PATH] [--today YYYY-MM-DD]

Exit 1 (errors):
  - a yaml block does not parse, a field is missing, or a value is invalid
  - owner is not a bot ID (fx-NNN or cx-NNN)
  - finding is over 30 words
  - a numeric token in finding or key_stats is missing from numbers
  - an id is duplicated, or a study has more than one section
  - a string in `numbers` is not found verbatim in its `source_file`
  - a study folder (excluding _template) with a RESULTS.md or a README
    "## Answer" section has no section in FINDINGS.md
Exit 0 with a warning:
  - valid_until is in the past
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]

REQUIRED = [
    "id", "study", "type", "region", "topic", "hypothesis", "verdict", "finding",
    "key_stats", "confidence", "numbers", "source_file", "run_date", "valid_until",
    "owner", "links_to", "people",
]
ENUMS = {
    "type": {"quant"},
    "region": {"US", "global"},
    "verdict": {"supported", "killed", "weak", "prior-only", "inconclusive", "interim"},
}
OWNER_RE = re.compile(r"^(?:fx|cx)-\d{3}$")
STATUSES = {"complete", "interim"}
MAX_FINDING_WORDS = 30
MAX_KEY_STATS = 3
# A numeric token: 1,917 / 0.668 / 2026 / 3 (sign and % are not part of it).
NUM_TOKEN_RE = re.compile(r"[0-9]{1,3}(?:,[0-9]{3})+(?:\.[0-9]+)?|[0-9]+(?:\.[0-9]+)?")
MARKDOWN_RE = re.compile(r"\*\*|__|`|\[[^\]]*\]\(")
DISCLAIMER = "Nothing here is a trading recommendation"

SECTION_RE = re.compile(r"^## (studies/\S+)\s*$", re.M)
STATUS_RE = re.compile(
    r"^Status: (?P<status>\S+) \| Run: (?P<run>\d{4}-\d{2}-\d{2}) \| Source: (?P<source>\S+)\s*$",
    re.M,
)
YAML_RE = re.compile(r"```yaml\n(.*?)```", re.S)
LOCAL_ID_RE = re.compile(r"^ud-[a-z0-9]+(?:-[a-z0-9]+)*$")
FOREIGN_ID_RE = re.compile(r"^fw-[a-z0-9]+(?:-[a-z0-9]+)*$")


def _as_date(v) -> dt.date | None:
    if isinstance(v, dt.datetime):
        return v.date()
    if isinstance(v, dt.date):
        return v
    if isinstance(v, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", v):
        return dt.date.fromisoformat(v)
    return None


def study_folders(root: Path) -> list[str]:
    """Study folders that must have a FINDINGS.md section."""
    out = []
    sdir = root / "studies"
    if not sdir.is_dir():
        return out
    for d in sorted(p for p in sdir.iterdir() if p.is_dir()):
        if d.name.startswith("_"):
            continue
        readme = d / "README.md"
        has_answer = readme.exists() and re.search(
            r"^## Answer\b", readme.read_text(encoding="utf-8"), re.M
        )
        if (d / "RESULTS.md").exists() or has_answer:
            out.append(f"studies/{d.name}")
    return out


def check(root: Path, today: dt.date) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    path = root / "FINDINGS.md"
    if not path.exists():
        return [f"missing {path}"], warnings
    text = path.read_text(encoding="utf-8")
    if DISCLAIMER not in text:
        errors.append(f"FINDINGS.md must contain '{DISCLAIMER}'")

    heads = list(SECTION_RE.finditer(text))
    sections: dict[str, str] = {}
    for i, m in enumerate(heads):
        name = m.group(1).rstrip("/")
        body = text[m.end(): heads[i + 1].start() if i + 1 < len(heads) else len(text)]
        if name in sections:
            errors.append(f"{name}: duplicate section (re-runs must replace, not append)")
            continue
        sections[name] = body

    seen_ids: dict[str, str] = {}
    findings: list[tuple[str, dict]] = []
    for name, body in sections.items():
        sm = STATUS_RE.search(body)
        if not sm:
            errors.append(f"{name}: missing or malformed 'Status: ... | Run: ... | Source: ...' line")
        elif sm.group("status") not in STATUSES:
            errors.append(f"{name}: status {sm.group('status')!r} not in {sorted(STATUSES)}")
        blocks = YAML_RE.findall(body)
        if len(blocks) != 1:
            errors.append(f"{name}: expected exactly one ```yaml block, found {len(blocks)}")
            continue
        try:
            items = yaml.safe_load(blocks[0])
        except yaml.YAMLError as e:
            errors.append(f"{name}: yaml does not parse: {e}")
            continue
        if not isinstance(items, list) or not items:
            errors.append(f"{name}: yaml block must be a non-empty list of findings")
            continue
        for k, f in enumerate(items):
            if not isinstance(f, dict):
                errors.append(f"{name}: finding #{k + 1} is not a mapping")
                continue
            findings.append((name, f))

    for name, f in findings:
        fid = f.get("id", f"<finding without id in {name}>")
        where = f"{name} / {fid}"
        missing = [k for k in REQUIRED if k not in f]
        if missing:
            errors.append(f"{where}: missing field(s) {missing}")
            continue
        extra = sorted(set(f) - set(REQUIRED))
        if extra:
            errors.append(f"{where}: unknown field(s) {extra}")

        if not isinstance(fid, str) or not LOCAL_ID_RE.match(fid):
            errors.append(f"{where}: id must look like ud-<study-slug>-<short-key>")
        elif fid in seen_ids:
            errors.append(f"{where}: duplicate id (also in {seen_ids[fid]})")
        else:
            seen_ids[fid] = name

        if f["study"] != name:
            errors.append(f"{where}: study {f['study']!r} does not match section {name!r}")
        for key, allowed in ENUMS.items():
            if f[key] not in allowed:
                errors.append(f"{where}: {key} {f[key]!r} not in {sorted(allowed)}")
        if not isinstance(f["topic"], str) or not f["topic"].strip():
            errors.append(f"{where}: topic must be a non-empty string")
        if not isinstance(f["owner"], str) or not OWNER_RE.match(f["owner"]):
            errors.append(f"{where}: owner {f['owner']!r} must be a bot ID like fx-115 (never a name)")
        hyp = f["hypothesis"]
        if not isinstance(hyp, str) or not hyp.strip():
            errors.append(f"{where}: hypothesis must be a non-empty string")
        finding_text = f["finding"]
        spoken: list[str] = []
        if not isinstance(finding_text, str) or not finding_text.strip():
            errors.append(f"{where}: finding must be a non-empty string")
        else:
            spoken.append(finding_text)
            n_words = len(finding_text.split())
            if n_words > MAX_FINDING_WORDS:
                errors.append(f"{where}: finding has {n_words} words (max {MAX_FINDING_WORDS})")
        stats = f["key_stats"]
        if (not isinstance(stats, list) or not 1 <= len(stats) <= MAX_KEY_STATS
                or not all(isinstance(x, str) and x.strip() for x in stats)):
            errors.append(f"{where}: key_stats must be a list of 1-{MAX_KEY_STATS} non-empty strings")
        else:
            spoken.extend(stats)
        for t in spoken:
            if MARKDOWN_RE.search(t):
                errors.append(f"{where}: no markdown allowed in finding or key_stats: {t!r}")
        conf = f["confidence"]
        if conf is not None and not isinstance(conf, (int, float, str)):
            errors.append(f"{where}: confidence must be a number, string or null")
        if _as_date(f["run_date"]) is None:
            errors.append(f"{where}: run_date must be YYYY-MM-DD")
        vu = f["valid_until"]
        if vu is not None:
            d = _as_date(vu)
            if d is None:
                errors.append(f"{where}: valid_until must be YYYY-MM-DD or null")
            elif d < today:
                warnings.append(f"{where}: valid_until {d} is in the past; re-check and re-run")
        if f["people"] != []:
            errors.append(f"{where}: people must be [] (studies here should not name people)")
        if not isinstance(f["links_to"], list):
            errors.append(f"{where}: links_to must be a list")

        src = f["source_file"]
        nums = f["numbers"]
        if not isinstance(nums, list) or not all(isinstance(n, str) and n for n in nums):
            errors.append(f"{where}: numbers must be a list of non-empty strings")
            continue
        backed = {tok for n in nums for tok in NUM_TOKEN_RE.findall(n)}
        for t in spoken:
            for tok in NUM_TOKEN_RE.findall(t):
                if tok not in backed:
                    errors.append(f"{where}: number {tok!r} in {t!r} is not in numbers")
        if not isinstance(src, str) or not src.startswith(name + "/"):
            errors.append(f"{where}: source_file {src!r} must be a file inside {name}/")
            continue
        sp = root / src
        if not sp.is_file():
            errors.append(f"{where}: source_file {src} not found")
            continue
        src_text = sp.read_text(encoding="utf-8")
        for n in nums:
            if n not in src_text:
                errors.append(f"{where}: number {n!r} not found verbatim in {src}")

    # links must resolve (fw-* ids live in fed-watchers and are format-checked only)
    for name, f in findings:
        links = f.get("links_to")
        if not isinstance(links, list):
            continue
        for link in links:
            if isinstance(link, str) and FOREIGN_ID_RE.match(link):
                continue
            if link not in seen_ids:
                errors.append(f"{name} / {f.get('id')}: links_to {link!r} is not a known id")

    for folder in study_folders(root):
        if folder not in sections:
            errors.append(f"{folder}: has results but no section in FINDINGS.md")

    return errors, warnings


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--today", type=dt.date.fromisoformat, default=dt.date.today())
    a = p.parse_args(argv)
    errors, warnings = check(a.root, a.today)
    for w in warnings:
        print(f"WARN  {w}")
    for e in errors:
        print(f"ERROR {e}")
    if errors:
        print(f"FAIL: {len(errors)} error(s), {len(warnings)} warning(s)")
        return 1
    print(f"OK: FINDINGS.md passes ({len(warnings)} warning(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
