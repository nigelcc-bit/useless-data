#!/usr/bin/env python3
"""Scaffold a new study from studies/_template/.

Usage:
    python scripts/new_study.py <slug>

Creates studies/YYYY-MM-<slug>/ from the template (UTC year-month).
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "studies" / "_template"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "slug",
        help="short kebab-case study slug (e.g. flush-or-regime)",
    )
    args = parser.parse_args(argv)
    slug = args.slug.strip().lower().replace("_", "-")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
        print(f"invalid slug: {args.slug!r} (use kebab-case)", file=sys.stderr)
        return 2
    if slug.startswith("20") and re.match(r"^\d{4}-\d{2}-", slug):
        print("pass the slug only; YYYY-MM- is added automatically", file=sys.stderr)
        return 2

    stamp = datetime.now(timezone.utc).strftime("%Y-%m")
    dest = ROOT / "studies" / f"{stamp}-{slug}"
    if dest.exists():
        print(f"already exists: {dest}", file=sys.stderr)
        return 1
    if not TEMPLATE.is_dir():
        print(f"missing template: {TEMPLATE}", file=sys.stderr)
        return 1

    shutil.copytree(TEMPLATE, dest)
    readme = dest / "README.md"
    if readme.exists():
        text = readme.read_text()
        text = text.replace("{{STUDY_SLUG}}", slug).replace("{{STUDY_DIR}}", dest.name)
        readme.write_text(text)
    print(dest.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
