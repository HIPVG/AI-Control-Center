"""RI-01 same-run adapters for Evidence, recovery, review and human decisions.

The accepted WC controllers remain the owners of their decisions. This module
only binds their outputs to the durable RunRecord created by RI-00; it does not
execute a Day or introduce another execution state machine.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from threading import RLock
from typing import Callable

from backend.control.evidence_completion import CompletionEvidenceEvaluator
from backend.control.human_decision import DecisionRequest, HumanDecisionControl, HumanResponse
from backend.control.local_llm_day_program import LocalLLMDayProgram
from backend.control.repair_recovery import RepairRecoveryController
from backend.control.review_continuation import ReviewContinuationControl
from backend.control.review_control import ReviewControl, ReviewControlState
from backend.control.run_store import RunStore
from backend.models.local_llm_day import EvidenceRecord, LocalLLMDayState, RunControl, RunRecord


class RunExecutionComposition:
    """Project accepted controller results onto exactly one durable run."""

    def __init__(
        self,
        program: LocalLLMDayProgram,
        store: RunStore,
        *,
        evaluator: CompletionEvidenceEvaluator | None = None,
        clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    ) -> None:
        self.program = program
        self.store = store
        self.evaluator = evaluator or CompletionEvidenceEvaluator()
        self.clock = clock
        self._lock = RLock()
        self._repairs: dict[str, RepairRecoveryController] = {}
        self._reviews: dict[str, ReviewControl] = {}
        self._report_owners: dict[str, str] = {}
        self._human_controls: dict[str, HumanDecisionControl] = {}
        self._human_requests: dict[str, DecisionRequest] = {}
        self._decision_owners: dict[str, str] = {}

    def project_day_state(self, run_id: str) -> dict[str, object]:
        """Copy the existing Day controller state into RunControl after identity checks."""
        with self._lock:
            record = self._record(run_id)
            current = self.store.current()
            if current is None or current.intent.run_id != run_id:
                return self._rejected(record, "RUN_NOT_CURRENT")
            snapshot = self.program.snapshot
            if snapshot.run_id != run_id:
                return self._rejected(record, "DAY_SNAPSHOT_RUN_ID_MISMATCH")
            if snapshot.selected_day != record.intent.selected_day:
                return self._rejected(record, "DAY_IDENTITY_MISMATCH")
            if snapshot.contract is None:
                return self._rejected(record, "DAY_CONTRACT_MISSING")
            fingerprint = self.program._contract_fingerprint(snapshot.contract)
            if fingerprint != record.intent.contract_fingerprint:
                return self._rejected(record, "CONTRACT_FINGERPRINT_MISMATCH")
            if snapshot.state == LocalLLMDayState.COMPLETE and not self._completion_ready(record):
                return self._rejected(record, "VALIDATOR_EVIDENCE_INCOMPLETE")
            if snapshot.state == LocalLLMDayState.COMPLETE and self._required_review_pending(record):
                return self._rejected(record, "REQUIRED_REVIEW_UNVERIFIED")
            blocker = snapshot.authority_blocker.reason_code if snapshot.authority_blocker else snapshot.stop_reason
            updated = self._advance(
                record,
                snapshot.state,
                snapshot.activity or "Continue the same run.",
                blocker=blocker,
                resume_target="PREFLIGHT" if blocker else None,
            )
            return self._accepted(updated)

    def evaluate_criterion(
        self, run_id: str, *, criterion_id: str, results: list[object]
    ) -> dict[str, object]:
        """Validate provider results and retain only records bound to this run."""
        with self._lock:
            record = self._record(run_id)
            snapshot = self.program.snapshot
            if snapshot.run_id != run_id:
                return self._rejected(record, "DAY_SNAPSHOT_RUN_ID_MISMATCH")
            contract = snapshot.contract
            if contract is None or contract.day != record.intent.selected_day:
                return self._rejected(record, "DAY_CONTRACT_MISMATCH")
            if self.program._contract_fingerprint(contract) != record.intent.contract_fingerprint:
                return self._rejected(record, "CONTRACT_FINGERPRINT_MISMATCH")
            evaluation = self.evaluator.evaluate_criterion(
                intent=record.intent,
                contract=contract,
                criterion_id=criterion_id,
                results=results,
            )
            if not evaluation["criterion_satisfied"]:
                return evaluation
            criterion = next(item for item in contract.completion_criteria if item.criterion_id == criterion_id)
            records = {
                key: EvidenceRecord.model_validate(value)
                for key, value in evaluation["evidence_records"].items()
            }
            if any(item.run_id != run_id for item in records.values()):
                return self._rejected(record, "EVIDENCE_RUN_ID_MISMATCH")
            self.program.snapshot.evidence_store.update(records)
            criterion.evidence_record_ids.update(evaluation["evidence_record_ids"])
            criterion.satisfied = True
            contract.satisfied_criteria = [
                item.criterion_id for item in contract.completion_criteria if item.satisfied
            ]
            contract.remaining_gaps = [
                item.criterion_id for item in contract.completion_criteria if not item.satisfied
            ]
            self.program._save()
            return evaluation

    def bind_day_evidence(self, run_id: str) -> dict[str, object]:
        """Create strict per-criterion records from already validated Day evidence.

        The Day controller may retain nullable legacy records for compatibility.
        Product completion never relabels those records: it revalidates their value
        and provenance through the strict Result Adapter under server-owned run and
        criterion identities, then applies all bindings atomically to the snapshot.
        """
        with self._lock:
            record = self._record(run_id)
            current = self.store.current()
            if current is None or current.intent.run_id != run_id:
                return self._rejected(record, "RUN_NOT_CURRENT")
            snapshot = self.program.snapshot
            if snapshot.run_id != run_id:
                return self._rejected(record, "DAY_SNAPSHOT_RUN_ID_MISMATCH")
            contract = snapshot.contract
            if contract is None or contract.day != record.intent.selected_day:
                return self._rejected(record, "DAY_CONTRACT_MISMATCH")
            if self.program._contract_fingerprint(contract) != record.intent.contract_fingerprint:
                return self._rejected(record, "CONTRACT_FINGERPRINT_MISMATCH")

            pending: list[tuple[object, dict[str, object], dict[str, EvidenceRecord]]] = []
            for criterion in contract.completion_criteria:
                results: list[dict[str, object]] = []
                for evidence_type in criterion.required_evidence:
                    source_id = criterion.evidence_record_ids.get(evidence_type)
                    source = snapshot.evidence_store.get(source_id) if source_id else None
                    if not self.program._evidence_record_valid(evidence_type, source):
                        return self._rejected(record, "DAY_EVIDENCE_SOURCE_INVALID")
                    assert source is not None
                    if source.day != contract.day or source.contract_version != contract.version:
                        return self._rejected(record, "DAY_EVIDENCE_SOURCE_CONTRACT_MISMATCH")
                    legacy_unbound = source.run_id is None and source.criterion_id is None
                    exact_binding = (
                        source.run_id == run_id
                        and source.criterion_id == criterion.criterion_id
                    )
                    if not legacy_unbound and not exact_binding:
                        return self._rejected(record, "DAY_EVIDENCE_SOURCE_BINDING_MISMATCH")
                    if (
                        exact_binding
                        and source.configuration_fingerprint != record.intent.config_fingerprint
                    ):
                        return self._rejected(record, "DAY_EVIDENCE_SOURCE_CONFIG_MISMATCH")
                    results.append({
                        "run_id": run_id,
                        "criterion_id": criterion.criterion_id,
                        "evidence_type": evidence_type,
                        "provider_id": source.provider_id,
                        "provider_version": source.provider_version,
                        "source_fingerprint": source.source_fingerprint,
                        "configuration_fingerprint": record.intent.config_fingerprint,
                        "value": source.value,
                        "source_paths": source.source_paths,
                        "source_revision": source.source_revision,
                        "source_hashes": source.source_hashes,
                        "retained_artifact_reference": source.retained_artifact_reference,
                    })
                evaluation = self.evaluator.evaluate_criterion(
                    intent=record.intent,
                    contract=contract,
                    criterion_id=criterion.criterion_id,
                    results=results,
                )
                if not evaluation["criterion_satisfied"]:
                    return self._rejected(record, "DAY_EVIDENCE_BINDING_INCOMPLETE")
                records = {
                    key: EvidenceRecord.model_validate(value)
                    for key, value in evaluation["evidence_records"].items()
                }
                if any(
                    item.run_id != run_id or item.criterion_id != criterion.criterion_id
                    for item in records.values()
                ):
                    return self._rejected(record, "EVIDENCE_IDENTITY_MISMATCH")
                pending.append((criterion, evaluation, records))

            for criterion, evaluation, records in pending:
                snapshot.evidence_store.update(records)
                criterion.evidence_record_ids = dict(evaluation["evidence_record_ids"])
                criterion.evidence = dict(evaluation["evidence_record_ids"])
                criterion.satisfied = True
            contract.satisfied_criteria = [
                criterion.criterion_id for criterion in contract.completion_criteria
                if criterion.satisfied
            ]
            contract.remaining_gaps = [
                criterion.criterion_id for criterion in contract.completion_criteria
                if not criterion.satisfied
            ]
            self.program._save()
            return {
                "outcome": "ACCEPTED",
                "run_id": run_id,
                "selected_day": record.intent.selected_day,
                "criterion_ids": [item[0].criterion_id for item in pending],
                "evidence_record_ids": {
                    item[0].criterion_id: dict(item[1]["evidence_record_ids"])
                    for item in pending
                },
                "day_execution_started": False,
            }

    def verify_bound_day_evidence(self, run_id: str) -> dict[str, object]:
        """Verify an already-bound completion snapshot without mutating or saving it."""
        with self._lock:
            record = self._record(run_id)
            current = self.store.current()
            if current is None or current.intent.run_id != run_id:
                return self._rejected(record, "RUN_NOT_CURRENT")
            snapshot = self.program.snapshot
            contract = snapshot.contract
            if snapshot.run_id != run_id:
                return self._rejected(record, "DAY_SNAPSHOT_RUN_ID_MISMATCH")
            if contract is None or contract.day != record.intent.selected_day:
                return self._rejected(record, "DAY_CONTRACT_MISMATCH")
            if self.program._contract_fingerprint(contract) != record.intent.contract_fingerprint:
                return self._rejected(record, "CONTRACT_FINGERPRINT_MISMATCH")
            for criterion in contract.completion_criteria:
                results: list[dict[str, object]] = []
                for evidence_type in criterion.required_evidence:
                    source_id = criterion.evidence_record_ids.get(evidence_type)
                    source = snapshot.evidence_store.get(source_id) if source_id else None
                    if not self.program._evidence_record_valid(evidence_type, source):
                        return self._rejected(record, "BOUND_EVIDENCE_INVALID")
                    assert source is not None
                    if (
                        source.run_id != run_id
                        or source.criterion_id != criterion.criterion_id
                        or source.day != contract.day
                        or source.contract_version != contract.version
                        or source.configuration_fingerprint != record.intent.config_fingerprint
                    ):
                        return self._rejected(record, "BOUND_EVIDENCE_IDENTITY_MISMATCH")
                    results.append({
                        "run_id": run_id,
                        "criterion_id": criterion.criterion_id,
                        "evidence_type": evidence_type,
                        "provider_id": source.provider_id,
                        "provider_version": source.provider_version,
                        "source_fingerprint": source.source_fingerprint,
                        "configuration_fingerprint": source.configuration_fingerprint,
                        "value": source.value,
                        "source_paths": source.source_paths,
                        "source_revision": source.source_revision,
                        "source_hashes": source.source_hashes,
                        "retained_artifact_reference": source.retained_artifact_reference,
                    })
                evaluation = self.evaluator.evaluate_criterion(
                    intent=record.intent,
                    contract=contract,
                    criterion_id=criterion.criterion_id,
                    results=results,
                )
                if (
                    not evaluation["criterion_satisfied"]
                    or evaluation["evidence_record_ids"] != criterion.evidence_record_ids
                ):
                    return self._rejected(record, "BOUND_EVIDENCE_CONFLICT")
            return {"outcome": "ACCEPTED", "run_id": run_id, "day_execution_started": False}

    def begin_repair(self, run_id: str, *, allowed_paths: set[str]) -> dict[str, object]:
        with self._lock:
            record = self._record(run_id)
            self._repairs[run_id] = RepairRecoveryController(record, allowed_paths=allowed_paths)
            return self._accepted(record)

    def record_repair_attempt(self, run_id: str, raw: object) -> dict[str, object]:
        with self._lock:
            controller = self._repairs.get(run_id)
            if controller is None:
                return self._rejected(self._record(run_id), "REPAIR_EPISODE_NOT_BOUND")
            before = controller.record.control
            result = controller.record_attempt(raw)
            self._persist_controller_record(controller, before)
            return result

    def apply_repair_review(self, run_id: str, raw: object) -> dict[str, object]:
        with self._lock:
            controller = self._repairs.get(run_id)
            if controller is None:
                return self._rejected(self._record(run_id), "REPAIR_EPISODE_NOT_BOUND")
            before = controller.record.control
            result = controller.apply_review(raw)
            self._persist_controller_record(controller, before)
            return result

    def request_review(self, run_id: str, report_id: str, *, at: datetime) -> dict[str, object]:
        with self._lock:
            record = self._record(run_id)
            owner = self._report_owners.get(report_id)
            if owner is not None and owner != run_id:
                return self._rejected(record, "REPORT_ID_BOUND_TO_OTHER_RUN")
            control = self._reviews.setdefault(run_id, ReviewControl())
            result = control.send(report_id, at=at)
            if result["outcome"] != "ACCEPTED":
                return result
            self._report_owners[report_id] = run_id
            self._advance(
                record,
                LocalLLMDayState.HUMAN_ACTION_REQUIRED,
                "Await the exactly matching reviewer response.",
                blocker="REVIEW_RESPONSE_REQUIRED",
                resume_target="PREFLIGHT",
            )
            return {**result, "run_id": run_id, "selected_day": record.intent.selected_day}

    def apply_review_response(
        self,
        run_id: str,
        response: object,
        *,
        comment_id: str,
        at: datetime,
        exit_code: int,
        envelope_valid: bool,
        envelope_validation_reason: str,
        downstream_effect_id: str | None,
        observed_effect_id: str | None,
    ) -> dict[str, object]:
        """Apply one injected response only after correlation and effect readback."""
        with self._lock:
            record = self._record(run_id)
            control = self._reviews.get(run_id)
            if control is None:
                return self._rejected(record, "REVIEW_NOT_BOUND")
            received = control.receive(response, at=at, watcher_available=True)
            if received["outcome"] != "ACCEPTED":
                return {**received, "run_id": run_id}
            response_id = str(received["response_id"])
            applied = control.apply(response_id=response_id, at=self._after(at))
            if applied["outcome"] != "ACCEPTED":
                return {**applied, "run_id": run_id}
            continuation = ReviewContinuationControl(
                report_id=str(received["report_id"]), response_id=response_id,
                comment_id=comment_id, received_at=at,
            )
            continuation.begin(
                report_id=str(received["report_id"]), response_id=response_id,
                at=self._after(at, 2), actor="injected-g6-fixture",
            )
            effect = continuation.finish(
                exit_code=exit_code, envelope_valid=envelope_valid,
                envelope_validation_reason=envelope_validation_reason,
                downstream_effect_id=downstream_effect_id, at=self._after(at, 3),
            )
            if effect["state"] != "APPLIED" or not observed_effect_id:
                return {"run_id": run_id, "review": applied, "continuation": effect}
            verified_effect = continuation.verify(
                observed_effect_id=observed_effect_id, at=self._after(at, 4)
            )
            if verified_effect["state"] != "VERIFIED":
                return {"run_id": run_id, "review": applied, "continuation": verified_effect}
            verified = control.verify(
                downstream_evidence_id=observed_effect_id, at=self._after(at, 5)
            )
            if verified["state"] == "VERIFIED":
                record = self._record(run_id)
                self._advance(
                    record, LocalLLMDayState.PREFLIGHT,
                    "Recheck the same run after the verified review effect.",
                )
            return {"run_id": run_id, "review": verified, "continuation": verified_effect}

    def bind_human_decision(self, run_id: str, request: DecisionRequest) -> dict[str, object]:
        with self._lock:
            record = self._record(run_id)
            owner = self._decision_owners.get(request.decision_id)
            if owner is not None and owner != run_id:
                return self._rejected(record, "DECISION_ID_BOUND_TO_OTHER_RUN")
            self._decision_owners[request.decision_id] = run_id
            self._human_requests[run_id] = request
            self._human_controls.setdefault(run_id, HumanDecisionControl())
            updated = self._advance(
                record, LocalLLMDayState.HUMAN_ACTION_REQUIRED,
                "Await the bound human decision and matching reviewer confirmation.",
                blocker="HUMAN_DECISION_REQUIRED", resume_target="PREFLIGHT",
            )
            return self._accepted(updated)

    def receive_human_decision(self, run_id: str, response: HumanResponse) -> dict[str, object]:
        with self._lock:
            request = self._human_requests.get(run_id)
            control = self._human_controls.get(run_id)
            if request is None or control is None:
                return self._rejected(self._record(run_id), "HUMAN_DECISION_NOT_BOUND")
            return control.receive(response, [request])

    def build_human_confirmation(
        self,
        run_id: str,
        record_id: str,
        *,
        confirmation_report_id: str,
        confirms_report_id: str,
        confirms_response_id: str,
        authority_record: str,
    ) -> dict[str, object]:
        with self._lock:
            control = self._human_controls.get(run_id)
            if control is None or record_id not in control.records:
                return self._rejected(self._record(run_id), "HUMAN_DECISION_NOT_BOUND")
            return control.build_confirmation(
                record_id,
                confirmation_report_id=confirmation_report_id,
                confirms_report_id=confirms_report_id,
                confirms_response_id=confirms_response_id,
                authority_record=authority_record,
            )

    def apply_human_confirmation(
        self,
        run_id: str,
        record_id: str,
        response: dict[str, object],
        *,
        continuation_succeeded: bool,
        effect_evidence_id: str | None,
    ) -> dict[str, object]:
        """Return only the bound run to PREFLIGHT after the confirmed effect."""
        with self._lock:
            control = self._human_controls.get(run_id)
            if control is None or record_id not in control.records:
                return self._rejected(self._record(run_id), "HUMAN_DECISION_NOT_BOUND")
            result = control.apply_confirmation(
                record_id,
                response,
                continuation_succeeded=continuation_succeeded,
                effect_evidence_id=effect_evidence_id,
            )
            if result["outcome"] == "ACCEPTED" and result["effect_applied"]:
                current = self._record(run_id)
                self._advance(
                    current,
                    LocalLLMDayState.PREFLIGHT,
                    "Recheck the same run after the confirmed human decision.",
                )
            return {**result, "run_id": run_id, "selected_day": self._record(run_id).intent.selected_day}

    def _persist_controller_record(
        self, controller: RepairRecoveryController, previous_control: RunControl
    ) -> None:
        if controller.record.control == previous_control:
            return
        current = self._record(controller.record.intent.run_id)
        adjusted = controller.record.control.model_copy(update={
            "state_history": current.control.state_history + (current.control.current_state,),
            "updated_at": self._next_time(current.control.updated_at),
        })
        controller.record = RunRecord(intent=current.intent, control=adjusted)
        self.store.update(controller.record, expected_updated_at=current.control.updated_at)

    def _completion_ready(self, record: RunRecord) -> bool:
        contract = self.program.snapshot.contract
        if contract is None or contract.remaining_gaps:
            return False
        required_ids = {
            record_id for criterion in contract.completion_criteria
            for record_id in criterion.evidence_record_ids.values()
        }
        evidence = self.program.snapshot.evidence_store
        return bool(required_ids) and all(
            record_id in evidence and evidence[record_id].run_id == record.intent.run_id
            and evidence[record_id].validator_result for record_id in required_ids
        )

    def _required_review_pending(self, record: RunRecord) -> bool:
        if record.control.blocker == "REVIEW_RESPONSE_REQUIRED":
            return True
        review = self._reviews.get(record.intent.run_id)
        return review is not None and review.state != ReviewControlState.VERIFIED

    def _advance(
        self, record: RunRecord, state: LocalLLMDayState, next_action: str,
        *, blocker: str | None = None, resume_target: str | None = None,
    ) -> RunRecord:
        control = RunControl(
            run_id=record.intent.run_id, selected_day=record.intent.selected_day,
            contract_fingerprint=record.intent.contract_fingerprint,
            current_state=state,
            state_history=record.control.state_history + (record.control.current_state,),
            next_action=next_action, blocker=blocker, resume_target=resume_target,
            updated_at=self._next_time(record.control.updated_at),
        )
        updated = RunRecord(intent=record.intent, control=control)
        self.store.update(updated, expected_updated_at=record.control.updated_at)
        return updated

    def _record(self, run_id: str) -> RunRecord:
        record = self.store.get(run_id)
        if record is None:
            raise KeyError(f"RunRecord not found: {run_id}")
        return record

    def _next_time(self, previous: datetime) -> datetime:
        candidate = self.clock()
        return candidate if candidate > previous else previous + timedelta(microseconds=1)

    @staticmethod
    def _after(value: datetime, microseconds: int = 1) -> datetime:
        return value + timedelta(microseconds=microseconds)

    @staticmethod
    def _accepted(record: RunRecord) -> dict[str, object]:
        return {
            "outcome": "ACCEPTED", "run_id": record.intent.run_id,
            "selected_day": record.intent.selected_day,
            "control": record.control.model_dump(mode="json"),
            "day_execution_started": False,
        }

    @staticmethod
    def _rejected(record: RunRecord, reason: str) -> dict[str, object]:
        return {
            "outcome": "REJECTED", "reason_code": reason,
            "run_id": record.intent.run_id, "selected_day": record.intent.selected_day,
            "control": record.control.model_dump(mode="json"),
            "day_execution_started": False,
        }
