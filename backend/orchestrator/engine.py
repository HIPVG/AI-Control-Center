import json
import hashlib
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Protocol
from uuid import uuid4

from backend.agents.architect import MockArchitect
from backend.agents.day_providers import (
    CodexArchitectProvider, CodexReviewerProvider, MockCodexArchitectProvider,
    MockDayArchitect, MockSemanticEvaluator, OpenAIDayArchitect, OpenAISemanticEvaluator,
    ProviderRequestError,
)
from backend.agents.evaluator import MockEvaluator
from backend.agents.triage import MockTriage, TriageDecision
from backend.control.context_broker import ContextBroker
from backend.control.model_router import ModelRouter, load_model_profile_registry
from backend.control.orchestration import load_orchestration_config
from backend.control.faults import FaultProfile, FaultRegistry, load_fault_registry, locate_qa_shipment_gt_operator
from backend.control.experiments import load_experiments
from backend.control.goal_policy import propose_goal
from backend.models.goal import GoalPlan, GoalPlanStatus
from backend.models.experiment import ExperimentOutcome, ExperimentRun
from backend.control.projects import ProjectRegistry, load_project_registry
from backend.control.plans import load_plan_registry
from backend.control.task_discovery import DeterministicTaskDiscovery, DiscoveryRegistry, FailingTaskDiscoveryResult, load_discovery_registry
from backend.control.tasks import ConfiguredTask, TaskCommand, TaskRegistry, load_task_registry
from backend.control.scope_guard import ScopeGuard
from backend.control.token_budget import BudgetDecision, TokenBudgetManager, load_budget_config
from backend.models.audit import AuditEvent, AuditEventType
from backend.models.day import ArchitectDecision, DayExecutionMode, DayPlan, DayPlanRegistry
from backend.models.orchestration import ProviderBudget
from backend.models.result import TokenUsage
from backend.models.runtime import CodexAttemptResult, CodexMode, CommandRunResult, FaultRepairResult, ProjectSmokeResult, RuntimeConfig, SmokeRunResult, TaskRunResult, load_runtime_config
from backend.models.state import RunState, WorkflowState
from backend.models.task import TaskType, WorkOrder
from backend.orchestrator.state_machine import StateManager
from backend.orchestrator.progress import calculate_progress
from backend.orchestrator.day_runner import DayRunner
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
        project_registry: ProjectRegistry | None = None,
        task_registry: TaskRegistry | None = None,
        discovery_registry: DiscoveryRegistry | None = None,
        fault_registry: FaultRegistry | None = None,
        worktree_root: Path | None = None,
        plan_registry: Any | None = None,
    ) -> None:
        self.store = state_store
        self.state_manager = StateManager()
        self.budgets = TokenBudgetManager(load_budget_config(config_path) if config_path else None)
        project_root = Path(__file__).resolve().parents[2]
        self.project_root = project_root
        self.runtime = runtime_config or load_runtime_config(project_root / "config" / "runtime.yaml")
        self.projects = project_registry or load_project_registry(project_root / "config" / "projects.yaml")
        self.tasks = task_registry or load_task_registry(project_root / "config" / "tasks.yaml")
        self.plans = plan_registry or load_plan_registry(project_root / "config" / "plans.yaml")
        self.orchestration = load_orchestration_config(project_root / "config" / "orchestration.yaml")
        self.model_profiles = load_model_profile_registry(project_root / "config" / "model_profiles.yaml")
        self.model_router = ModelRouter(self.model_profiles)
        self.discoveries = discovery_registry or load_discovery_registry(project_root / "config" / "discovery.yaml")
        self.faults = fault_registry or load_fault_registry(project_root / "config" / "faults.yaml")
        self.experiments = load_experiments(project_root / "config" / "experiments.yaml")
        self.worktree_root = (worktree_root or project_root / "state" / "worktrees").resolve()
        self.smoke_workspace = SmokeWorkspace(smoke_root or project_root / "state" / "smoke")
        self.real_runner = real_runner or RealCodexRunner(self.runtime.codex)
        role_workspace = self._codex_role_workspace_root()
        self.codex_architect = (
            CodexArchitectProvider(self.real_runner, role_workspace)
            if self.runtime.codex.mode == CodexMode.REAL else MockCodexArchitectProvider()
        )
        self.codex_reviewer = CodexReviewerProvider(self.real_runner, role_workspace)
        self.timeline: list[AuditEvent] = []
        self._load()
        self.day_runner = DayRunner(
            self.plans, self.tasks, self._run_day_task,
            architects={
                "mock": MockDayArchitect(), "codex": self.codex_architect,
                "openai": OpenAIDayArchitect(self.orchestration.orchestration.architect),
            },
            evaluators={"mock": MockSemanticEvaluator(), "openai": OpenAISemanticEvaluator(self.orchestration.orchestration.evaluator)},
            provider_budgets={
                "architect": self.orchestration.orchestration.architect_budget,
                "evaluator": self.orchestration.orchestration.evaluator_budget,
                "codex": ProviderBudget(
                    daily_input_tokens=self.budgets.config.codex.daily_input_tokens,
                    daily_output_tokens=self.budgets.config.codex.daily_output_tokens,
                    max_calls=50,
                ),
            },
            model_router=self.model_router,
            persist=self._save_day_state, audit=self._day_audit,
            saved=self.data.get("day_orchestration"),
        )

    @staticmethod
    def _codex_role_workspace_root() -> Path:
        """Keep read-only role calls outside any repository's inherited context."""
        configured = os.environ.get("AI_CONTROL_CENTER_CODEX_ROLE_WORKSPACE")
        if configured:
            return Path(configured).resolve()
        local_data = os.environ.get("LOCALAPPDATA")
        base = Path(local_data) if local_data else Path(tempfile.gettempdir())
        return (base / "AI-Control-Center" / "codex-roles").resolve()

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
            "project_smoke_results": [],
            "task_runs": [],
            "day_orchestration": {},
            "task_discoveries": [],
            "fault_repair_runs": [],
            "experiment_runs": [],
            "goal_plans": [],
            "escalation_validations": [],
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
            "day": self.day_runner.view(),
        }

    def runtime_view(self) -> dict[str, Any]:
        return self.runtime.model_dump(mode="json")

    def record_autostart_enabled(self) -> None:
        """Persist the explicit local automatic-start choice without OS details."""
        self._event(
            "SYSTEM", AuditEventType.DAILY_OPERATION_AUTOSTART,
            "Windows automatic startup enabled for AI Control Center.",
            details={"action": "ENABLED"},
        )
        self._save()

    def configured_tasks(self) -> list[dict[str, str]]:
        return self.tasks.metadata()

    def configured_plans(self) -> list[dict[str, object]]:
        return self.plans.metadata()

    def configured_experiments(self) -> list[dict[str, object]]:
        return [{"experiment_id": item.experiment_id, "project_id": item.project_id, "model": item.model, "cases": item.cases} for item in self.experiments.values()]

    def goal_plans(self) -> list[dict[str, Any]]:
        return list(self.data["goal_plans"])

    def propose_goal(self, goal: str) -> dict[str, Any]:
        proposal = propose_goal(goal, set(self.experiments))
        payload = proposal.model_dump(mode="json")
        self.data["goal_plans"].append(payload)
        event_type = AuditEventType.GOAL_PLAN_PROPOSED if proposal.status == GoalPlanStatus.PROPOSED else AuditEventType.GOAL_PLAN_REJECTED
        self._event("GOAL", event_type, f"Goal plan {proposal.status.value.lower()}: {proposal.policy_reason}", details={"goal_id": proposal.goal_id, "status": proposal.status.value, "target_type": proposal.target_type, "target_id": proposal.target_id, "policy_reason": proposal.policy_reason})
        self._save()
        return payload

    def execute_goal(self, goal_id: str) -> dict[str, Any]:
        stored = next((item for item in self.data["goal_plans"] if item["goal_id"] == goal_id), None)
        if stored is None:
            return {"error_code": "GOAL_PLAN_NOT_FOUND"}
        proposal = GoalPlan.model_validate(stored)
        if proposal.status != GoalPlanStatus.PROPOSED or proposal.target_type != "TRUSTED_EXPERIMENT" or not proposal.target_id:
            return {"error_code": "GOAL_PLAN_NOT_EXECUTABLE"}
        result = self.run_experiment(proposal.target_id)
        proposal.status, proposal.executed_at, proposal.execution_result = GoalPlanStatus.EXECUTED, datetime.now(timezone.utc), result["outcome"]
        stored.update(proposal.model_dump(mode="json"))
        self._event("GOAL", AuditEventType.GOAL_PLAN_EXECUTED, f"Goal plan executed: {proposal.target_id}", details={"goal_id": proposal.goal_id, "target_type": proposal.target_type, "target_id": proposal.target_id, "outcome": proposal.execution_result})
        self._save()
        return {"goal_plan": stored, "result": result}

    def run_experiment(self, experiment_id: str) -> dict[str, Any]:
        started = datetime.now(timezone.utc)
        definition = self.experiments.get(experiment_id)
        if definition is None:
            return ExperimentRun(experiment_id=experiment_id, project_id="unconfigured", started_at=started, outcome=ExperimentOutcome.CONFIGURATION_BLOCKED, classification_reason="EXPERIMENT_NOT_CONFIGURED").model_dump(mode="json")
        project = self.projects.get(definition.project_id)
        root = project.path.resolve() if project else None
        runner = (root / definition.runner).resolve() if root else None
        if not root or not runner or not runner.is_file() or not runner.is_relative_to(root):
            result = ExperimentRun(experiment_id=experiment_id, project_id=definition.project_id, started_at=started, completed_at=datetime.now(timezone.utc), outcome=ExperimentOutcome.CONFIGURATION_BLOCKED, classification_reason="TRUSTED_RUNNER_UNAVAILABLE")
            return self._finish_experiment(result)
        command = [sys.executable, str(runner), "--engine", "ollama", "--model", definition.model, "--cases", ",".join(definition.cases), "--timeout", str(definition.timeout_seconds), "--output-root", definition.output_root]
        try:
            completed = subprocess.run(command, cwd=root, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=definition.timeout_seconds + 30, check=False)
            payload = json.loads(completed.stdout.strip().splitlines()[-1]) if completed.stdout.strip() else {}
        except subprocess.TimeoutExpired:
            result = ExperimentRun(experiment_id=experiment_id, project_id=definition.project_id, started_at=started, completed_at=datetime.now(timezone.utc), outcome=ExperimentOutcome.TIMEOUT, classification_reason="RUNNER_TIMEOUT", model=definition.model)
            return self._finish_experiment(result)
        except (OSError, json.JSONDecodeError):
            result = ExperimentRun(experiment_id=experiment_id, project_id=definition.project_id, started_at=started, completed_at=datetime.now(timezone.utc), outcome=ExperimentOutcome.HARNESS_FAILURE, classification_reason="RUNNER_OUTPUT_INVALID", model=definition.model)
            return self._finish_experiment(result)
        error = (payload.get("error") or {}).get("code")
        status = payload.get("status")
        outcome = ExperimentOutcome.RESULT_RECORDED if status == "completed" else ExperimentOutcome.MODEL_NOT_FOUND if error == "model_not_found" else ExperimentOutcome.ENGINE_UNAVAILABLE if error == "engine_unavailable" else ExperimentOutcome.CONFIGURATION_BLOCKED if status == "blocked" else ExperimentOutcome.MODEL_QUALITY_FINDING if status == "completed_with_errors" else ExperimentOutcome.HARNESS_FAILURE
        result = ExperimentRun(experiment_id=experiment_id, project_id=definition.project_id, started_at=started, completed_at=datetime.now(timezone.utc), outcome=outcome, runner_exit_code=completed.returncode, artifact_path=payload.get("output_directory"), model=definition.model, engine="ollama", response_count=int(payload.get("response_count", 0)), success_count=int(payload.get("success_count", 0)), failed_count=int(payload.get("failed_count", 0)), classification_reason=error or status or "RUNNER_UNKNOWN")
        return self._finish_experiment(result)

    def run_escalation_validation(self, scenario: str) -> dict[str, Any]:
        """Isolated, no-provider M21 contract check; never touches normal Day state."""
        if scenario not in {"transient-architect", "missing-runtime"}:
            return {"error_code": "ESCALATION_VALIDATION_NOT_CONFIGURED"}
        task = ConfiguredTask(task_id="VALIDATION-ONLY", project_id="validation", title="Validation-only deterministic task", task_type=TaskType.CODE_FIX, precheck=TaskCommand(argv=["python", "-c", "pass"]), postcheck=TaskCommand(argv=["python", "-c", "pass"]), allowed_files=["validation-only"], context_files=["validation-only"], requires_codex=False)
        plan = DayPlan(plan_id="validation-only", title="Validation-only", task_ids=[task.task_id], architect_provider="validation", continuous_mode_supported=True)

        class ValidationArchitect:
            calls = 0
            def choose(self, request, execution):
                self.calls += 1
                if scenario == "transient-architect" and self.calls == 1:
                    raise ProviderRequestError("CODEX_TIMEOUT", "validation-only transient timeout")
                if scenario == "missing-runtime":
                    raise ProviderRequestError("CODEX_NOT_FOUND", "validation-only missing runtime")
                return ArchitectDecision(task_id="VALIDATION-ONLY", reason="validation-only trusted task")

        runner = DayRunner(DayPlanRegistry(plans={plan.plan_id: plan}), TaskRegistry(tasks={task.task_id: task}), lambda *_args, **_kwargs: {"task_id": task.task_id, "final_result": "COMPLETE_NO_CHANGE", "codex_attempts": [], "codex_invoked": False}, architects={"validation": ValidationArchitect()})
        result = runner.start(plan.plan_id, mode=DayExecutionMode.CONTINUOUS)
        payload = {"scenario": scenario, "isolated": True, "normal_day_unchanged": True, "result": result}
        self.data["escalation_validations"].append(payload)
        self._event("VALIDATION", AuditEventType.DAY_ESCALATION, f"Validation-only escalation: {scenario}", details=payload)
        self._save()
        return payload

    def _finish_experiment(self, result: ExperimentRun) -> dict[str, Any]:
        payload = result.model_dump(mode="json")
        self.data["experiment_runs"].append(payload)
        self._event(result.experiment_id, AuditEventType.EXPERIMENT_RESULT, f"Experiment {result.outcome.value}", details=payload)
        self._save()
        return payload

    def start_day(self, plan_id: str, *, mode: DayExecutionMode = DayExecutionMode.SINGLE_STEP) -> dict[str, Any]:
        return self.day_runner.start(plan_id, mode=mode)

    def resume_day(self, *, mode: DayExecutionMode | None = None) -> dict[str, Any]:
        return self.day_runner.resume(mode=mode)

    def stop_day(self) -> dict[str, Any]:
        return self.day_runner.stop()

    def day_status(self) -> dict[str, Any]:
        return self.day_runner.view()

    def _run_day_task(self, task_id: str, max_codex_attempts: int | None = None, repair_instruction: str | None = None, codex_routing_selector: Callable[[int, int], object | None] | None = None) -> dict[str, Any]:
        # The current configured real task set is deterministic. Semantic task
        # adapters may consume this bounded instruction in a later integration.
        # Codex CLI capability mapping is intentionally not guessed. The
        # DayRunner selector is invoked only after deterministic CODE_FIX triage.
        return self.run_task(task_id, max_codex_attempts=max_codex_attempts, codex_routing_selector=codex_routing_selector)

    def _save_day_state(self, snapshot: dict[str, Any]) -> None:
        self.data["day_orchestration"] = snapshot
        self._save()

    def _day_audit(self, task_id: str, event_name: str, details: dict[str, Any]) -> None:
        self._event(task_id, AuditEventType(event_name), f"Day orchestration: {event_name}", details=details)

    def discover_failing_task(self, discovery_id: str) -> dict[str, Any]:
        """Run trusted, deterministic candidate checks without invoking Codex."""
        definition = self.discoveries.get(discovery_id)
        started = datetime.now(timezone.utc)
        run_id = uuid4().hex
        if definition is None:
            return self._discovery_finish(FailingTaskDiscoveryResult(
                run_id=run_id, discovery_id=discovery_id, project_id="unconfigured", started_at=started,
                completed_at=datetime.now(timezone.utc), final_result="FAILED", error_code="DISCOVERY_NOT_CONFIGURED",
            ))
        project = self.projects.get(definition.project_id)
        if project is None:
            return self._discovery_finish(FailingTaskDiscoveryResult(
                run_id=run_id, discovery_id=discovery_id, project_id=definition.project_id, started_at=started,
                completed_at=datetime.now(timezone.utc), final_result="FAILED", error_code="DISCOVERY_PROJECT_NOT_CONFIGURED",
            ))
        source_root = project.path.resolve()
        validation_error, _ = self._validate_project_repository(source_root)
        if validation_error:
            return self._discovery_finish(FailingTaskDiscoveryResult(
                run_id=run_id, discovery_id=discovery_id, project_id=definition.project_id, started_at=started,
                completed_at=datetime.now(timezone.utc), final_result="FAILED", error_code=validation_error,
            ))
        try:
            working_directory = self._task_working_directory(source_root, definition.working_directory)
        except ValueError:
            return self._discovery_finish(FailingTaskDiscoveryResult(
                run_id=run_id, discovery_id=discovery_id, project_id=definition.project_id, started_at=started,
                completed_at=datetime.now(timezone.utc), final_result="FAILED", error_code="DISCOVERY_WORKING_DIRECTORY_ESCAPE",
            ))
        self._event("DISCOVERY", AuditEventType.DETERMINISTIC_CHECK, f"{discovery_id} deterministic candidate discovery started", details={"candidate_count": len(definition.candidate_case_ids)})
        result = DeterministicTaskDiscovery().discover(
            definition,
            run_id=run_id,
            started_at=started,
            run_command=self._run_task_command,
            working_directory=working_directory,
            artifact_root=self._discovery_artifact_root(run_id),
        )
        self._event("DISCOVERY", AuditEventType.DETERMINISTIC_CHECK, f"{discovery_id} discovery {result.final_result}", details={"cases_checked": len(result.cases), "selected_case_id": result.selected_case_id})
        return self._discovery_finish(result)

    def _discovery_finish(self, result: FailingTaskDiscoveryResult) -> dict[str, Any]:
        self.data.setdefault("task_discoveries", []).append(result.model_dump(mode="json"))
        self._save()
        return result.model_dump(mode="json")

    def run_fault_repair(self, fault_id: str) -> dict[str, Any]:
        """Validate a trusted repair path without ever mutating the source checkout."""
        started = datetime.now(timezone.utc)
        run_id = uuid4().hex
        profile = self.faults.get(fault_id)
        if profile is None:
            return self._fault_finish(FaultRepairResult(
                run_id=run_id, fault_id=fault_id, task_id="unconfigured", project_id="unconfigured",
                state=WorkflowState.FAILED.value, final_result="FAILED", error_code="FAULT_NOT_CONFIGURED",
            ))
        try:
            profile.validate_scope()
        except ValueError:
            return self._fault_finish(FaultRepairResult(
                run_id=run_id, fault_id=fault_id, task_id=profile.task_id, project_id=profile.project_id,
                target_file=profile.target_file, state=WorkflowState.HUMAN_REVIEW.value, final_result="HUMAN_REVIEW",
                human_review_reason="fault profile does not meet controlled repair scope", error_code="FAULT_SOURCE_MISMATCH",
            ))
        common: dict[str, Any] = {
            "run_id": run_id, "fault_id": profile.fault_id, "task_id": profile.task_id,
            "project_id": profile.project_id, "target_file": profile.target_file,
        }
        if self.runtime.codex.mode != CodexMode.REAL:
            return self._fault_finish(FaultRepairResult(
                **common, state=WorkflowState.FAILED.value, final_result="FAILED", error_code="REAL_MODE_REQUIRED",
            ))
        project = self.projects.get(profile.project_id)
        if project is None:
            return self._fault_finish(FaultRepairResult(
                **common, state=WorkflowState.FAILED.value, final_result="FAILED", error_code="PROJECT_NOT_CONFIGURED",
            ))
        source_root = project.path.resolve()
        validation_error, source_status, source_head = self._task_source_validation(source_root)
        if validation_error or source_head is None:
            return self._fault_finish(FaultRepairResult(
                **common, state=WorkflowState.FAILED.value, final_result="FAILED", error_code=validation_error or "PROJECT_HEAD_UNAVAILABLE",
            ))
        if profile.target_file in source_status:
            return self._fault_finish(FaultRepairResult(
                **common, source_head_sha=source_head, state=WorkflowState.HUMAN_REVIEW.value, final_result="HUMAN_REVIEW",
                human_review_reason="source target file is already dirty", error_code="SOURCE_TASK_DEPENDENCY_DIRTY",
            ))
        source_target = (source_root / profile.target_file).resolve()
        try:
            source_target.relative_to(source_root)
            if not source_target.is_file():
                raise OSError("configured fault target is not a file")
        except (ValueError, OSError):
            return self._fault_finish(FaultRepairResult(
                **common, source_head_sha=source_head, state=WorkflowState.HUMAN_REVIEW.value, final_result="HUMAN_REVIEW",
                human_review_reason="configured fault target is unavailable", error_code="FAULT_TARGET_UNAVAILABLE",
            ))
        if self.state_manager.current.state != WorkflowState.IDLE:
            self._transition(profile.task_id, WorkflowState.IDLE, "previous terminal workflow reset")
        self.state_manager.start_task(profile.task_id)
        self._transition(profile.task_id, WorkflowState.PLANNING, "controlled fault repair started")
        worktree, branch, worktree_error = self._create_fault_worktree(source_root, source_head, profile, run_id)
        if worktree_error or worktree is None:
            self._transition(profile.task_id, WorkflowState.HUMAN_REVIEW, "isolated worktree creation failed")
            return self._fault_finish(FaultRepairResult(
                **common, source_head_sha=source_head, state=WorkflowState.HUMAN_REVIEW.value, final_result="HUMAN_REVIEW",
                human_review_reason="isolated worktree could not be created", error_code=worktree_error or "WORKTREE_CREATION_FAILED",
            ))
        common["worktree_path"] = str(worktree)
        self._event(profile.task_id, AuditEventType.SMOKE_STARTED, f"{profile.task_id} WORKTREE CREATED", details={"fault_id": profile.fault_id, "worktree": str(worktree), "branch": branch, "source_head_sha": source_head})
        try:
            working_directory = self._task_working_directory(worktree, profile.working_directory)
        except ValueError:
            self._transition(profile.task_id, WorkflowState.HUMAN_REVIEW, "fault working directory escaped worktree")
            return self._fault_finish(FaultRepairResult(
                **common, source_head_sha=source_head, state=WorkflowState.HUMAN_REVIEW.value, final_result="HUMAN_REVIEW",
                human_review_reason="configured working directory escaped worktree", error_code="WORKTREE_PATH_ESCAPE",
            ))
        self._transition(profile.task_id, WorkflowState.PRECHECK, "clean worktree baseline")
        baseline = self._run_task_command(profile.baseline, working_directory, self._fault_artifact_root(run_id, "baseline"))
        if not baseline.passed:
            self._event(profile.task_id, AuditEventType.DETERMINISTIC_CHECK, f"{profile.task_id} BASELINE FAIL", details=baseline.model_dump())
            self._transition(profile.task_id, WorkflowState.HUMAN_REVIEW, "baseline did not pass")
            return self._fault_finish(FaultRepairResult(
                **common, source_head_sha=source_head, baseline_result="FAIL", baseline=baseline,
                state=WorkflowState.HUMAN_REVIEW.value, final_result="HUMAN_REVIEW", human_review_reason="clean worktree baseline failed", error_code="BASELINE_FAILED",
            ))
        self._event(profile.task_id, AuditEventType.DETERMINISTIC_CHECK, f"{profile.task_id} BASELINE PASS", details=baseline.model_dump())
        injected, injection_error = self._inject_fault(worktree, profile)
        if not injected:
            self._transition(profile.task_id, WorkflowState.HUMAN_REVIEW, "trusted fault injection could not be applied")
            return self._fault_finish(FaultRepairResult(
                **common, source_head_sha=source_head, baseline_result="PASS", baseline=baseline,
                state=WorkflowState.HUMAN_REVIEW.value, final_result="HUMAN_REVIEW", human_review_reason="trusted fault injection failed", error_code=injection_error,
            ))
        injection_status = self._project_status_snapshot(worktree)
        if injection_status is None:
            self._transition(profile.task_id, WorkflowState.HUMAN_REVIEW, "worktree status unavailable after fault injection")
            return self._fault_finish(FaultRepairResult(
                **common, source_head_sha=source_head, baseline_result="PASS", baseline=baseline, fault_injected=True,
                state=WorkflowState.HUMAN_REVIEW.value, final_result="HUMAN_REVIEW", human_review_reason="worktree status unavailable", error_code="WORKTREE_GIT_UNAVAILABLE",
            ))
        self._event(profile.task_id, AuditEventType.DETERMINISTIC_CHECK, f"{profile.task_id} FAULT INJECTED", details={"target_file": profile.target_file})
        precheck = self._run_task_command(profile.postcheck, working_directory, self._fault_artifact_root(run_id, "precheck"))
        self._transition(profile.task_id, WorkflowState.RUNNING_TEST, "faulted deterministic precheck")
        if precheck.passed:
            self._event(profile.task_id, AuditEventType.DETERMINISTIC_CHECK, f"{profile.task_id} PRECHECK unexpected PASS", details=precheck.model_dump())
            self._transition(profile.task_id, WorkflowState.FAILED, "fault injection did not fail its deterministic check")
            return self._fault_finish(FaultRepairResult(
                **common, source_head_sha=source_head, baseline_result="PASS", baseline=baseline, fault_injected=True,
                precheck_result="PASS", precheck=precheck, state=WorkflowState.FAILED.value, final_result="FAILED", error_code="FAULT_INJECTION_INVALID",
            ))
        if not self._is_expected_fault_failure(precheck, profile):
            self._event(profile.task_id, AuditEventType.TRIAGE, f"{profile.task_id} PRECHECK infrastructure or unexpected failure", details=precheck.model_dump())
            self._transition(profile.task_id, WorkflowState.TRIAGE, "precheck failure classified")
            self._transition(profile.task_id, WorkflowState.HUMAN_REVIEW, "fault precheck was not the configured code failure")
            return self._fault_finish(FaultRepairResult(
                **common, source_head_sha=source_head, baseline_result="PASS", baseline=baseline, fault_injected=True,
                precheck_result="FAIL", precheck=precheck, triage_result="INFRASTRUCTURE_FAILURE" if precheck.error_code else "UNEXPECTED_FAILURE",
                state=WorkflowState.HUMAN_REVIEW.value, final_result="HUMAN_REVIEW", human_review_reason="fault precheck did not match expected deterministic evidence",
                error_code=precheck.error_code or "PRECHECK_UNEXPECTED_FAILURE",
            ))
        self._event(profile.task_id, AuditEventType.DETERMINISTIC_CHECK, f"{profile.task_id} PRECHECK FAIL", details=precheck.model_dump())
        self._transition(profile.task_id, WorkflowState.TRIAGE, "fault precheck classified CODE_FIX")
        return self._run_fault_codex_attempts(profile, common, source_head, working_directory, worktree, injection_status, baseline, precheck)

    def _fault_finish(self, result: FaultRepairResult) -> dict[str, Any]:
        self.data.setdefault("fault_repair_runs", []).append(result.model_dump(mode="json"))
        self._save()
        return result.model_dump(mode="json")

    def _run_fault_codex_attempts(
        self,
        profile: FaultProfile,
        common: dict[str, Any],
        source_head: str,
        working_directory: Path,
        worktree: Path,
        injection_status: dict[str, str],
        baseline: CommandRunResult,
        precheck: CommandRunResult,
    ) -> dict[str, Any]:
        attempts: list[CodexAttemptResult] = []
        aggregate = TokenUsage()
        retry_number = 0
        while True:
            budget = self.budgets.check(TokenUsage(), retry_count=retry_number)
            if budget != BudgetDecision.ALLOWED:
                self._transition(profile.task_id, WorkflowState.HUMAN_REVIEW, "pre-execution budget guard blocked Codex")
                return self._fault_finish(FaultRepairResult(
                    **common, source_head_sha=source_head, baseline_result="PASS", baseline=baseline, fault_injected=True,
                    precheck_result="FAIL", precheck=precheck, triage_result="CODE_FIX", codex_attempts=attempts,
                    token_usage=aggregate, state=WorkflowState.HUMAN_REVIEW.value, final_result="HUMAN_REVIEW",
                    human_review_reason=budget.value, error_code=budget.value,
                ))
            context_files, context_error = self._load_fault_context_files(worktree, profile)
            if context_error:
                self._transition(profile.task_id, WorkflowState.HUMAN_REVIEW, "configured context file unavailable")
                return self._fault_finish(FaultRepairResult(
                    **common, source_head_sha=source_head, baseline_result="PASS", baseline=baseline, fault_injected=True,
                    precheck_result="FAIL", precheck=precheck, triage_result="INFRASTRUCTURE_FAILURE", codex_attempts=attempts,
                    token_usage=aggregate, state=WorkflowState.HUMAN_REVIEW.value, final_result="HUMAN_REVIEW",
                    human_review_reason=context_error, error_code="CONTEXT_FILE_UNAVAILABLE",
                ))
            work_order = WorkOrder(
                task_id=profile.task_id,
                goal=f"Restore deterministic correctness for {profile.base_case}.",
                task_type=TaskType.CODE_FIX,
                allowed_files=profile.allowed_files,
                acceptance_tests=[" ".join(profile.postcheck.argv)],
                max_retry=profile.max_retry,
                needs_codex=True,
            )
            excerpt = (precheck.stderr or precheck.stdout or "deterministic precheck failed")[:2000]
            context = ContextBroker().build(
                work_order, error_excerpt=excerpt,
                configuration={"working_directory": str(working_directory), "postcheck_argv": " ".join(profile.postcheck.argv), "base_case": profile.base_case},
                retry_number=retry_number, context_files=context_files,
            )
            prompt = self._task_prompt(context)
            self._transition(profile.task_id, WorkflowState.CODEX_FIX, f"Codex attempt {retry_number + 1} authorized")
            self._event(profile.task_id, AuditEventType.CONTEXT_CREATED, f"{profile.task_id} minimal context package built", details={"context_character_count": len(prompt), "context_byte_count": len(prompt.encode("utf-8")), "context_files": list(context_files)})
            self._save()
            execution = self.real_runner.run_worktree_task(working_directory, prompt)
            diagnostics = execution.diagnostics
            attempt = CodexAttemptResult(
                attempt=retry_number + 1, exit_code=execution.exit_code,
                thread_started=diagnostics.thread_started if diagnostics else False,
                turn_started=diagnostics.turn_started if diagnostics else False,
                turn_completed=diagnostics.turn_completed if diagnostics else False,
                gross_input_tokens=execution.token_usage.gross_input_tokens, cached_input_tokens=execution.token_usage.cached_input_tokens,
                uncached_input_tokens=execution.token_usage.uncached_input_tokens, output_tokens=execution.token_usage.output_tokens,
                error_code=execution.error_code,
            )
            attempts.append(attempt)
            aggregate = TokenUsage(input_tokens=aggregate.input_tokens + execution.token_usage.input_tokens, cached_input_tokens=aggregate.cached_input_tokens + execution.token_usage.cached_input_tokens, output_tokens=aggregate.output_tokens + execution.token_usage.output_tokens, available=aggregate.available or execution.token_usage.available)
            self._record_project_usage(profile.task_id, execution.token_usage)
            self._event(profile.task_id, AuditEventType.CODEX_RESULT, f"Codex attempt {attempt.attempt} COMPLETE", details={"attempt": attempt.model_dump(), "status": execution.status})
            if execution.status != "completed" or execution.exit_code != 0 or not attempt.turn_completed:
                self._transition(profile.task_id, WorkflowState.FAILED, "Codex execution failed")
                return self._fault_finish(FaultRepairResult(
                    **common, source_head_sha=source_head, baseline_result="PASS", baseline=baseline, fault_injected=True,
                    precheck_result="FAIL", precheck=precheck, triage_result="CODE_FIX", codex_invoked=True, codex_attempts=attempts,
                    token_usage=aggregate, context_character_count=len(prompt), context_byte_count=len(prompt.encode("utf-8")),
                    state=WorkflowState.FAILED.value, final_result="FAILED", error_code=execution.error_code or "CODEX_EXECUTION_FAILED",
                ))
            current_status = self._project_status_snapshot(worktree)
            if current_status is None:
                self._transition(profile.task_id, WorkflowState.HUMAN_REVIEW, "worktree status unavailable after Codex")
                return self._fault_finish(FaultRepairResult(
                    **common, source_head_sha=source_head, baseline_result="PASS", baseline=baseline, fault_injected=True,
                    precheck_result="FAIL", precheck=precheck, triage_result="CODE_FIX", codex_invoked=True, codex_attempts=attempts,
                    token_usage=aggregate, state=WorkflowState.HUMAN_REVIEW.value, final_result="HUMAN_REVIEW",
                    human_review_reason="worktree status unavailable", error_code="WORKTREE_GIT_UNAVAILABLE",
                ))
            repair_delta = self._snapshot_status_delta(injection_status, current_status)
            scope = ScopeGuard().check(work_order, repair_delta)
            if not scope.allowed:
                self._event(profile.task_id, AuditEventType.CODEX_RESULT, "Scope Guard FAIL", details={"injected_file": profile.target_file, "repair_delta_files": repair_delta, "out_of_scope": scope.out_of_scope})
                self._transition(profile.task_id, WorkflowState.HUMAN_REVIEW, "Codex changed files outside configured repair scope")
                return self._fault_finish(FaultRepairResult(
                    **common, source_head_sha=source_head, baseline_result="PASS", baseline=baseline, fault_injected=True,
                    precheck_result="FAIL", precheck=precheck, triage_result="CODE_FIX", codex_invoked=True, codex_attempts=attempts,
                    repair_delta_files=repair_delta, scope_guard_result="FAIL", token_usage=aggregate, context_character_count=len(prompt), context_byte_count=len(prompt.encode("utf-8")),
                    state=WorkflowState.HUMAN_REVIEW.value, final_result="HUMAN_REVIEW", human_review_reason="scope guard failed", error_code="SCOPE_GUARD_FAILED",
                ))
            self._event(profile.task_id, AuditEventType.CODEX_RESULT, "Scope Guard PASS", details={"injected_file": profile.target_file, "repair_delta_files": repair_delta})
            self._transition(profile.task_id, WorkflowState.RUNNING_TEST, "scope guard passed")
            postcheck = self._run_task_command(profile.postcheck, working_directory, self._fault_artifact_root(common["run_id"], f"postcheck-{attempt.attempt}"))
            if not postcheck.passed:
                self._event(profile.task_id, AuditEventType.TEST_RESULT, "Deterministic POSTCHECK FAIL", details=postcheck.model_dump())
                if retry_number >= profile.max_retry:
                    self._transition(profile.task_id, WorkflowState.TRIAGE, "postcheck failure requires bounded repair decision")
                    self._transition(profile.task_id, WorkflowState.HUMAN_REVIEW, "bounded repair attempts exhausted")
                    return self._fault_finish(FaultRepairResult(
                        **common, source_head_sha=source_head, baseline_result="PASS", baseline=baseline, fault_injected=True,
                        precheck_result="FAIL", precheck=precheck, triage_result="CODE_FIX", codex_invoked=True, codex_attempts=attempts,
                        repair_delta_files=repair_delta, scope_guard_result="PASS", postcheck_result="FAIL", postcheck=postcheck, token_usage=aggregate,
                        context_character_count=len(prompt), context_byte_count=len(prompt.encode("utf-8")), state=WorkflowState.HUMAN_REVIEW.value,
                        final_result="HUMAN_REVIEW", human_review_reason="bounded repair attempts exhausted", error_code="RETRY_LIMIT_EXCEEDED",
                    ))
                self._transition(profile.task_id, WorkflowState.TRIAGE, "deterministic postcheck failed")
                self.state_manager.increment_retry()
                retry_number += 1
                continue
            self._event(profile.task_id, AuditEventType.TEST_RESULT, "Deterministic POSTCHECK PASS", details=postcheck.model_dump())
            self._transition(profile.task_id, WorkflowState.EVALUATING, "deterministic postcheck passed")
            original_match, comparison_method = self._git_original_file_match(worktree, profile.target_file)
            if original_match is None:
                self._transition(profile.task_id, WorkflowState.HUMAN_REVIEW, "Git comparison of repaired target failed")
                return self._fault_finish(FaultRepairResult(
                    **common, source_head_sha=source_head, baseline_result="PASS", baseline=baseline, fault_injected=True,
                    precheck_result="FAIL", precheck=precheck, triage_result="CODE_FIX", codex_invoked=True, codex_attempts=attempts,
                    repair_delta_files=repair_delta, scope_guard_result="PASS", postcheck_result="PASS", postcheck=postcheck,
                    original_file_match_method=comparison_method, token_usage=aggregate,
                    context_character_count=len(prompt), context_byte_count=len(prompt.encode("utf-8")), state=WorkflowState.HUMAN_REVIEW.value,
                    final_result="HUMAN_REVIEW", human_review_reason="Git comparison of repaired target failed", error_code="ORIGINAL_FILE_COMPARISON_FAILED",
                ))
            if not original_match:
                self._transition(profile.task_id, WorkflowState.HUMAN_REVIEW, "passing repair differs from original clean source")
                return self._fault_finish(FaultRepairResult(
                    **common, source_head_sha=source_head, baseline_result="PASS", baseline=baseline, fault_injected=True,
                    precheck_result="FAIL", precheck=precheck, triage_result="CODE_FIX", codex_invoked=True, codex_attempts=attempts,
                    repair_delta_files=repair_delta, scope_guard_result="PASS", postcheck_result="PASS", postcheck=postcheck, original_file_match=False, original_file_match_method=comparison_method, token_usage=aggregate,
                    context_character_count=len(prompt), context_byte_count=len(prompt.encode("utf-8")), state=WorkflowState.HUMAN_REVIEW.value,
                    final_result="HUMAN_REVIEW", human_review_reason="passing repair differs from original clean source", error_code="ORIGINAL_FILE_MISMATCH",
                ))
            self._transition(profile.task_id, WorkflowState.COMPLETE, "postcheck passed and original file was restored")
            return self._fault_finish(FaultRepairResult(
                **common, source_head_sha=source_head, baseline_result="PASS", baseline=baseline, fault_injected=True,
                precheck_result="FAIL", precheck=precheck, triage_result="CODE_FIX", codex_invoked=True, codex_attempts=attempts,
                repair_delta_files=repair_delta, scope_guard_result="PASS", postcheck_result="PASS", postcheck=postcheck, original_file_match=True, original_file_match_method=comparison_method, token_usage=aggregate,
                context_character_count=len(prompt), context_byte_count=len(prompt.encode("utf-8")), state=WorkflowState.COMPLETE.value, final_result="COMPLETE",
            ))

    def _create_fault_worktree(self, source_root: Path, head: str, profile: FaultProfile, run_id: str) -> tuple[Path | None, str | None, str | None]:
        self.worktree_root.mkdir(parents=True, exist_ok=True)
        candidate = (self.worktree_root / run_id).resolve()
        try:
            candidate.relative_to(self.worktree_root)
        except ValueError:
            return None, None, "WORKTREE_PATH_ESCAPE"
        if candidate.exists():
            return None, None, "WORKTREE_PATH_ALREADY_EXISTS"
        branch = f"agent/{profile.task_id.lower()}-{run_id[:8]}"
        try:
            completed = subprocess.run(
                ["git", "-C", str(source_root), "-c", f"safe.directory={source_root}", "worktree", "add", "-b", branch, str(candidate), head],
                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60, check=False, shell=False,
            )
        except (FileNotFoundError, OSError, subprocess.TimeoutExpired):
            return None, None, "WORKTREE_CREATION_FAILED"
        if completed.returncode != 0 or not candidate.is_dir():
            return None, None, "WORKTREE_CREATION_FAILED"
        return candidate, branch, None

    @staticmethod
    def _inject_fault(worktree: Path, profile: FaultProfile) -> tuple[bool, str | None]:
        target = (worktree / profile.target_file).resolve()
        try:
            target.relative_to(worktree.resolve())
            content = target.read_bytes()
        except (ValueError, OSError):
            return False, "FAULT_TARGET_UNAVAILABLE"
        try:
            operator_offset = locate_qa_shipment_gt_operator(content)
        except ValueError:
            return False, "FAULT_SOURCE_MISMATCH"
        if operator_offset is None:
            return False, "FAULT_SOURCE_MISMATCH"
        mutated = content[:operator_offset] + b">=" + content[operator_offset + 1:]
        if len(mutated) != len(content) + 1 or mutated[:operator_offset] != content[:operator_offset] or mutated[operator_offset + 2:] != content[operator_offset + 1:]:
            return False, "FAULT_SOURCE_MISMATCH"
        try:
            import ast
            ast.parse(mutated.decode("utf-8"))
        except (SyntaxError, UnicodeError):
            return False, "FAULT_SOURCE_MISMATCH"
        try:
            target.write_bytes(mutated)
        except OSError:
            return False, "FAULT_INJECTION_WRITE_FAILED"
        return True, None

    @staticmethod
    def _is_expected_fault_failure(precheck: CommandRunResult, profile: FaultProfile) -> bool:
        evidence = (precheck.stdout or "") + "\n" + (precheck.stderr or "")
        return not precheck.error_code and precheck.exit_code == profile.expected_precheck_exit_code and profile.expected_precheck_text in evidence

    @staticmethod
    def _load_fault_context_files(worktree: Path, profile: FaultProfile) -> tuple[dict[str, str], str | None]:
        remaining = profile.context_max_characters
        contents: dict[str, str] = {}
        for relative in profile.context_files:
            path = (worktree / relative).resolve()
            try:
                path.relative_to(worktree.resolve())
                content = path.read_text(encoding="utf-8")
            except (ValueError, OSError, UnicodeError):
                return {}, f"configured context file is unavailable: {relative}"
            if len(content) > remaining:
                return {}, "configured context files exceed context bound"
            contents[relative] = content
            remaining -= len(content)
        return contents, None

    def _fault_artifact_root(self, run_id: str, stage: str) -> Path:
        root = (self.project_root / "state" / "fault-repair-artifacts" / run_id / stage).resolve()
        managed_root = (self.project_root / "state" / "fault-repair-artifacts").resolve()
        try:
            root.relative_to(managed_root)
        except ValueError as exc:
            raise ValueError("fault artifact path escaped managed state") from exc
        return root

    @staticmethod
    def _git_original_file_match(worktree: Path, target_file: str) -> tuple[bool | None, str]:
        """Use Git's normalized content comparison for the one trusted repair file."""
        root = worktree.resolve()
        target = (root / target_file).resolve()
        try:
            relative = target.relative_to(root).as_posix()
        except ValueError:
            return None, "git_diff_quiet"
        try:
            completed = subprocess.run(
                ["git", "-c", f"safe.directory={root}", "diff", "--quiet", "HEAD", "--", relative],
                cwd=root, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10, check=False, shell=False,
            )
        except (FileNotFoundError, OSError, subprocess.TimeoutExpired):
            return None, "git_diff_quiet"
        if completed.returncode == 0:
            return True, "git_diff_quiet"
        if completed.returncode == 1:
            return False, "git_diff_quiet"
        return None, "git_diff_quiet"

    @staticmethod
    def _snapshot_status_delta(before: dict[str, str], after: dict[str, str]) -> list[str]:
        """Report both additions and removals relative to the injected-fault baseline."""
        return sorted(path for path in set(before) | set(after) if before.get(path) != after.get(path))

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

    def run_project_smoke(self, project_id: str) -> dict[str, Any]:
        """Run the one fixed, deterministic fixture workflow for a configured project."""
        task_id = "CONTROL-CENTER-SMOKE-001"
        started = datetime.now(timezone.utc)
        run_id = uuid4().hex
        project = self.projects.get(project_id)
        if project is None:
            return self._project_smoke_finish(ProjectSmokeResult(
                run_id=run_id, project_id=project_id, state=WorkflowState.FAILED.value,
                start_time=started, end_time=datetime.now(timezone.utc), final_result="FAILED",
                error_code="PROJECT_NOT_CONFIGURED",
            ))
        root = project.path.resolve()
        if self.runtime.codex.mode != CodexMode.REAL:
            return self._project_smoke_finish(ProjectSmokeResult(
                run_id=run_id, project_id=project_id, project_path=str(root), state=WorkflowState.FAILED.value,
                start_time=started, end_time=datetime.now(timezone.utc), final_result="FAILED",
                error_code="REAL_MODE_REQUIRED",
            ))
        validation_error, baseline = self._validate_project_repository(root)
        if validation_error:
            return self._project_smoke_finish(ProjectSmokeResult(
                run_id=run_id, project_id=project_id, project_path=str(root), state=WorkflowState.FAILED.value,
                start_time=started, end_time=datetime.now(timezone.utc), final_result="FAILED",
                error_code=validation_error,
            ))
        budget_decision = self.budgets.check(TokenUsage(), retry_count=0)
        if budget_decision != BudgetDecision.ALLOWED:
            return self._project_smoke_finish(ProjectSmokeResult(
                run_id=run_id, project_id=project_id, project_path=str(root), state=WorkflowState.FAILED.value,
                start_time=started, end_time=datetime.now(timezone.utc), final_result="FAILED",
                error_code=budget_decision.value,
            ))

        if self.state_manager.current.state != WorkflowState.IDLE:
            self._transition(task_id, WorkflowState.IDLE, "previous terminal workflow reset")
        self.state_manager.start_task(task_id)
        self._transition(task_id, WorkflowState.PLANNING, "configured project smoke started")
        self._transition(task_id, WorkflowState.PRECHECK, "deterministic fixture precheck")
        fixture_directory = root / ".ai-control-center-smoke" / run_id
        target = fixture_directory / "status.txt"
        fixture_directory.mkdir(parents=True, exist_ok=False)
        target.write_text("FAIL", encoding="utf-8")
        fixture_relative = target.relative_to(root).as_posix()
        setup_state = self._project_status_snapshot(root)
        if setup_state is None:
            self._transition(task_id, WorkflowState.FAILED, "repository status became unavailable after fixture setup")
            return self._project_smoke_finish(ProjectSmokeResult(
                run_id=run_id, project_id=project_id, project_path=str(root), state=WorkflowState.FAILED.value,
                start_time=started, end_time=datetime.now(timezone.utc), fixture_path=fixture_relative,
                final_result="FAILED", error_code="PROJECT_STATUS_UNAVAILABLE",
            ))

        precheck = self._status_fixture_result(target)
        if precheck != "FAIL":
            self._event(task_id, AuditEventType.DETERMINISTIC_CHECK, f"{task_id} PRECHECK unexpected {precheck}", details={"result": precheck})
            self._transition(task_id, WorkflowState.FAILED, "fixture precheck unexpectedly passed")
            return self._project_smoke_finish(ProjectSmokeResult(
                run_id=run_id, project_id=project_id, project_path=str(root), state=WorkflowState.FAILED.value,
                start_time=started, end_time=datetime.now(timezone.utc), fixture_path=fixture_relative,
                precheck_result=precheck, final_result="FAILED", error_code="PRECHECK_UNEXPECTED_PASS",
            ))
        self._event(task_id, AuditEventType.DETERMINISTIC_CHECK, f"{task_id} PRECHECK FAIL", details={"result": "FAIL", "fixture": fixture_relative})
        self._transition(task_id, WorkflowState.RUNNING_TEST, "precheck recorded")
        self._transition(task_id, WorkflowState.TRIAGE, "deterministic fixture requires code change")
        work_order = WorkOrder(
            task_id=task_id,
            goal="Change the isolated status fixture from FAIL to PASS.",
            task_type=TaskType.CODE_FIX,
            allowed_files=[fixture_relative],
            acceptance_tests=["status.txt content equals PASS"],
            max_retry=0,
            needs_codex=True,
        )
        context = ContextBroker().build(
            work_order,
            error_excerpt="status.txt is FAIL.",
            configuration={"project_id": project_id, "working_directory": str(fixture_directory), "required_final_content": "PASS"},
        )
        self._transition(task_id, WorkflowState.CODEX_FIX, "minimal structured work order approved")
        self._event(task_id, AuditEventType.CONTEXT_CREATED, f"{task_id} minimal context package built", details={"allowed_files": context.allowed_files, "retry_number": context.retry_number})
        self._event(task_id, AuditEventType.SMOKE_STARTED, "Codex STARTED", details={"project_id": project_id, "fixture": fixture_relative})
        self._save()
        execution = self.real_runner.run_isolated_file_change(fixture_directory, target, "PASS")
        diagnostics = execution.diagnostics
        self._event(task_id, AuditEventType.SMOKE_RESULT, f"Codex COMPLETE exit={execution.exit_code if execution.exit_code is not None else 'unavailable'}", details={"exit_code": execution.exit_code, "status": execution.status, "token_usage": execution.token_usage.model_dump(), "diagnostics": diagnostics.model_dump(mode="json") if diagnostics else None})
        result_values = {
            "run_id": run_id, "project_id": project_id, "project_path": str(root), "fixture_path": fixture_relative,
            "precheck_result": "FAIL", "codex_invoked": True, "codex_exit_code": execution.exit_code,
            "thread_started": diagnostics.thread_started if diagnostics else False,
            "turn_started": diagnostics.turn_started if diagnostics else False,
            "turn_completed": diagnostics.turn_completed if diagnostics else False,
            "gross_input_tokens": execution.token_usage.gross_input_tokens,
            "cached_input_tokens": execution.token_usage.cached_input_tokens,
            "uncached_input_tokens": execution.token_usage.uncached_input_tokens,
            "output_tokens": execution.token_usage.output_tokens,
        }
        budget_warning = self._record_project_usage(task_id, execution.token_usage)
        if execution.status != "completed" or execution.exit_code != 0 or not result_values["turn_completed"]:
            self._transition(task_id, WorkflowState.FAILED, "Codex execution failed")
            return self._project_smoke_finish(ProjectSmokeResult(
                **result_values, state=WorkflowState.FAILED.value, start_time=started, end_time=datetime.now(timezone.utc),
                budget_warning=budget_warning, final_result="FAILED", error_code=execution.error_code or "CODEX_EXECUTION_FAILED",
            ))

        after_state = self._project_status_snapshot(root)
        if after_state is None:
            self._transition(task_id, WorkflowState.HUMAN_REVIEW, "repository status unavailable after Codex execution")
            return self._project_smoke_finish(ProjectSmokeResult(
                **result_values, state=WorkflowState.HUMAN_REVIEW.value, start_time=started, end_time=datetime.now(timezone.utc),
                budget_warning=budget_warning, final_result="HUMAN_REVIEW", error_code="PROJECT_STATUS_UNAVAILABLE",
            ))
        runtime_changes = self._snapshot_changes(setup_state, after_state)
        scope = ScopeGuard().check(work_order, runtime_changes)
        result_values["changed_files"] = runtime_changes
        result_values["scope_guard_result"] = "PASS" if scope.allowed else "FAIL"
        if not scope.allowed:
            self._event(task_id, AuditEventType.CODEX_RESULT, "Scope Guard FAIL", details={"out_of_scope": scope.out_of_scope, "baseline_file_count": len(baseline)})
            self._transition(task_id, WorkflowState.HUMAN_REVIEW, "Codex changed files outside the exact fixture scope")
            return self._project_smoke_finish(ProjectSmokeResult(
                **result_values, state=WorkflowState.HUMAN_REVIEW.value, start_time=started, end_time=datetime.now(timezone.utc),
                budget_warning=budget_warning, final_result="HUMAN_REVIEW", error_code="SCOPE_GUARD_FAILED",
            ))
        self._event(task_id, AuditEventType.CODEX_RESULT, "Scope Guard PASS", details={"changed_files": runtime_changes, "baseline_file_count": len(baseline)})
        self._transition(task_id, WorkflowState.RUNNING_TEST, "scope guard passed")
        postcheck = self._postcheck_status_fixture(target)
        result_values["postcheck_result"] = postcheck
        if postcheck != "PASS":
            self._event(task_id, AuditEventType.TEST_RESULT, "Deterministic POSTCHECK FAIL", details={"result": postcheck})
            self._transition(task_id, WorkflowState.FAILED, "deterministic postcheck failed")
            return self._project_smoke_finish(ProjectSmokeResult(
                **result_values, state=WorkflowState.FAILED.value, start_time=started, end_time=datetime.now(timezone.utc),
                budget_warning=budget_warning, final_result="FAILED", error_code="POSTCHECK_FAILED",
            ))
        self._event(task_id, AuditEventType.TEST_RESULT, "Deterministic POSTCHECK PASS", details={"result": "PASS"})
        self._transition(task_id, WorkflowState.COMPLETE, "deterministic project smoke passed")
        self._event(task_id, AuditEventType.EVALUATION_RESULT, f"{task_id} COMPLETE", details={"deterministic": True, "evaluator_invoked": False})
        return self._project_smoke_finish(ProjectSmokeResult(
            **result_values, state=WorkflowState.COMPLETE.value, start_time=started, end_time=datetime.now(timezone.utc),
            budget_warning=budget_warning, final_result="COMPLETE",
        ))

    def _project_smoke_finish(self, result: ProjectSmokeResult) -> dict[str, Any]:
        self.data.setdefault("project_smoke_results", []).append(result.model_dump(mode="json"))
        self._save()
        return result.model_dump(mode="json")

    def _record_project_usage(self, task_id: str, usage: TokenUsage) -> str | None:
        decision = self.budgets.record_actual(usage, retry_count=0)
        if decision == BudgetDecision.ALLOWED:
            return None
        self._event(task_id, AuditEventType.TOKEN_BUDGET_WARNING, f"Codex completed over configured budget: {decision.value}.", details={"budget_decision": decision.value, "token_usage": usage.model_dump()})
        return decision.value

    @staticmethod
    def _status_fixture_result(target: Path) -> str:
        try:
            return target.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            return "MISSING"

    @staticmethod
    def _postcheck_status_fixture(target: Path) -> str:
        try:
            content = target.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            return "FAIL"
        if content.endswith("\r\n"):
            content = content[:-2]
        elif content.endswith("\n"):
            content = content[:-1]
        return "PASS" if content == "PASS" else "FAIL"

    def _validate_project_repository(self, root: Path) -> tuple[str | None, dict[str, str]]:
        if not root.exists():
            return "PROJECT_PATH_NOT_FOUND", {}
        if not root.is_dir():
            return "PROJECT_PATH_NOT_DIRECTORY", {}
        snapshot = self._project_status_snapshot(root)
        if snapshot is None:
            return "PROJECT_GIT_UNAVAILABLE", {}
        return None, snapshot

    @staticmethod
    def _snapshot_changes(before: dict[str, str], after: dict[str, str]) -> list[str]:
        return sorted(path for path, value in after.items() if before.get(path) != value)

    def _project_status_snapshot(self, root: Path) -> dict[str, str] | None:
        try:
            probe = subprocess.run(
                ["git", "-c", f"safe.directory={root}", "rev-parse", "--show-toplevel"],
                cwd=root, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10, check=False, shell=False,
            )
            if probe.returncode != 0 or Path(probe.stdout.strip()).resolve() != root.resolve():
                return None
            status = subprocess.run(
                ["git", "-c", f"safe.directory={root}", "status", "--porcelain", "--untracked-files=all"],
                cwd=root, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10, check=False, shell=False,
            )
        except (FileNotFoundError, OSError, subprocess.TimeoutExpired):
            return None
        if status.returncode != 0:
            return None
        snapshot: dict[str, str] = {}
        for line in status.stdout.splitlines():
            if len(line) < 4:
                continue
            path = line[3:].replace("\\", "/")
            candidate = root / path
            try:
                digest = hashlib.sha256(candidate.read_bytes()).hexdigest() if candidate.is_file() else "non-file"
            except OSError:
                digest = "unreadable"
            snapshot[path] = f"{line[:2]}:{digest}"
        return snapshot

    def run_task(self, task_id: str, *, max_codex_attempts: int | None = None, codex_routing_selector: Callable[[int, int], object | None] | None = None) -> dict[str, Any]:
        """Execute one trusted configured task in a detached target-project worktree."""
        started = datetime.now(timezone.utc)
        run_id = uuid4().hex
        task = self.tasks.get(task_id)
        if task is None:
            return self._task_finish(TaskRunResult(
                run_id=run_id, task_id=task_id, project_id="unconfigured", state=WorkflowState.FAILED.value,
                start_time=started, end_time=datetime.now(timezone.utc), final_result="FAILED", error_code="TASK_NOT_CONFIGURED",
            ))
        project = self.projects.get(task.project_id)
        common = {
            "run_id": run_id, "task_id": task.task_id, "project_id": task.project_id,
            "start_time": started, "allowed_files": task.allowed_files,
        }
        if project is None:
            return self._task_finish(TaskRunResult(
                **common, state=WorkflowState.FAILED.value, end_time=datetime.now(timezone.utc), final_result="FAILED",
                error_code="TASK_PROJECT_NOT_CONFIGURED",
            ))
        source_root = project.path.resolve()
        common["source_repo_path"] = str(source_root)
        if self.runtime.codex.mode != CodexMode.REAL:
            return self._task_finish(TaskRunResult(
                **common, state=WorkflowState.FAILED.value, end_time=datetime.now(timezone.utc), final_result="FAILED",
                error_code="REAL_MODE_REQUIRED",
            ))
        source_error, source_status, source_head = self._task_source_validation(source_root)
        common["source_head_sha"] = source_head
        if source_error:
            return self._task_finish(TaskRunResult(
                **common, state=WorkflowState.FAILED.value, end_time=datetime.now(timezone.utc), final_result="FAILED",
                error_code=source_error,
            ))
        task_dependencies = set(task.allowed_files) | set(task.context_files)
        dirty_dependencies = sorted(set(source_status) & task_dependencies)
        if dirty_dependencies:
            return self._task_finish(TaskRunResult(
                **common, state=WorkflowState.HUMAN_REVIEW.value, end_time=datetime.now(timezone.utc), final_result="HUMAN_REVIEW",
                human_review_reason="source checkout has uncommitted task dependency changes", error_code="SOURCE_TASK_DEPENDENCY_DIRTY",
            ))
        if self.state_manager.current.state != WorkflowState.IDLE:
            self._transition(task.task_id, WorkflowState.IDLE, "previous terminal workflow reset")
        self.state_manager.start_task(task.task_id)
        self._transition(task.task_id, WorkflowState.PLANNING, "configured deterministic task started")
        worktree, branch, worktree_error = self._create_task_worktree(source_root, source_head, task, run_id)
        if worktree_error:
            self._transition(task.task_id, WorkflowState.HUMAN_REVIEW, "isolated worktree creation failed")
            return self._task_finish(TaskRunResult(
                **common, state=WorkflowState.HUMAN_REVIEW.value, end_time=datetime.now(timezone.utc), final_result="HUMAN_REVIEW",
                human_review_reason="isolated worktree could not be created", error_code=worktree_error,
            ))
        common.update({"worktree_path": str(worktree), "task_branch": branch})
        self._event(task.task_id, AuditEventType.SMOKE_STARTED, f"{task.task_id} WORKTREE CREATED", details={"worktree": str(worktree), "branch": branch, "source_head_sha": source_head, "source_dirty_file_count": len(source_status)})
        try:
            working_directory = self._task_working_directory(worktree, task.working_directory)
        except ValueError:
            self._transition(task.task_id, WorkflowState.HUMAN_REVIEW, "task working directory escaped managed worktree")
            return self._task_finish(TaskRunResult(
                **common, state=WorkflowState.HUMAN_REVIEW.value, end_time=datetime.now(timezone.utc), final_result="HUMAN_REVIEW",
                human_review_reason="configured working directory escaped managed worktree", error_code="WORKTREE_PATH_ESCAPE",
            ))
        self._transition(task.task_id, WorkflowState.PRECHECK, "targeted deterministic precheck")
        precheck = self._run_task_command(task.precheck, working_directory, self._task_artifact_root(run_id, "precheck"))
        if precheck.passed:
            self._event(task.task_id, AuditEventType.DETERMINISTIC_CHECK, f"{task.task_id} PRECHECK PASS", details=precheck.model_dump())
            self._transition(task.task_id, WorkflowState.RUNNING_TEST, "precheck passed")
            self._transition(task.task_id, WorkflowState.COMPLETE, "deterministic task already satisfied")
            self._event(task.task_id, AuditEventType.TEST_RESULT, f"{task.task_id} COMPLETE_NO_CHANGE", details={"precheck": "PASS"})
            return self._task_finish(TaskRunResult(
                **common, state=WorkflowState.COMPLETE.value, end_time=datetime.now(timezone.utc), precheck_result="PASS", precheck=precheck,
                final_result="COMPLETE_NO_CHANGE",
            ))
        self._event(task.task_id, AuditEventType.DETERMINISTIC_CHECK, f"{task.task_id} PRECHECK FAIL", details=precheck.model_dump())
        self._transition(task.task_id, WorkflowState.RUNNING_TEST, "precheck failed")
        triage = self._triage_precheck(precheck)
        if triage != "CODE_FIX" or not task.requires_codex:
            self._event(task.task_id, AuditEventType.TRIAGE, f"{task.task_id} TRIAGE {triage}", details={"precheck_error": precheck.error_code})
            self._transition(task.task_id, WorkflowState.TRIAGE, "deterministic triage completed")
            self._transition(task.task_id, WorkflowState.HUMAN_REVIEW if triage != "FAILED" else WorkflowState.FAILED, "deterministic triage blocked Codex")
            state = self.state_manager.current.state
            return self._task_finish(TaskRunResult(
                **common, state=state.value, end_time=datetime.now(timezone.utc), precheck_result="FAIL", precheck=precheck,
                triage_result=triage, final_result=state.value, human_review_reason="precheck is not a code-fix failure" if state == WorkflowState.HUMAN_REVIEW else None,
                error_code=precheck.error_code or "PRECHECK_TRIAGE_BLOCKED",
            ))
        self._event(task.task_id, AuditEventType.TRIAGE, f"{task.task_id} TRIAGE CODE_FIX", details={"precheck_exit_code": precheck.exit_code})
        self._transition(task.task_id, WorkflowState.TRIAGE, "deterministic triage classified CODE_FIX")
        worktree_baseline = self._project_status_snapshot(worktree)
        if worktree_baseline is None:
            self._transition(task.task_id, WorkflowState.HUMAN_REVIEW, "worktree status unavailable")
            return self._task_finish(TaskRunResult(
                **common, state=WorkflowState.HUMAN_REVIEW.value, end_time=datetime.now(timezone.utc), precheck_result="FAIL", precheck=precheck,
                triage_result="INFRASTRUCTURE_FAILURE", final_result="HUMAN_REVIEW", human_review_reason="worktree status unavailable", error_code="WORKTREE_GIT_UNAVAILABLE",
            ))
        return self._run_task_codex_attempts(task, common, working_directory, worktree, worktree_baseline, precheck, max_codex_attempts=max_codex_attempts, codex_routing_selector=codex_routing_selector)

    def _run_task_codex_attempts(
        self,
        task: ConfiguredTask,
        common: dict[str, Any],
        working_directory: Path,
        worktree: Path,
        worktree_baseline: dict[str, str],
        precheck: CommandRunResult,
        *,
        max_codex_attempts: int | None = None,
        codex_routing_selector: Callable[[int, int], object | None] | None = None,
    ) -> dict[str, Any]:
        attempts: list[CodexAttemptResult] = []
        aggregate = TokenUsage()
        budget_warnings: list[str] = []
        changed_files: list[str] = []
        retry_number = 0
        postcheck: CommandRunResult | None = None
        while True:
            if max_codex_attempts is not None and len(attempts) >= max_codex_attempts:
                self._transition(task.task_id, WorkflowState.HUMAN_REVIEW, "Day plan Codex call limit reached")
                return self._task_finish(TaskRunResult(
                    **common, state=WorkflowState.HUMAN_REVIEW.value, end_time=datetime.now(timezone.utc), precheck_result="FAIL", precheck=precheck,
                    triage_result="CODE_FIX", codex_attempts=attempts, allowed_files=task.allowed_files, changed_files=changed_files,
                    final_result="HUMAN_REVIEW", human_review_reason="CODEX_CALL_LIMIT_EXCEEDED", error_code="CODEX_CALL_LIMIT_EXCEEDED",
                ))
            budget_decision = self.budgets.check(TokenUsage(), retry_count=retry_number)
            if budget_decision != BudgetDecision.ALLOWED:
                self._transition(task.task_id, WorkflowState.HUMAN_REVIEW, "pre-execution budget guard blocked Codex")
                return self._task_finish(TaskRunResult(
                    **common, state=WorkflowState.HUMAN_REVIEW.value, end_time=datetime.now(timezone.utc), precheck_result="FAIL", precheck=precheck,
                    triage_result="CODE_FIX", codex_attempts=attempts, allowed_files=task.allowed_files, changed_files=changed_files,
                    final_result="HUMAN_REVIEW", human_review_reason=budget_decision.value, error_code=budget_decision.value,
                ))
            context_files, context_error = self._load_task_context_files(worktree, task)
            if context_error:
                self._transition(task.task_id, WorkflowState.HUMAN_REVIEW, "configured context files unavailable")
                return self._task_finish(TaskRunResult(
                    **common, state=WorkflowState.HUMAN_REVIEW.value, end_time=datetime.now(timezone.utc), precheck_result="FAIL", precheck=precheck,
                    triage_result="INFRASTRUCTURE_FAILURE", codex_attempts=attempts, final_result="HUMAN_REVIEW",
                    human_review_reason=context_error, error_code="CONTEXT_FILE_UNAVAILABLE",
                ))
            work_order = WorkOrder(
                task_id=task.task_id,
                goal=f"Fix the deterministic failure for {task.title}.",
                task_type=task.task_type,
                allowed_files=task.allowed_files,
                acceptance_tests=[" ".join(task.postcheck.argv)],
                max_retry=task.max_retry,
                needs_codex=True,
            )
            excerpt = (precheck.stderr or precheck.stdout or "deterministic precheck failed")[:2000]
            context = ContextBroker().build(
                work_order,
                error_excerpt=excerpt,
                configuration={"working_directory": str(working_directory), "postcheck_argv": " ".join(task.postcheck.argv), "evaluator_type": task.evaluator_type},
                retry_number=retry_number,
                context_files=context_files,
            )
            prompt = self._task_prompt(context)
            if codex_routing_selector and codex_routing_selector(len(prompt), retry_number) is None:
                self._transition(task.task_id, WorkflowState.HUMAN_REVIEW, "ModelRouter blocked Codex before execution")
                return self._task_finish(TaskRunResult(
                    **common, state=WorkflowState.HUMAN_REVIEW.value, end_time=datetime.now(timezone.utc), precheck_result="FAIL", precheck=precheck,
                    triage_result="CODE_FIX", codex_attempts=attempts, allowed_files=task.allowed_files, changed_files=changed_files,
                    final_result="HUMAN_REVIEW", human_review_reason="MODEL_ROUTER_BLOCKED", error_code="MODEL_ROUTER_BLOCKED",
                ))
            self._transition(task.task_id, WorkflowState.TRIAGE, "deterministic triage classified CODE_FIX") if self.state_manager.current.state == WorkflowState.RUNNING_TEST else None
            self._transition(task.task_id, WorkflowState.CODEX_FIX, f"Codex attempt {retry_number + 1} authorized")
            self._event(task.task_id, AuditEventType.CONTEXT_CREATED, f"{task.task_id} minimal context package built", details={"context_character_count": len(prompt), "context_byte_count": len(prompt.encode("utf-8")), "context_files": list(context_files)})
            self._event(task.task_id, AuditEventType.SMOKE_STARTED, f"Codex attempt {retry_number + 1} STARTED", details={"working_directory": str(working_directory)})
            self._save()
            execution = self.real_runner.run_worktree_task(working_directory, prompt)
            diagnostics = execution.diagnostics
            attempt = CodexAttemptResult(
                attempt=retry_number + 1, exit_code=execution.exit_code,
                thread_started=diagnostics.thread_started if diagnostics else False,
                turn_started=diagnostics.turn_started if diagnostics else False,
                turn_completed=diagnostics.turn_completed if diagnostics else False,
                gross_input_tokens=execution.token_usage.gross_input_tokens,
                cached_input_tokens=execution.token_usage.cached_input_tokens,
                uncached_input_tokens=execution.token_usage.uncached_input_tokens,
                output_tokens=execution.token_usage.output_tokens, error_code=execution.error_code,
            )
            attempts.append(attempt)
            aggregate = TokenUsage(
                input_tokens=aggregate.input_tokens + execution.token_usage.input_tokens,
                cached_input_tokens=aggregate.cached_input_tokens + execution.token_usage.cached_input_tokens,
                output_tokens=aggregate.output_tokens + execution.token_usage.output_tokens,
                available=aggregate.available or execution.token_usage.available,
            )
            warning = self._record_project_usage(task.task_id, execution.token_usage)
            if warning:
                budget_warnings.append(warning)
            self._event(task.task_id, AuditEventType.SMOKE_RESULT, f"Codex attempt {attempt.attempt} COMPLETE exit={execution.exit_code if execution.exit_code is not None else 'unavailable'}", details={"attempt": attempt.model_dump(), "status": execution.status})
            result_common = {
                **common, "precheck_result": "FAIL", "precheck": precheck, "triage_result": "CODE_FIX", "codex_invoked": True,
                "codex_attempts": attempts, "codex_exit_code": execution.exit_code,
                "thread_started": attempt.thread_started, "turn_started": attempt.turn_started, "turn_completed": attempt.turn_completed,
                "allowed_files": task.allowed_files, "changed_files": changed_files,
                "gross_input_tokens": aggregate.gross_input_tokens, "cached_input_tokens": aggregate.cached_input_tokens,
                "uncached_input_tokens": aggregate.uncached_input_tokens, "output_tokens": aggregate.output_tokens,
                "budget_warning": ",".join(budget_warnings) or None,
                "context_character_count": len(prompt), "context_byte_count": len(prompt.encode("utf-8")),
            }
            if execution.status != "completed" or execution.exit_code != 0 or not attempt.turn_completed:
                self._transition(task.task_id, WorkflowState.FAILED, "Codex execution failed")
                return self._task_finish(TaskRunResult(
                    **result_common, state=WorkflowState.FAILED.value, end_time=datetime.now(timezone.utc), final_result="FAILED",
                    error_code=execution.error_code or "CODEX_EXECUTION_FAILED",
                ))
            current_status = self._project_status_snapshot(worktree)
            if current_status is None:
                self._transition(task.task_id, WorkflowState.HUMAN_REVIEW, "worktree status unavailable after Codex")
                return self._task_finish(TaskRunResult(
                    **result_common, state=WorkflowState.HUMAN_REVIEW.value, end_time=datetime.now(timezone.utc), final_result="HUMAN_REVIEW",
                    human_review_reason="worktree status unavailable", error_code="WORKTREE_GIT_UNAVAILABLE",
                ))
            changed_files = self._snapshot_changes(worktree_baseline, current_status)
            scope = ScopeGuard().check(work_order, changed_files)
            result_common["changed_files"] = changed_files
            if not scope.allowed:
                self._event(task.task_id, AuditEventType.CODEX_RESULT, "Scope Guard FAIL", details={"allowed_files": task.allowed_files, "changed_files": changed_files, "out_of_scope": scope.out_of_scope})
                self._transition(task.task_id, WorkflowState.HUMAN_REVIEW, "Codex changed files outside configured scope")
                return self._task_finish(TaskRunResult(
                    **result_common, state=WorkflowState.HUMAN_REVIEW.value, end_time=datetime.now(timezone.utc), scope_guard_result="FAIL",
                    out_of_scope_files=scope.out_of_scope, final_result="HUMAN_REVIEW", human_review_reason="scope guard failed", error_code="SCOPE_GUARD_FAILED",
                ))
            self._event(task.task_id, AuditEventType.CODEX_RESULT, "Scope Guard PASS", details={"changed_files": changed_files})
            self._transition(task.task_id, WorkflowState.RUNNING_TEST, "scope guard passed")
            postcheck = self._run_task_command(task.postcheck, working_directory, self._task_artifact_root(common["run_id"], f"postcheck-{attempt.attempt}"))
            if postcheck.passed:
                self._event(task.task_id, AuditEventType.TEST_RESULT, "Deterministic POSTCHECK PASS", details=postcheck.model_dump())
                self._transition(task.task_id, WorkflowState.COMPLETE, "deterministic postcheck passed")
                self._event(task.task_id, AuditEventType.EVALUATION_RESULT, f"{task.task_id} COMPLETE", details={"deterministic": True, "evaluator_invoked": False})
                return self._task_finish(TaskRunResult(
                    **result_common, state=WorkflowState.COMPLETE.value, end_time=datetime.now(timezone.utc), scope_guard_result="PASS",
                    postcheck_result="PASS", postcheck=postcheck, final_result="COMPLETE",
                ))
            self._event(task.task_id, AuditEventType.TEST_RESULT, "Deterministic POSTCHECK FAIL", details=postcheck.model_dump())
            if retry_number >= task.max_retry:
                self._transition(task.task_id, WorkflowState.TRIAGE, "postcheck failure requires bounded repair decision")
                self._transition(task.task_id, WorkflowState.HUMAN_REVIEW, "bounded repair attempts exhausted")
                return self._task_finish(TaskRunResult(
                    **result_common, state=WorkflowState.HUMAN_REVIEW.value, end_time=datetime.now(timezone.utc), scope_guard_result="PASS",
                    postcheck_result="FAIL", postcheck=postcheck, final_result="HUMAN_REVIEW", human_review_reason="bounded repair attempts exhausted", error_code="RETRY_LIMIT_EXCEEDED",
                ))
            self.state_manager.increment_retry()
            retry_number += 1

    def _task_finish(self, result: TaskRunResult) -> dict[str, Any]:
        self.data.setdefault("task_runs", []).append(result.model_dump(mode="json"))
        self._save()
        return result.model_dump(mode="json")

    def _task_source_validation(self, source_root: Path) -> tuple[str | None, dict[str, str], str | None]:
        validation_error, status = self._validate_project_repository(source_root)
        if validation_error:
            return validation_error, {}, None
        try:
            completed = subprocess.run(
                ["git", "-C", str(source_root), "-c", f"safe.directory={source_root}", "rev-parse", "HEAD"],
                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10, check=False, shell=False,
            )
        except (FileNotFoundError, OSError, subprocess.TimeoutExpired):
            return "PROJECT_GIT_UNAVAILABLE", {}, None
        if completed.returncode != 0 or not completed.stdout.strip():
            return "PROJECT_HEAD_UNAVAILABLE", {}, None
        return None, status, completed.stdout.strip()

    def _create_task_worktree(self, source_root: Path, head: str, task: ConfiguredTask, run_id: str) -> tuple[Path | None, str | None, str | None]:
        self.worktree_root.mkdir(parents=True, exist_ok=True)
        candidate = (self.worktree_root / run_id).resolve()
        try:
            candidate.relative_to(self.worktree_root)
        except ValueError:
            return None, None, "WORKTREE_PATH_ESCAPE"
        if candidate.exists():
            return None, None, "WORKTREE_PATH_ALREADY_EXISTS"
        branch = f"agent/{task.task_id.lower()}-{run_id[:8]}"
        try:
            completed = subprocess.run(
                ["git", "-C", str(source_root), "-c", f"safe.directory={source_root}", "worktree", "add", "-b", branch, str(candidate), head],
                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60, check=False, shell=False,
            )
        except (FileNotFoundError, OSError, subprocess.TimeoutExpired):
            return None, None, "WORKTREE_CREATION_FAILED"
        if completed.returncode != 0 or not candidate.is_dir():
            return None, None, "WORKTREE_CREATION_FAILED"
        return candidate, branch, None

    @staticmethod
    def _task_working_directory(worktree: Path, configured: str) -> Path:
        directory = (worktree / configured).resolve()
        try:
            directory.relative_to(worktree.resolve())
        except ValueError as exc:
            raise ValueError("configured task working directory escaped worktree") from exc
        return directory

    def _task_artifact_root(self, run_id: str, stage: str) -> Path:
        root = (self.project_root / "state" / "task-artifacts" / run_id / stage).resolve()
        managed_root = (self.project_root / "state" / "task-artifacts").resolve()
        try:
            root.relative_to(managed_root)
        except ValueError as exc:
            raise ValueError("task artifact path escaped managed state") from exc
        return root

    def _discovery_artifact_root(self, run_id: str) -> Path:
        root = (self.project_root / "state" / "task-discovery" / run_id).resolve()
        managed_root = (self.project_root / "state" / "task-discovery").resolve()
        try:
            root.relative_to(managed_root)
        except ValueError as exc:
            raise ValueError("discovery artifact path escaped managed state") from exc
        return root

    def _run_task_command(self, command: TaskCommand, cwd: Path, artifact_root: Path) -> CommandRunResult:
        argv = [str(artifact_root) if value == "{artifact_root}" else value for value in command.argv]
        try:
            completed = subprocess.run(
                argv, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120, check=False, shell=False,
            )
        except FileNotFoundError:
            return CommandRunResult(argv=argv, cwd=str(cwd), error_code="COMMAND_NOT_FOUND")
        except subprocess.TimeoutExpired as exc:
            return CommandRunResult(argv=argv, cwd=str(cwd), error_code="COMMAND_TIMEOUT", stdout=self._bounded_text(exc.stdout), stderr=self._bounded_text(exc.stderr))
        return CommandRunResult(
            argv=argv, cwd=str(cwd), exit_code=completed.returncode, passed=completed.returncode == 0,
            stdout=self._bounded_text(completed.stdout), stderr=self._bounded_text(completed.stderr),
        )

    @staticmethod
    def _bounded_text(value: str | bytes | None, limit: int = 4000) -> str | None:
        if value is None:
            return None
        if isinstance(value, bytes):
            value = value.decode("utf-8", errors="replace")
        return value[:limit] or None

    @staticmethod
    def _triage_precheck(precheck: CommandRunResult) -> str:
        if precheck.error_code:
            return "INFRASTRUCTURE_FAILURE"
        return "CODE_FIX" if precheck.exit_code == 1 else "FAILED"

    @staticmethod
    def _task_prompt(context: Any) -> str:
        context_files = "\n\n".join(f"--- {path} ---\n{content}" for path, content in context.context_files.items())
        return (
            f"TASK: {context.task_id}\nGoal: {context.goal}\n\n"
            f"Failure:\n{context.error_excerpt or 'deterministic precheck failed'}\n\n"
            f"Acceptance command: {context.configuration['postcheck_argv']}\n"
            f"Allowed files:\n" + "\n".join(f"- {path}" for path in context.allowed_files) + "\n\n"
            f"Relevant context:\n{context_files}\n\n"
            "Solve only this task. Modify only allowed files. Make the smallest reasonable change. "
            "Do not alter acceptance criteria or weaken tests. Do not modify unrelated files. Do not commit or push. No explanatory essay is required."
        )

    @staticmethod
    def _load_task_context_files(worktree: Path, task: ConfiguredTask) -> tuple[dict[str, str], str | None]:
        remaining = task.context_max_characters
        contents: dict[str, str] = {}
        for relative in task.context_files:
            path = (worktree / relative).resolve()
            try:
                path.relative_to(worktree.resolve())
            except ValueError:
                return {}, "configured context path escaped worktree"
            if not path.is_file():
                return {}, f"configured context file is missing: {relative}"
            try:
                content = path.read_text(encoding="utf-8")
            except (OSError, UnicodeError):
                return {}, f"configured context file is unreadable: {relative}"
            if len(content) > remaining:
                return {}, "configured context files exceed context bound"
            contents[relative] = content
            remaining -= len(content)
        return contents, None

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
