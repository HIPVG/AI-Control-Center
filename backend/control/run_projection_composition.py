"""RI-02 read-time composition of one exact persisted run projection."""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import ValidationError

from backend.control.local_llm_day_program import LocalLLMDayProgram
from backend.control.preflight_authority import PreflightFactStore
from backend.control.run_read_model import (
    AdmissionProjection,
    CriterionProjection,
    HumanDecisionProjection,
    ReviewProjection,
    RunReadModel,
    RuntimeObservation,
    empty_run_read_model,
)
from backend.control.run_store import RunStore
from backend.control.run_telemetry_store import RunTelemetryStore


def build_run_read_model(
    *,
    run_store: RunStore,
    telemetry_store: RunTelemetryStore,
    preflight_fact_store: PreflightFactStore | None = None,
    program: LocalLLMDayProgram,
    at: datetime | None = None,
    review: ReviewProjection | None = None,
    human_decision: HumanDecisionProjection | None = None,
    runtime_observation: RuntimeObservation | None = None,
) -> RunReadModel:
    """Rebuild current/history at read time; mismatched optional data fails closed."""
    projected_at = at or datetime.now(timezone.utc)
    errors: list[str] = []
    try:
        current = run_store.current()
        records = run_store.records()
    except (OSError, ValueError, ValidationError):
        return empty_run_read_model(
            at=projected_at, projection_errors=("RUN_STORE_UNREADABLE",)
        )
    if current is None:
        return empty_run_read_model(at=projected_at)

    run_id = current.intent.run_id
    history = tuple(item for item in records if item.intent.run_id != run_id)
    try:
        versions = run_store.versions(run_id)
    except (OSError, ValueError, ValidationError):
        return empty_run_read_model(
            at=projected_at,
            projection_errors=("RUN_VERSION_HISTORY_UNREADABLE",),
        )
    initial = versions[0] if versions else current
    admission = AdmissionProjection(
        run_id=run_id,
        status="BLOCKED" if initial.control.blocker else "ADMISSIBLE",
        reason_code=initial.control.blocker,
        observed_at=initial.control.updated_at,
        source="initial persisted RunControl",
    )

    criteria: tuple[CriterionProjection, ...] = ()
    snapshot = program.snapshot
    if snapshot.run_id is None:
        errors.append("DAY_SNAPSHOT_RUN_ID_UNKNOWN")
    elif snapshot.run_id != run_id:
        errors.append("DAY_SNAPSHOT_RUN_ID_MISMATCH")
    elif snapshot.contract is None:
        errors.append("DAY_CONTRACT_MISSING")
    elif snapshot.selected_day != current.intent.selected_day:
        errors.append("DAY_IDENTITY_MISMATCH")
    elif program._contract_fingerprint(snapshot.contract) != current.intent.contract_fingerprint:
        errors.append("CONTRACT_FINGERPRINT_MISMATCH")
    else:
        criteria = tuple(
            CriterionProjection(
                run_id=run_id,
                criterion_id=item.criterion_id,
                satisfied=item.satisfied,
                evidence_record_ids=tuple(sorted(item.evidence_record_ids.values())),
                observed_at=snapshot.updated_at,
                source="run-bound Day snapshot and Evidence evaluator",
            )
            for item in snapshot.contract.completion_criteria
        )

    telemetry = None
    try:
        telemetry = telemetry_store.get(run_id)
    except (OSError, ValueError, ValidationError):
        errors.append("TELEMETRY_UNREADABLE_OR_MISMATCHED")

    preflight_fact = None
    if preflight_fact_store is not None:
        try:
            preflight_fact = preflight_fact_store.get(run_id)
        except (OSError, ValueError, ValidationError):
            errors.append("PREFLIGHT_FACT_UNREADABLE_OR_MISMATCHED")

    try:
        return RunReadModel(
            current=current,
            history=history,
            admission=admission,
            preflight_fact=preflight_fact,
            criteria=criteria,
            review=review,
            telemetry=telemetry,
            human_decision=human_decision,
            runtime_observation=runtime_observation,
            projection_errors=tuple(errors),
            projected_at=projected_at,
            source="read-time persisted run composition",
        )
    except ValidationError:
        # Optional projections supplied by later controllers never displace the
        # authoritative current run when their identity is wrong.
        return RunReadModel(
            current=current,
            history=history,
            admission=admission,
            preflight_fact=preflight_fact,
            criteria=criteria,
            projection_errors=tuple((*errors, "OPTIONAL_PROJECTION_RUN_ID_MISMATCH")),
            projected_at=projected_at,
            source="read-time persisted run composition (optional data rejected)",
        )
