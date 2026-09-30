"""RI-00 durable Go boundary for one server-owned run identity."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from threading import RLock
from typing import Callable

from backend.control.local_llm_day_program import LocalLLMDayProgram
from backend.control.run_store import RunStore
from backend.control.preflight_authority import PreflightFactRecord
from backend.models.local_llm_day import LocalLLMDayState, RunControl, RunIntent, RunRecord


@dataclass(frozen=True)
class RunPreflightFacts:
    effective_permission: bool | None = None
    external_prerequisite: bool | None = None
    record: PreflightFactRecord | None = None


PreflightResolver = Callable[[RunIntent], RunPreflightFacts]
RunExecutor = Callable[[str, int], dict[str, object]]


class RunCoordinator:
    """Persist admission before delegating exactly once to the Day executor."""

    TERMINAL_STATES = frozenset({
        LocalLLMDayState.COMPLETE,
        LocalLLMDayState.STOPPED,
        LocalLLMDayState.FAILED,
        LocalLLMDayState.FAILED_UNRECOVERABLE,
    })

    def __init__(
        self,
        program: LocalLLMDayProgram,
        store: RunStore,
        *,
        preflight_resolver: PreflightResolver,
        executor: RunExecutor,
        clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    ) -> None:
        self.program = program
        self.store = store
        self.preflight_resolver = preflight_resolver
        self.executor = executor
        self.clock = clock
        self._lock = RLock()

    def go(self, day: int, *, source: str = "go") -> dict[str, object]:
        with self._lock:
            current = self.store.current()
            if current is not None and current.control.current_state not in self.TERMINAL_STATES:
                return {
                    "error_code": "RUN_ALREADY_ACTIVE",
                    "source": source,
                    "run_id": current.intent.run_id,
                    "selected_day": current.intent.selected_day,
                    "execution_started": False,
                    "record_persisted": True,
                    "run_record": current.model_dump(mode="json"),
                }

            prepared = self.program.prepare_intent(day)
            raw_intent = prepared.get("run_intent")
            if raw_intent is None:
                return {**prepared, "source": source, "record_persisted": False}
            intent = RunIntent.model_validate(raw_intent)
            facts = self.preflight_resolver(intent)
            admission = self.program.admission(
                intent,
                effective_permission=facts.effective_permission,
                external_prerequisite=facts.external_prerequisite,
            )
            state = LocalLLMDayState(admission["next_state"])
            record = RunRecord(
                intent=intent,
                control=RunControl(
                    run_id=intent.run_id,
                    selected_day=intent.selected_day,
                    contract_fingerprint=intent.contract_fingerprint,
                    current_state=state,
                    state_history=(),
                    next_action=str(admission["next_action"]),
                    blocker=(str(admission["reason_code"])
                             if admission["status"] != "ADMISSIBLE" else None),
                    resume_target=("PREFLIGHT" if admission["status"] != "ADMISSIBLE" else None),
                    updated_at=self.clock(),
                ),
            )
            self.store.create(record)
            response = {
                **prepared,
                "admission_run_id": intent.run_id,
                "admission": admission,
                "preflight_fact": (facts.record.model_dump(mode="json") if facts.record else None),
                "source": source,
                "record_persisted": True,
                "run_record": record.model_dump(mode="json"),
            }
            if admission["status"] != "ADMISSIBLE":
                return response

            try:
                effect = self.executor(intent.run_id, day)
            except Exception as exc:  # the persisted PREFLIGHT is the recovery anchor
                return {
                    **response,
                    "error_code": "DAY_EXECUTOR_FAILED",
                    "execution_started": True,
                    "executor_error": type(exc).__name__,
                }
            effect_run_id = effect.get("run_id")
            if effect_run_id != intent.run_id:
                return {
                    **response,
                    "error_code": "EXECUTOR_RUN_ID_MISMATCH",
                    "execution_started": True,
                }
            return {**response, "execution_started": True, "execution": effect}

    def legacy_start(self, day: int) -> dict[str, object]:
        return self.go(day, source="legacy_direct_start")
