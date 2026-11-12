"""Load frozen YAML configs (reference + active study)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = Path(__file__).resolve().parent / "reference"
DEFAULT_STUDY = ROOT / "studies" / "2026-11-flush-or-regime"


def study_root() -> Path:
    """Active study directory (override with AI_STUDY_DIR)."""
    override = os.environ.get("AI_STUDY_DIR")
    if override:
        return Path(override).resolve()
    return DEFAULT_STUDY


def study_config_dir() -> Path:
    return study_root() / "config"


def study_outputs() -> Path:
    return study_root() / "outputs"


def load_yaml_path(path: Path) -> dict[str, Any]:
    with path.open() as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise TypeError(f"{path} must contain a mapping")
    return data


def pins() -> dict[str, Any]:
    return load_yaml_path(study_config_dir() / "pins.yaml")


def reference_path(key: str) -> Path:
    """Resolve a versioned reference YAML via the active study's pins.yaml."""
    ref = pins().get("reference", {})
    name = ref.get(key)
    if not name:
        raise KeyError(f"pins.yaml missing reference.{key}")
    path = REFERENCE / f"{name}.yaml"
    if not path.exists():
        raise FileNotFoundError(path)
    return path


def load_reference(key: str) -> dict[str, Any]:
    return load_yaml_path(reference_path(key))


def load_study_yaml(name: str) -> dict[str, Any]:
    path = study_config_dir() / name
    return load_yaml_path(path)


def fixtures() -> dict[str, Any]:
    return load_study_yaml("fixtures.yaml")


def episodes() -> dict[str, Any]:
    return load_study_yaml("episodes.yaml")


def universe() -> dict[str, Any]:
    return load_reference("universe")
