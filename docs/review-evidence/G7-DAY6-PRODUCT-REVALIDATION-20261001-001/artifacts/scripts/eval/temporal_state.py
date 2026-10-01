"""Fail-closed validation for the planned/actual/forecast state boundary."""
from __future__ import annotations

from datetime import datetime
from typing import Any


TIME_KINDS = ("planned", "actual", "forecast")
REQUIRED_FACT_FIELDS = ("fact_id", "value", "effective_time", "source_record_ids")


def _parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def validate_temporal_state(state: Any) -> list[dict[str, str]]:
    """Return deterministic errors; accept only complete, provenance-backed state."""
    errors: list[dict[str, str]] = []
    if not isinstance(state, dict):
        return [{"path": "$", "code": "STATE_NOT_OBJECT"}]
    if set(state) != {"snapshot_time", *TIME_KINDS}:
        errors.append({"path": "$", "code": "INVALID_TOP_LEVEL_FIELDS"})

    snapshot = _parse_time(state.get("snapshot_time"))
    if snapshot is None:
        errors.append({"path": "snapshot_time", "code": "INVALID_SNAPSHOT_TIME"})

    for kind in TIME_KINDS:
        facts = state.get(kind)
        if not isinstance(facts, list):
            errors.append({"path": kind, "code": "FACT_SET_NOT_ARRAY"})
            continue
        seen: set[str] = set()
        for index, fact in enumerate(facts):
            path = f"{kind}[{index}]"
            if not isinstance(fact, dict):
                errors.append({"path": path, "code": "FACT_NOT_OBJECT"})
                continue
            if set(fact) != set(REQUIRED_FACT_FIELDS):
                errors.append({"path": path, "code": "INVALID_FACT_FIELDS"})
                continue
            fact_id = fact.get("fact_id")
            if not isinstance(fact_id, str) or not fact_id:
                errors.append({"path": f"{path}.fact_id", "code": "INVALID_FACT_ID"})
            elif fact_id in seen:
                errors.append({"path": f"{path}.fact_id", "code": "DUPLICATE_FACT_ID"})
            else:
                seen.add(fact_id)
            effective = _parse_time(fact.get("effective_time"))
            if effective is None:
                errors.append({"path": f"{path}.effective_time", "code": "INVALID_EFFECTIVE_TIME"})
            elif snapshot is not None and kind == "actual" and effective > snapshot:
                errors.append({"path": f"{path}.effective_time", "code": "ACTUAL_AFTER_SNAPSHOT"})
            sources = fact.get("source_record_ids")
            if (not isinstance(sources, list) or not sources
                    or any(not isinstance(item, str) or not item for item in sources)):
                errors.append({"path": f"{path}.source_record_ids", "code": "INVALID_SOURCE_RECORD_IDS"})
    return errors


def is_valid_temporal_state(state: Any) -> bool:
    """Convenience predicate for callers that need a strict admission gate."""
    return not validate_temporal_state(state)
