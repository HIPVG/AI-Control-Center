import json
import subprocess
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
from backend.models.result import TokenUsage
from backend.models.runtime import CodexMode, RuntimeConfig, SmokeRunResult, load_runtime_config
from backend.models.state import RunState, WorkflowState
from backend.orchestrator.state_machine import StateManager
from backend.orchestrator.progress import calculate_progress
from backend.runners.codex import MockCodexRunner, RealCodexRunner, SmokeWorkspace
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
    def __init__(
        self,
        state_store: StateStore | None = None,
        config_path: Path | None = None,
        runtime_config: RuntimeConfig | None = None,
        smoke_root: Path | None = None,
        real_runner: RealCodexRunner | None = None,
    ) -> None:
        self.store = state_store
        self.state_manager = StateManager()
        self.budgets = TokenBudgetManager(load_budget_config(config_path) if config_path else None)
        project_root = Path(__file__).resolve().parents[2]
        self.project_root = project_root
        self.runtime = runtime_config or load_runtime_config(project_root / "config" / "runtime.yaml")
        self.smoke_workspace = SmokeWorkspace(smoke_root or project_root / "state" / "smoke")
        self.real_runner = real_runner or RealCodexRunner(self.runtime.codex)
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
            "token_usage_tracking_version": 1,
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
        usage = saved.get("token_usage")
        if usage:
            self.budgets.day_usage = TokenUsage.model_validate(usage)
        migrated = self._migrate_legacy_progress(saved)
        reconciled = self._reconcile_legacy_mock_usage(saved)
        if migrated or reconciled:
            self._save()

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

    def _reconcile_legacy_mock_usage(self, saved: dict[str, Any]) -> bool:
        """Remove only v0.1's fabricated mock counts, retaining a structured audit record."""
        if "token_usage_tracking_version" in saved:
            return False
        self.data["token_usage_tracking_version"] = 1
        if self.budgets.day_usage.total_tokens == 0 or any(event.event_type == AuditEventType.SMOKE_ACCEPTED for event in self.timeline):
            return True
        previous = self.budgets.day_usage.model_dump()
        self.budgets.day_usage = TokenUsage()
        self._event(
            "SYSTEM",
            AuditEventType.TOKEN_USAGE_RECONCILED,
            "Legacy fabricated mock token usage was reset to zero.",
            details={"previous": previous, "current": self.budgets.day_usage.model_dump(), "migration": "v0.1 mock token reconciliation"},
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
            "runtime": self.runtime.model_dump(mode="json"),
            "timeline": [event.model_dump(mode="json") for event in self.timeline],
        }

    def runtime_view(self) -> dict[str, Any]:
        return self.runtime.model_dump(mode="json")

    def run_codex_smoke(self) -> dict[str, Any]:
        task_id = "CODEX-SMOKE"
        mode = self.runtime.codex.mode
        if mode != CodexMode.REAL:
            result = SmokeRunResult(status="rejected", mode=mode, error_code="REAL_MODE_REQUIRED")
            self._event(task_id, AuditEventType.SMOKE_REJECTED, "Real Codex smoke rejected because runtime mode is mock.", details=result.model_dump(mode="json"))
            self._save()
            return result.model_dump(mode="json")

        budget_decision = self.budgets.check(TokenUsage(), retry_count=0)
        if budget_decision != BudgetDecision.ALLOWED:
            result = SmokeRunResult(status="rejected", mode=mode, error_code=budget_decision.value)
            self._event(task_id, AuditEventType.SMOKE_REJECTED, f"Real Codex smoke blocked by {budget_decision.value}.", details=result.model_dump(mode="json"))
            self._save()
            return result.model_dump(mode="json")

        smoke_directory = self.smoke_workspace.create_run()
        target = self.smoke_workspace.result_path(smoke_directory)
        relative_path = str(target.relative_to(self.smoke_workspace.root))
        before_files = self._repository_files()
        self._event(task_id, AuditEventType.SMOKE_STARTED, "Real Codex smoke started in an isolated workspace.", details={"smoke_path": relative_path, "mode": mode.value})
        self._save()
        execution = self.real_runner.run_smoke(smoke_directory, target)
        after_files = self._repository_files()
        changed_files = sorted(after_files - before_files) if before_files is not None and after_files is not None else []
        self._event(task_id, AuditEventType.SMOKE_RESULT, f"Codex process completed exit={execution.exit_code if execution.exit_code is not None else 'unavailable'}.", details={"status": execution.status, "error_code": execution.error_code, "exit_code": execution.exit_code, "token_usage": execution.token_usage.model_dump(), "diagnostics": execution.diagnostics.model_dump(mode="json") if execution.diagnostics else None})
        if execution.status != "completed":
            result = SmokeRunResult(status="failed", mode=mode, smoke_path=relative_path, execution=execution, error_code=execution.error_code)
            self._event(task_id, AuditEventType.SMOKE_REJECTED, f"Real Codex smoke failed: {execution.error_code}.", details=result.model_dump(mode="json"))
            self._save()
            return result.model_dump(mode="json")

        if changed_files:
            result = SmokeRunResult(status="failed", mode=mode, smoke_path=relative_path, execution=execution, error_code="PRODUCTION_FILES_MODIFIED")
            self._event(task_id, AuditEventType.SMOKE_REJECTED, "Real Codex smoke failed: production files changed.", details={**result.model_dump(mode="json"), "changed_files": changed_files})
            self._save()
            return result.model_dump(mode="json")

        recorded = self.budgets.record_actual(execution.token_usage, retry_count=0)
        if recorded != BudgetDecision.ALLOWED:
            self._event(
                task_id,
                AuditEventType.TOKEN_BUDGET_WARNING,
                f"Real Codex smoke completed over the configured budget: {recorded.value}.",
                details={"budget_decision": recorded.value, "token_usage": execution.token_usage.model_dump()},
            )

        acceptance_error = self.smoke_workspace.acceptance_error(target)
        accepted = acceptance_error is None
        execution.test_result = "pass" if accepted else "fail"
        result = SmokeRunResult(status="completed" if accepted else "failed", mode=mode, smoke_path=relative_path, deterministic_passed=accepted, execution=execution, error_code=acceptance_error)
        event_type = AuditEventType.SMOKE_ACCEPTED if accepted else AuditEventType.SMOKE_REJECTED
        if accepted and execution.token_usage.available:
            self._event(task_id, AuditEventType.SMOKE_ACCEPTED, "Real Codex smoke deterministic acceptance passed; token usage captured.", details=result.model_dump(mode="json"))
        elif accepted:
            self._event(task_id, AuditEventType.SMOKE_ACCEPTED, "Real Codex smoke deterministic acceptance passed; token usage unavailable.", details=result.model_dump(mode="json"))
        else:
            self._event(task_id, event_type, f"Real Codex smoke failed: {acceptance_error}.", details=result.model_dump(mode="json"))
        self._save()
        return result.model_dump(mode="json")

    def _repository_files(self) -> set[str] | None:
        try:
            completed = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
                shell=False,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return None
        if completed.returncode != 0:
            return None
        return {line[3:] for line in completed.stdout.splitlines() if len(line) > 3}

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
