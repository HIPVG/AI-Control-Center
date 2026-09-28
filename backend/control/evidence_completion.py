"""Typed Result Adapter and criterion evaluation for the WC-05 boundary.

This module evaluates supplied fixture results only.  It does not execute a Day,
collect evidence, persist a run, or promote a whole Day to COMPLETE.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

from pydantic import ValidationError

from backend.control.evidence_registry import REGISTRY, EvidenceRegistry
from backend.models.local_llm_day import (
    DayCriterion,
    EvidenceRecord,
    EvidenceResultInput,
    LocalLLMDayContract,
    RunIntent,
)


class CompletionEvidenceEvaluator:
    """Convert strict provider results into run-bound validator-owned records."""

    def __init__(self, registry: EvidenceRegistry = REGISTRY) -> None:
        self.registry = registry

    def evaluate_criterion(
        self,
        *,
        intent: RunIntent,
        contract: LocalLLMDayContract,
        criterion_id: str,
        results: list[object],
    ) -> dict[str, object]:
        criterion = next(
            (item for item in contract.completion_criteria if item.criterion_id == criterion_id),
            None,
        )
        if criterion is None:
            return self._blocked(criterion_id, "CRITERION_NOT_FOUND", results)
        if intent.selected_day != contract.day:
            return self._blocked(criterion_id, "DAY_IDENTITY_MISMATCH", results)

        records: dict[str, EvidenceRecord] = {}
        outcomes: list[dict[str, object]] = []
        accepted_types: dict[str, str] = {}
        for raw in results:
            outcome, record = self._adapt(intent, contract, criterion, raw)
            outcomes.append(outcome)
            if record is not None and record.evidence_type not in accepted_types:
                records[record.record_id] = record
                accepted_types[record.evidence_type] = record.record_id

        required = set(criterion.required_evidence)
        satisfied = bool(required) and required == set(accepted_types)
        return {
            "run_id": intent.run_id,
            "criterion_id": criterion_id,
            "status": "CRITERION_COMPLETE" if satisfied else "INCOMPLETE",
            "criterion_satisfied": satisfied,
            "evidence_record_ids": accepted_types,
            "evidence_records": {
                key: value.model_dump(mode="json") for key, value in records.items()
            },
            "missing_evidence_types": sorted(required - set(accepted_types)),
            "adapter_outcomes": outcomes,
            "day_execution_started": False,
        }

    def _adapt(
        self,
        intent: RunIntent,
        contract: LocalLLMDayContract,
        criterion: DayCriterion,
        raw: object,
    ) -> tuple[dict[str, object], EvidenceRecord | None]:
        try:
            result = EvidenceResultInput.model_validate(raw)
        except ValidationError as exc:
            return ({"accepted": False, "reason_code": "MALFORMED_RESULT", "details": exc.error_count()}, None)
        if result.run_id != intent.run_id:
            return ({"accepted": False, "reason_code": "RUN_ID_MISMATCH", "evidence_type": result.evidence_type}, None)
        if result.criterion_id != criterion.criterion_id:
            return ({"accepted": False, "reason_code": "CRITERION_ID_MISMATCH", "evidence_type": result.evidence_type}, None)
        if result.evidence_type not in criterion.required_evidence:
            return ({"accepted": False, "reason_code": "EVIDENCE_TYPE_NOT_REQUIRED", "evidence_type": result.evidence_type}, None)
        if result.configuration_fingerprint != intent.config_fingerprint:
            return ({"accepted": False, "reason_code": "CONFIGURATION_FINGERPRINT_MISMATCH", "evidence_type": result.evidence_type}, None)

        envelope = {
            "evidence_type": result.evidence_type,
            "value": result.value,
            "source": result.provider_id,
            "verified": True,
            "validation": {"passed": True, "validator": f"evidence-registry:{result.evidence_type}"},
        }
        valid = self.registry.validate(result.evidence_type, envelope)
        if not valid:
            return ({"accepted": False, "reason_code": "EVIDENCE_VALIDATION_FAILED", "evidence_type": result.evidence_type}, None)

        record_id = hashlib.sha256(json.dumps({
            "run_id": intent.run_id,
            "criterion_id": criterion.criterion_id,
            "evidence_type": result.evidence_type,
            "provider_id": result.provider_id,
            "source_fingerprint": result.source_fingerprint,
            "value": result.value,
        }, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[:32]
        record = EvidenceRecord(
            record_id=record_id,
            run_id=intent.run_id,
            criterion_id=criterion.criterion_id,
            project_id="local_llm_lab",
            day=contract.day,
            contract_version=contract.version,
            evidence_type=result.evidence_type,
            provider_id=result.provider_id,
            provider_version=result.provider_version,
            validator_id=f"evidence-registry:{result.evidence_type}",
            validator_version="v1",
            source_paths=result.source_paths,
            source_revision=result.source_revision,
            source_fingerprint=result.source_fingerprint,
            configuration_fingerprint=result.configuration_fingerprint,
            collected_at=datetime.now(timezone.utc),
            value=result.value,
            status="VALID",
            validator_result=True,
            compatibility_result=True,
            retained_artifact_reference=result.retained_artifact_reference,
            source_hashes=result.source_hashes,
            observation_fingerprint=result.source_fingerprint,
        )
        return ({"accepted": True, "reason_code": "VALIDATED", "evidence_type": result.evidence_type, "record_id": record_id}, record)

    @staticmethod
    def _blocked(criterion_id: str, reason_code: str, results: list[object]) -> dict[str, object]:
        return {
            "run_id": None,
            "criterion_id": criterion_id,
            "status": "INPUT_BLOCKED",
            "criterion_satisfied": False,
            "evidence_record_ids": {},
            "evidence_records": {},
            "missing_evidence_types": [],
            "adapter_outcomes": [{"accepted": False, "reason_code": reason_code}] if results else [],
            "day_execution_started": False,
        }
