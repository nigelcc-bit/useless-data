"""Load frozen YAML configs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config"


def load_yaml(name: str) -> dict[str, Any]:
    path = CONFIG / name
    with path.open() as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise TypeError(f"{path} must contain a mapping")
    return data


def fixtures() -> dict[str, Any]:
    return load_yaml("fixtures.yaml")


def episodes() -> dict[str, Any]:
    return load_yaml("episodes.yaml")


def universe() -> dict[str, Any]:
    return load_yaml("universe.yaml")
