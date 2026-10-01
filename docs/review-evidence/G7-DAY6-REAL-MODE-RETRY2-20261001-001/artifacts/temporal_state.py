"""Fail-closed validation for the Day 6 temporal-state boundary."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
import json
from typing import Any, Iterable, Mapping


TIME_PARTITIONS = ("planned_time", "actual_time", "forecast_time", "snapshot_time")
FACT_FIELDS = {"fact_id", "value", "unit", "source_record_ids"}
PARTITION_FIELDS = {"as_of", "facts"}


def load_schema() -> dict[str, Any]:
    """Load the versioned schema kept beside the deterministic boundary."""
    root = Path(__file__).resolve().parents[2]
    return json.loads((root / "schemas" / "temporal-state.json").read_text(encoding="utf-8"))


def _is_timestamp(value: Any) -> bool:
    if not isinstance(value, str) or not value:
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None


def _required_pairs(required_facts: Mapping[str, str] | Iterable[str] | None) -> list[tuple[str | None, str]]:
    if required_facts is None:
        return []
    if isinstance(required_facts, Mapping):
        return [(partition, fact_id) for fact_id, partition in required_facts.items()]
    return [(None, fact_id) for fact_id in required_facts]


def validate_temporal_state(
    value: Any, required_facts: Mapping[str, str] | Iterable[str] | None = None
) -> dict[str, Any]:
    """Validate temporal separation and provenance without inferring missing facts.

    ``required_facts`` may be an iterable of fact IDs (required in any partition)
    or a mapping of fact ID to its required partition.  Any malformed or missing
    required value produces ``FAILED``; callers must not substitute a plan or a
    forecast for an actual fact.
    """
    errors: list[dict[str, str]] = []
    seen: dict[str, set[str]] = {partition: set() for partition in TIME_PARTITIONS}
    if not isinstance(value, dict):
        return {"validation_status": "FAILED", "errors": [{"code": "ROOT_NOT_OBJECT"}],
                "facts_by_partition": seen}
    actual_fields = set(value)
    if actual_fields != set(TIME_PARTITIONS):
        errors.append({"code": "TEMPORAL_PARTITIONS_INVALID"})

    for partition in TIME_PARTITIONS:
        payload = value.get(partition)
        if not isinstance(payload, dict) or set(payload) != PARTITION_FIELDS:
            errors.append({"code": "PARTITION_SCHEMA", "partition": partition})
            continue
        if not _is_timestamp(payload.get("as_of")):
            errors.append({"code": "INVALID_AS_OF", "partition": partition})
        facts = payload.get("facts")
        if not isinstance(facts, list):
            errors.append({"code": "FACTS_NOT_ARRAY", "partition": partition})
            continue
        for fact in facts:
            if not isinstance(fact, dict) or set(fact) != FACT_FIELDS:
                errors.append({"code": "FACT_SCHEMA", "partition": partition})
                continue
            fact_id = fact.get("fact_id")
            sources = fact.get("source_record_ids")
            if not isinstance(fact_id, str) or not fact_id:
                errors.append({"code": "INVALID_FACT_ID", "partition": partition})
                continue
            if fact_id in seen[partition]:
                errors.append({"code": "DUPLICATE_FACT_ID", "partition": partition})
            seen[partition].add(fact_id)
            if not isinstance(fact.get("unit"), str):
                errors.append({"code": "INVALID_UNIT", "partition": partition})
            if isinstance(fact.get("value"), (dict, list)):
                errors.append({"code": "INVALID_FACT_VALUE", "partition": partition})
            if not isinstance(sources, list) or not sources or any(not isinstance(item, str) or not item for item in sources):
                errors.append({"code": "MISSING_PROVENANCE", "partition": partition})

    for required_partition, fact_id in _required_pairs(required_facts):
        if required_partition is not None and required_partition not in TIME_PARTITIONS:
            errors.append({"code": "INVALID_REQUIRED_PARTITION", "partition": str(required_partition)})
        elif required_partition is not None and fact_id not in seen[required_partition]:
            errors.append({"code": "MISSING_REQUIRED_FACT", "partition": required_partition})
        elif required_partition is None and not any(fact_id in ids for ids in seen.values()):
            errors.append({"code": "MISSING_REQUIRED_FACT"})

    return {"validation_status": "SUCCESS" if not errors else "FAILED",
            "errors": errors, "facts_by_partition": seen}
