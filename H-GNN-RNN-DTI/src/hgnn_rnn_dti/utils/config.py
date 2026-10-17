"""Minimal YAML config loader (nested dict)."""
from __future__ import annotations

import copy
from pathlib import Path

import yaml


def load_config(path: str | Path) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def clone_config(cfg: dict) -> dict:
    """Deep copy so experiment variants (e.g. fusion sweep) don't mutate shared state."""
    return copy.deepcopy(cfg)
