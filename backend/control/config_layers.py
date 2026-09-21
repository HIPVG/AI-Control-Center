"""Deterministic, local-only configuration overrides for runtime settings."""

from collections.abc import Mapping
from pathlib import Path
from typing import Any


def local_override_path(path: Path) -> Path:
    return path.with_name(f"{path.stem}.local{path.suffix}")


def load_yaml_layers(path: Path) -> dict[str, Any]:
    """Merge a tracked default with an ignored local override, in that order."""
    import yaml

    merged: dict[str, Any] = {}
    for candidate in (path, local_override_path(path)):
        if not candidate.exists():
            continue
        loaded = yaml.safe_load(candidate.read_text(encoding="utf-8")) or {}
        if not isinstance(loaded, Mapping):
            raise ValueError(f"configuration root must be a mapping: {candidate.name}")
        merged = _deep_merge(merged, dict(loaded))
    return merged


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = dict(base)
    for key, value in override.items():
        if isinstance(value, Mapping) and isinstance(result.get(key), Mapping):
            result[key] = _deep_merge(dict(result[key]), dict(value))
        else:
            result[key] = value
    return result
