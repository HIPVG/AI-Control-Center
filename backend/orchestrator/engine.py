import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from backend.agents.architect import MockArchitect
from backend.agents.evaluator import MockEvaluator
from backend.agents.triage import MockTriage, TriageDecision
from backend.control.context_broker import ContextBroker
from backend.control.scope_guard import ScopeGuard
from backend.control.token_budget import BudgetDecision, TokenBudgetManager, load_budget_config
from backend.models.audit import AuditEvent, AuditEventType
from backend.models.state import RunState, WorkflowState
from backend.orchestrator.state_machine import StateManager
from backend.orchestrator.progress import calculate_progress
from backend.runners.codex import MockCodexRunner
from backend.runners.pytest_runner import PytestRunner


class StateStore(Protocol):
    def load(self) -> dict[str, Any] | None: ...
    def save(self, data: dict[str, Any]) -> None: ...


class JsonStateStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> dict[str, Any] | None:
        if not self.path.exists():
            return None
        return json.loads(self.path.read_text(encoding="utf-8"))

    def save(self, data: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


class ControlCenterEngine:
    def __init__(self, state_store: StateStore | None = None, config_path: Path | None = None) -> None:
        self.store = state_store
        self.state_manager = StateManager()
        self.budgets = TokenBudgetManager(load_budget_config(config_path) if config_path else None)
        self.timeline: list[AuditEvent] = []
        self._load()

    def _defaults(self) -> dict[str, Any]:
        task_completed, task_total = 18, 22
        return {
            "week": 1,
            "validation_day": 3,
            "calendar_day": 5,
            "overall_progress": 58,
            "day_progress": 63,
            "progress_basis": {
                "overall": {"completed": 58, "total": 100},
                "day": {"completed": 63, "total": 100},
            },
            "progress_tracking_version": 1,
            "task_start_completed": {"PC-014": 18},
            "task_progress": calculate_progress(task_completed, task_total),
            "current_task": {"task_id": "PC-014", "title": "Evidence Grounding", "completed": task_completed, "total": task_total, "retry": 0, "max_retry": 2},
            "summary": {"pass": 12, "fail": 1, "review": 0},
            "agent_activity": {"Architect": "DONE", "Gate": "WAITING", "Codex": "WAITING", "Tests": "WAITING", "Evaluator": "WAITING"},
            "metrics": {"groundedness": 4.8, "process_consistency": 4.7, "instruction_fit": 4.9, "information_capacity": 4.6},
            "days": [{"day": day, "title": title, "progress": 100 if day < 3 else 63 if day == 3 else 0, "current": day == 3} for day, title in enumerate(["Environment", "Baseline", "Adaptability", "Process", "Capacity", "Comparison", "Scenario", "Review"])],
            "tasks": [{"task_id": "PC-014", "title": "Evidence Grounding", "state": "IDLE", "progress": 82}],
        }

    def _load(self) -> None:
        saved = self.store.load() if self.store else None
        if not saved:
            self.data = self._defaults()
            return
        self.data = {**self._defaults(), **saved}
        self.state_manager = StateManager(RunState.model_validate(saved.get("run_state", {})))
        self.timeline = [self._load_event(event) for event in saved.get("timeline", [])]
        if self._migrate_legacy_progress(saved):
            self._save()
        usage = saved.get("token_usage")
        if usage:
            from backend.models.result import TokenUsage
            self.budgets.day_usage = TokenUsage.model_validate(usage)

    def _save(self) -> None:
        if self.store:
            self.store.save({**self.data, "run_state": self.state_manager.current.model_dump(mode="json"), "timeline": [event.model_dump(mode="json") for event in self.timeline], "token_usage": self.budgets.day_usage.model_dump()})

    def _load_event(self, event: dict[str, Any]) -> AuditEvent:
        if "event_type" in event:
            return AuditEvent.model_validate(event)
        return AuditEvent(
            timestamp=event.get("timestamp", datetime.now(timezone.utc)),
            task_id=self.data["current_task"]["task_id"],
            event_type=AuditEventType.LEGACY_EVENT,
            message=event.get("message", "Legacy audit event"),
        )

    def _event(
        self,
        task_id: str,
        event_type: AuditEventType,
        message: str,
        *,
        from_state: WorkflowState | None = None,
        to_state: WorkflowState | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.timeline.append(AuditEvent(
            task_id=task_id,
            event_type=event_type,
            message=message,
            from_state=from_state,
            to_state=to_state,
            details=details or {},
        ))

    def _transition(self, task_id: str, target: WorkflowState, reason: str) -> None:
        source = self.state_manager.current.state
        self.state_manager.transition(target, reason=reason)
        self._event(
            task_id,
            AuditEventType.STATE_TRANSITION,
            f"{source.value} → {target.value}: {reason}",
            from_state=source,
            to_state=target,
            details={"reason": reason},
        )

    def _task_record(self, task_id: str) -> dict[str, Any]:
        return next(item for item in self.data["tasks"] if item["task_id"] == task_id)

    def _migrate_legacy_progress(self, saved: dict[str, Any]) -> bool:
        """Backfill v0.1 mock progress once for state written before tracking existed."""
        if "progress_tracking_version" in saved:
            return False
        task = self.data["current_task"]
        task_id = task["task_id"]
        if self._task_record(task_id)["state"] != WorkflowState.COMPLETE.value:
            return False
        start_completed = self.data["task_start_completed"].get(task_id, task["total"])
        remaining = max(0, task["total"] - start_completed)
        before = {"overall": self.data["overall_progress"], "day": self.data["day_progress"], "task": self.data["task_progress"]}
        basis = {
            scope: {"completed": min(100, before[scope] + remaining), "total": 100}
            for scope in ("overall", "day")
        }
        self.data["progress_basis"] = basis
        self.data["progress_tracking_version"] = 1
        self.data["overall_progress"] = calculate_progress(**basis["overall"])
        self.data["day_progress"] = calculate_progress(**basis["day"])
        self.data["days"][self.data["validation_day"]]["progress"] = self.data["day_progress"]
        self._event(
            task_id,
            AuditEventType.PROGRESS_UPDATED,
            f"{task_id} legacy completion progress backfilled: overall {before['overall']}% → {self.data['overall_progress']}%, day {before['day']}% → {self.data['day_progress']}%",
            details={"previous": before, "current": {"overall": self.data["overall_progress"], "day": self.data["day_progress"], "task": self.data["task_progress"]}, "migration": "v0.1 progress tracking backfill"},
        )
        return True

    def _complete_task_progress(self, task_id: str) -> None:
        task = self.data["current_task"]
        previous = {
            "overall": self.data["overall_progress"],
            "day": self.data["day_progress"],
            "task": self.data["task_progress"],
        }
        remaining = task["total"] - task["completed"]
        basis = self.data["progress_basis"]
        for scope in ("overall", "day"):
            basis[scope]["completed"] += remaining
        task["completed"] = task["total"]
        self.data["task_progress"] = calculate_progress(task["completed"], task["total"])
        self.data["overall_progress"] = calculate_progress(**basis["overall"])
        self.data["day_progress"] = calculate_progress(**basis["day"])
        self.data["days"][self.data["validation_day"]]["progress"] = self.data["day_progress"]
        current_task = self._task_record(task_id)
        current_task.update({"state": "COMPLETE", "progress": self.data["task_progress"]})
        current = {
            "overall": self.data["overall_progress"],
            "day": self.data["day_progress"],
            "task": self.data["task_progress"],
        }
        self._event(
            task_id,
            AuditEventType.PROGRESS_UPDATED,
            f"{task_id} completion updated progress: overall {previous['overall']}% → {current['overall']}%, day {previous['day']}% → {current['day']}%, task {previous['task']}% → {current['task']}%",
            details={"previous": previous, "current": current, "delta": {scope: current[scope] - previous[scope] for scope in current}, "basis": basis},
        )

    def status(self) -> dict[str, Any]:
        return {
            **self.data,
            "run_state": self.state_manager.current.model_dump(mode="json"),
            "token_usage": self.budgets.usage_view(),
            "timeline": [event.model_dump(mode="json") for event in self.timeline],
        }

    def run_mock(self) -> dict[str, Any]:
        task_id = self.data["current_task"]["task_id"]
        if self._task_record(task_id)["state"] == WorkflowState.COMPLETE.value:
            self._event(task_id, AuditEventType.WORKFLOW_SKIPPED, f"{task_id} mock workflow skipped; task is already complete.")
            self._save()
            return self.status()
        if self.state_manager.current.state != WorkflowState.IDLE:
            self._transition(task_id, WorkflowState.IDLE, "previous terminal workflow reset")
        work_order = MockArchitect().create_work_order()
        self.state_manager.start_task(work_order.task_id)
        self._event(work_order.task_id, AuditEventType.TASK_STARTED, f"{work_order.task_id} mock workflow started")
        self._transition(work_order.task_id, WorkflowState.PLANNING, "structured work order created")
        self._transition(work_order.task_id, WorkflowState.PRECHECK, "deterministic gate")
        self._transition(work_order.task_id, WorkflowState.RUNNING_TEST, "precheck test")
        self._event(work_order.task_id, AuditEventType.DETERMINISTIC_CHECK, f"{work_order.task_id} deterministic check FAIL", details={"passed": False})
        self._transition(work_order.task_id, WorkflowState.TRIAGE, "deterministic failure triaged")
        if MockTriage().classify(work_order) != TriageDecision.CODE_FIX:
            self._transition(work_order.task_id, WorkflowState.HUMAN_REVIEW, "not a code fix")
            self._save()
            return self.status()
        self._transition(work_order.task_id, WorkflowState.CODEX_FIX, "CODE_FIX approved")
        self.data["agent_activity"].update({"Gate": "DONE", "Codex": "RUNNING"})
        self._event(work_order.task_id, AuditEventType.TRIAGE, f"{work_order.task_id} gate classified CODE_FIX", details={"decision": "CODE_FIX"})
        context = ContextBroker().build(work_order, error_excerpt="Mock deterministic validation failed.")
        self._event(work_order.task_id, AuditEventType.CONTEXT_CREATED, f"{work_order.task_id} bounded context package built", details={"allowed_file_count": len(context.allowed_files), "retry_number": context.retry_number})
        execution = MockCodexRunner().run(context)
        budget = self.budgets.record(execution.token_usage, retry_count=self.state_manager.current.retry_count)
        if budget != BudgetDecision.ALLOWED:
            self._transition(work_order.task_id, WorkflowState.HUMAN_REVIEW, budget.value)
            self._event(work_order.task_id, AuditEventType.CODEX_RESULT, f"{work_order.task_id} budget blocked: {budget.value}", details={"budget_decision": budget.value})
            self._save()
            return self.status()
        scope = ScopeGuard().check(work_order, execution.files_changed)
        if not scope.allowed:
            self._transition(work_order.task_id, WorkflowState.HUMAN_REVIEW, "out-of-scope files")
            self._event(work_order.task_id, AuditEventType.CODEX_RESULT, f"{work_order.task_id} scope escalation: {', '.join(scope.out_of_scope)}", details={"out_of_scope": scope.out_of_scope})
            self._save()
            return self.status()
        self._event(work_order.task_id, AuditEventType.CODEX_RESULT, f"{', '.join(execution.files_changed)} mock builder change recorded", details={"files_changed": execution.files_changed, "token_usage": execution.token_usage.model_dump()})
        self._transition(work_order.task_id, WorkflowState.RUNNING_TEST, "post-builder deterministic test")
        test = PytestRunner().mock_pass(work_order.acceptance_tests[0])
        self.data["agent_activity"].update({"Codex": "DONE", "Tests": "DONE", "Evaluator": "RUNNING"})
        self._event(work_order.task_id, AuditEventType.TEST_RESULT, f"{work_order.task_id} pytest PASS", details=test.model_dump())
        self._transition(work_order.task_id, WorkflowState.EVALUATING, "tests passed")
        evaluation = MockEvaluator().evaluate(execution, test)
        self.data["metrics"] = evaluation.score
        if evaluation.decision.value == "PASS":
            self._event(work_order.task_id, AuditEventType.EVALUATION_RESULT, f"{work_order.task_id} evaluator PASS", details=evaluation.model_dump(mode="json"))
            self._transition(work_order.task_id, WorkflowState.COMPLETE, "independent evaluation pass")
            self.data["summary"]["pass"] += 1
            self.data["current_task"]["retry"] = 0
            self._complete_task_progress(work_order.task_id)
            self.data["agent_activity"]["Evaluator"] = "DONE"
        else:
            self._transition(work_order.task_id, WorkflowState.HUMAN_REVIEW, evaluation.decision.value)
        self._save()
        return self.status()
