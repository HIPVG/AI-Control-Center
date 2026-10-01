"""Production composition root for one durable local-LLM run.

The component owns no new workflow state.  It wires the accepted coordinator,
execution controllers, telemetry store, and read projection to the same stores
and rejects cross-run data before it can become observable product state.
"""

from __future__ import annotations

from datetime import datetime
from hashlib import sha256
import json

from backend.control.local_llm_day_program import LocalLLMDayProgram
from backend.control.preflight_authority import PreflightFactStore
from backend.control.run_execution_composition import RunExecutionComposition
from backend.control.run_projection_composition import build_run_read_model
from backend.control.run_store import RunStore
from backend.control.run_telemetry_store import RunTelemetryStore
from backend.models.local_llm_day import (
    LocalLLMDayState,
    RunIntent,
    RunTelemetry,
    TelemetryDecision,
    TelemetryMetric,
)


class RunProductComposition:
    """Bind execution, telemetry, and readback to one production run store."""

    def __init__(
        self,
        program: LocalLLMDayProgram,
        run_store: RunStore,
        telemetry_store: RunTelemetryStore,
        preflight_fact_store: PreflightFactStore | None = None,
    ) -> None:
        self.program = program
        self.run_store = run_store
        self.telemetry_store = telemetry_store
        self.preflight_fact_store = preflight_fact_store
        self.execution = RunExecutionComposition(program, run_store)

    def record_telemetry(self, run_id: str, telemetry: RunTelemetry) -> dict[str, object]:
        current = self.run_store.current()
        if current is None or current.intent.run_id != run_id:
            return {"outcome": "REJECTED", "reason_code": "RUN_NOT_CURRENT", "run_id": run_id}
        if telemetry.run_id != run_id:
            return {
                "outcome": "REJECTED",
                "reason_code": "TELEMETRY_RUN_ID_MISMATCH",
                "run_id": run_id,
            }
        existing = self.telemetry_store.get(run_id)
        if existing is not None:
            if existing == telemetry:
                return {"outcome": "ACCEPTED", "run_id": run_id, "replay": True}
            return {"outcome": "REJECTED", "reason_code": "TELEMETRY_CONFLICT", "run_id": run_id}
        self.telemetry_store.create(telemetry)
        return {"outcome": "ACCEPTED", "run_id": run_id, "replay": False}

    def reconcile_terminal_telemetry(
        self, run_id: str, task_records: list[object]
    ) -> dict[str, object]:
        """Create one v2 snapshot from exact-run terminal task facts."""
        current = self.run_store.current()
        if current is None or current.intent.run_id != run_id:
            return {"outcome": "REJECTED", "reason_code": "RUN_NOT_CURRENT", "run_id": run_id}
        snapshot = self.program.snapshot
        if snapshot.run_id != run_id:
            return {"outcome": "REJECTED", "reason_code": "DAY_SNAPSHOT_RUN_ID_MISMATCH", "run_id": run_id}
        if snapshot.state not in {
            LocalLLMDayState.COMPLETE,
            LocalLLMDayState.HUMAN_ACTION_REQUIRED,
            LocalLLMDayState.EXTERNAL_ACTION_REQUIRED,
            LocalLLMDayState.FAILED_UNRECOVERABLE,
            LocalLLMDayState.FAILED,
        }:
            return {"outcome": "REJECTED", "reason_code": "DAY_NOT_TERMINAL", "run_id": run_id}
        try:
            telemetry = self._terminal_telemetry(current.intent, task_records)
        except ValueError as exc:
            return {"outcome": "REJECTED", "reason_code": str(exc), "run_id": run_id}
        return self.record_telemetry(run_id, telemetry)

    def settle_terminal_run(
        self, run_id: str, task_records: list[object]
    ) -> dict[str, object]:
        """Reconcile one already-saved terminal Day without repeating an effect."""
        if self.program.snapshot.state != LocalLLMDayState.COMPLETE:
            return self.execution.project_day_state(run_id)
        current = self.run_store.current()
        if (
            current is not None
            and current.intent.run_id == run_id
            and current.control.current_state == LocalLLMDayState.COMPLETE
        ):
            evidence = self.execution.verify_bound_day_evidence(run_id)
            if evidence.get("outcome") != "ACCEPTED":
                return {
                    "outcome": "REJECTED",
                    "reason_code": evidence.get("reason_code", "BOUND_EVIDENCE_CONFLICT"),
                    "run_id": run_id,
                    "stage": "EVIDENCE_REPLAY",
                }
            try:
                candidate = self._terminal_telemetry(current.intent, task_records)
            except ValueError as exc:
                return {
                    "outcome": "REJECTED", "reason_code": str(exc),
                    "run_id": run_id, "stage": "TELEMETRY_REPLAY",
                }
            if self.telemetry_store.get(run_id) != candidate:
                return {
                    "outcome": "REJECTED", "reason_code": "TELEMETRY_CONFLICT",
                    "run_id": run_id, "stage": "TELEMETRY_REPLAY",
                }
            return {
                "outcome": "ACCEPTED",
                "run_id": run_id,
                "stage": "ALREADY_PROJECTED",
                "telemetry_replay": True,
                "run_record": current.model_dump(mode="json"),
            }
        evidence = self.execution.bind_day_evidence(run_id)
        if evidence.get("outcome") != "ACCEPTED":
            return {
                "outcome": "REJECTED",
                "reason_code": evidence.get("reason_code", "EVIDENCE_RECONCILIATION_FAILED"),
                "run_id": run_id,
                "stage": "EVIDENCE",
            }
        telemetry = self.reconcile_terminal_telemetry(run_id, task_records)
        if telemetry.get("outcome") != "ACCEPTED":
            return {
                "outcome": "REJECTED",
                "reason_code": telemetry.get("reason_code", "TELEMETRY_RECONCILIATION_FAILED"),
                "run_id": run_id,
                "stage": "TELEMETRY",
            }
        projection = self.execution.project_day_state(run_id)
        if projection.get("outcome") != "ACCEPTED":
            return {
                "outcome": "REJECTED",
                "reason_code": projection.get("reason_code", "DAY_STATE_PROJECTION_FAILED"),
                "run_id": run_id,
                "stage": "PROJECTION",
                "telemetry_replay": bool(telemetry.get("replay")),
            }
        return {
            "outcome": "ACCEPTED",
            "run_id": run_id,
            "stage": "PROJECTED",
            "telemetry_replay": bool(telemetry.get("replay")),
            "run_record": projection.get("run_record"),
        }

    @staticmethod
    def _terminal_telemetry(intent: RunIntent, task_records: list[object]) -> RunTelemetry:
        if not task_records:
            raise ValueError("TERMINAL_TASK_RECORDS_MISSING")
        task_ids: list[str] = []
        observed: list[datetime] = []
        gross = cached = uncached = output = attempts = 0
        warnings: set[str] = set()
        costs: list[tuple[float, str]] = []
        for raw in task_records:
            if not isinstance(raw, dict):
                raise ValueError("TERMINAL_TASK_RECORD_INVALID")
            if raw.get("product_run_id") != intent.run_id:
                raise ValueError("TERMINAL_TASK_RUN_ID_MISMATCH")
            if raw.get("final_result") not in {
                "COMPLETE", "COMPLETE_NO_CHANGE", "FAILED", "HUMAN_REVIEW"
            }:
                raise ValueError("TERMINAL_TASK_NOT_TERMINAL")
            task_id = raw.get("run_id")
            if not isinstance(task_id, str) or not task_id or task_id in task_ids:
                raise ValueError("TERMINAL_TASK_ID_INVALID_OR_DUPLICATE")
            task_ids.append(task_id)
            end_time = raw.get("end_time")
            try:
                at = datetime.fromisoformat(str(end_time).replace("Z", "+00:00"))
            except ValueError as exc:
                raise ValueError("TERMINAL_TASK_TIME_INVALID") from exc
            if at.utcoffset() is None:
                raise ValueError("TERMINAL_TASK_TIME_INVALID")
            observed.append(at)
            raw_attempts = raw.get("codex_attempts")
            if not isinstance(raw_attempts, list):
                raise ValueError("TERMINAL_TASK_ATTEMPTS_INVALID")
            local = {"gross": 0, "cached": 0, "uncached": 0, "output": 0}
            seen_attempts: set[int] = set()
            for attempt in raw_attempts:
                if not isinstance(attempt, dict) or not isinstance(attempt.get("attempt"), int):
                    raise ValueError("TERMINAL_TASK_ATTEMPTS_INVALID")
                attempt_id = attempt["attempt"]
                if attempt_id < 1 or attempt_id in seen_attempts:
                    raise ValueError("TERMINAL_TASK_ATTEMPTS_INVALID")
                seen_attempts.add(attempt_id)
                values = {
                    key: attempt.get(field)
                    for key, field in (
                        ("gross", "gross_input_tokens"),
                        ("cached", "cached_input_tokens"),
                        ("uncached", "uncached_input_tokens"),
                        ("output", "output_tokens"),
                    )
                }
                if any(not isinstance(value, int) or value < 0 for value in values.values()):
                    raise ValueError("TERMINAL_TASK_TOKEN_TOTAL_INVALID")
                if values["gross"] != values["cached"] + values["uncached"]:
                    raise ValueError("TERMINAL_TASK_TOKEN_TOTAL_INVALID")
                for key, value in values.items():
                    local[key] += value
            expected = {
                "gross": raw.get("gross_input_tokens"),
                "cached": raw.get("cached_input_tokens"),
                "uncached": raw.get("uncached_input_tokens"),
                "output": raw.get("output_tokens"),
            }
            if local != expected:
                raise ValueError("TERMINAL_TASK_TOKEN_TOTAL_INVALID")
            attempts += len(raw_attempts)
            gross += local["gross"]
            cached += local["cached"]
            uncached += local["uncached"]
            output += local["output"]
            warning = raw.get("budget_warning")
            if warning is not None:
                if not isinstance(warning, str) or not warning:
                    raise ValueError("TERMINAL_TASK_BUDGET_DECISION_INVALID")
                warnings.add(warning)
            cost = raw.get("measured_cost")
            currency = raw.get("cost_currency")
            if cost is not None or currency is not None:
                if not isinstance(cost, (int, float)) or isinstance(cost, bool) or cost < 0:
                    raise ValueError("TERMINAL_TASK_COST_INVALID")
                if not isinstance(currency, str) or not currency:
                    raise ValueError("TERMINAL_TASK_COST_INVALID")
                costs.append((float(cost), currency))
        if len(warnings) > 1:
            raise ValueError("TERMINAL_TASK_BUDGET_DECISION_CONFLICT")
        if costs and len(costs) != len(task_records):
            raise ValueError("TERMINAL_TASK_COST_INCOMPLETE")
        if costs and len({item[1] for item in costs}) != 1:
            raise ValueError("TERMINAL_TASK_COST_CURRENCY_CONFLICT")
        at = max(observed)
        fingerprint = sha256(json.dumps(sorted(task_ids)).encode("utf-8")).hexdigest()[:16]
        source = f"terminal task records:{fingerprint}"
        metric = lambda value, unit: TelemetryMetric(
            value=value, unit=unit, source=source, observed_at=at
        )
        budget = (
            TelemetryDecision(value=next(iter(warnings)), source=source, observed_at=at)
            if warnings
            else TelemetryDecision(
                value=None, observed_at=at,
                unknown_reason="terminal task records did not expose a budget decision",
            )
        )
        cost_metric = (
            metric(sum(item[0] for item in costs), costs[0][1])
            if costs
            else TelemetryMetric(
                value=None, unit=intent.requested_limits.currency, observed_at=at,
                unknown_reason="terminal task records did not expose measured cost",
            )
        )
        return RunTelemetry(
            schema_version=2,
            run_id=intent.run_id,
            manual_relay_count=TelemetryMetric(
                value=None, unit="count", observed_at=at,
                unknown_reason="terminal task records do not capture relay interventions",
            ),
            attempt_count=metric(attempts, "attempts"),
            attempt_limit=TelemetryMetric(
                value=intent.requested_limits.max_attempts,
                unit="attempts", source="immutable RunIntent", observed_at=at,
            ),
            input_tokens=metric(gross, "tokens"),
            cached_input_tokens=metric(cached, "tokens"),
            uncached_input_tokens=metric(uncached, "tokens"),
            output_tokens=metric(output, "tokens"),
            budget_decision=budget,
            cost=cost_metric,
            captured_at=at,
        )

    def read(self) -> dict[str, object]:
        return build_run_read_model(
            run_store=self.run_store,
            telemetry_store=self.telemetry_store,
            preflight_fact_store=self.preflight_fact_store,
            program=self.program,
        ).read()
