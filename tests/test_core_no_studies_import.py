"""Architectural gate: core/ must not import the studies tree."""

from __future__ import annotations

import ast
from pathlib import Path

from core.config_io import ROOT

CORE = ROOT / "core"
FORBIDDEN_PREFIXES = (
    "src.",  # study package (studies/*/src)
    "studies.",
)


def _imports_from(node: ast.AST) -> list[str]:
    out: list[str] = []
    if isinstance(node, ast.Import):
        for alias in node.names:
            out.append(alias.name)
    elif isinstance(node, ast.ImportFrom):
        if node.module:
            out.append(node.module)
    return out


def test_core_does_not_import_studies_or_study_src():
    hits: list[str] = []
    for path in sorted(CORE.rglob("*.py")):
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            for name in _imports_from(node):
                if name == "src" or name.startswith(FORBIDDEN_PREFIXES):
                    rel = path.relative_to(ROOT)
                    hits.append(f"{rel}: imports {name}")
                if name == "studies" or name.startswith("studies."):
                    rel = path.relative_to(ROOT)
                    hits.append(f"{rel}: imports {name}")
    assert hits == [], "core/ must not import studies/ or study src:\n" + "\n".join(hits)
