from datetime import datetime, timezone
from typing import Any, Callable, Protocol

from backend.agents.day_providers import DayArchitect, DayEvaluator, MockDayArchitect, MockSemanticEvaluator
from backend.control.tasks import ConfiguredTask, TaskRegistry
from backend.models.day import DayPlan, DayPlanRegistry, DayRunSnapshot, DayRunState, HumanReviewItem, QueueTaskState, QueuedTask
from backend.models.result import TokenUsage


class DayTaskExecutor(Protocol):
    def __call__(self, task_id: str, max_codex_attempts: int | None = None, repair_instruction: str | None = None) -> dict[str, Any]: ...


class DayRunner:
    """Persistent, single-step scheduler that delegates execution to the guarded engine."""

    def __init__(
        self,
        plans: DayPlanRegistry,
        tasks: TaskRegistry,
        execute_task: DayTaskExecutor,
        *,
        architects: dict[str, DayArchitect] | None = None,
        evaluators: dict[str, DayEvaluator] | None = None,
        persist: Callable[[dict[str, Any]], None] | None = None,
        audit: Callable[[str, str, dict[str, Any]], None] | None = None,
        saved: dict[str, Any] | None = None,
    ) -> None:
        self.plans, self.tasks, self.execute_task = plans, tasks, execute_task
        self.architects = architects or {"mock": MockDayArchitect()}
        self.evaluators = evaluators or {"mock": MockSemanticEvaluator()}
        self.persist = persist
        self.audit = audit
        self.snapshot = DayRunSnapshot.model_validate(saved or {})
        if self.snapshot.state == DayRunState.RUNNING:
            self.snapshot.state = DayRunState.PAUSED
            self.snapshot.stop_reason = "INTERRUPTED_REQUIRES_RESUME"
            self._save()

    def view(self) -> dict[str, Any]:
        return self.snapshot.model_dump(mode="json")

    def start(self, plan_id: str, *, single_step: bool | None = None) -> dict[str, Any]:
        plan = self.plans.get(plan_id)
        if plan is None:
            return {"error_code": "PLAN_NOT_CONFIGURED", **self.view()}
        missing = [task_id for task_id in plan.task_ids if self.tasks.get(task_id) is None]
        if missing:
            return {"error_code": "PLAN_TASK_NOT_CONFIGURED", "missing_task_ids": missing, **self.view()}
        self.snapshot = DayRunSnapshot(plan_id=plan_id, state=DayRunState.RUNNING, queue=[QueuedTask(task_id=task_id) for task_id in plan.task_ids])
        self._audit("SYSTEM", "DAY_PLAN_STARTED", {"plan_id": plan_id, "task_ids": plan.task_ids})
        self._save()
        return self.step(single_step=plan.single_step_default if single_step is None else single_step)

    def resume(self, *, single_step: bool | None = None) -> dict[str, Any]:
        plan = self._plan()
        if plan is None:
            return {"error_code": "NO_DAY_PLAN", **self.view()}
        if self.snapshot.state not in {DayRunState.RUNNING, DayRunState.PAUSED, DayRunState.STOPPED}:
            return {"error_code": "DAY_NOT_RESUMABLE", **self.view()}
        self.snapshot.state = DayRunState.RUNNING
        self.snapshot.stop_reason = None
        self._save()
        return self.step(single_step=plan.single_step_default if single_step is None else single_step)

    def stop(self) -> dict[str, Any]:
        if self.snapshot.state == DayRunState.RUNNING:
            self.snapshot.state = DayRunState.STOPPED
            self.snapshot.stop_reason = "STOP_REQUESTED"
            for item in self.snapshot.queue:
                if item.state == QueueTaskState.RUNNING:
                    item.state = QueueTaskState.STOPPED
            self._audit("SYSTEM", "DAY_STOPPED", {"reason": self.snapshot.stop_reason})
            self._save()
        return self.view()

    def step(self, *, single_step: bool = True) -> dict[str, Any]:
        plan = self._plan()
        if plan is None:
            return {"error_code": "NO_DAY_PLAN", **self.view()}
        if not single_step:
            return {"error_code": "CONTINUOUS_MODE_NOT_SUPPORTED", **self.view()}
        if self.snapshot.state != DayRunState.RUNNING:
            return {"error_code": "DAY_NOT_RUNNING", **self.view()}
        if self.snapshot.architect_calls >= plan.max_architect_calls:
            return self._human_review("SYSTEM", "ARCHITECT_CALL_LIMIT_EXCEEDED")
        architect = self.architects.get(plan.architect_provider)
        if architect is None:
            return self._human_review("SYSTEM", "ARCHITECT_PROVIDER_NOT_CONFIGURED")
        self.snapshot.architect_calls += 1
        try:
            decision = architect.choose(self.snapshot.queue)
        except RuntimeError as exc:
            return self._human_review("SYSTEM", f"ARCHITECT_ERROR:{exc}")
        self._add_usage("architect", decision.token_usage)
        self._audit("SYSTEM", "DAY_ARCHITECT_DECISION", {"task_id": decision.task_id, "reason": decision.reason})
        item = next((candidate for candidate in self.snapshot.queue if candidate.task_id == decision.task_id and candidate.state in {QueueTaskState.PENDING, QueueTaskState.READY, QueueTaskState.REPAIR_PENDING}), None)
        if item is None:
            if all(candidate.state in {QueueTaskState.PASS, QueueTaskState.COMPLETE_NO_CHANGE} for candidate in self.snapshot.queue):
                self.snapshot.state = DayRunState.COMPLETE
                self.snapshot.stop_reason = "ALL_TASKS_TERMINAL"
                self._save()
                return self.view()
            return self._human_review("SYSTEM", "ARCHITECT_SELECTED_INELIGIBLE_TASK")
        return self._execute_one(plan, item)

    def _execute_one(self, plan: DayPlan, item: QueuedTask, repair_instruction: str | None = None) -> dict[str, Any]:
        task = self.tasks.get(item.task_id)
        assert task is not None
        remaining_codex = plan.max_codex_calls - self.snapshot.codex_calls
        if task.requires_codex and remaining_codex <= 0:
            return self._human_review(item.task_id, "CODEX_CALL_LIMIT_EXCEEDED")
        item.state = QueueTaskState.RUNNING
        item.attempts += 1
        item.updated_at = datetime.now(timezone.utc)
        self._save()
        result = self.execute_task(item.task_id, max_codex_attempts=remaining_codex, repair_instruction=repair_instruction)
        self._audit(item.task_id, "DAY_TASK_RESULT", {"final_result": result.get("final_result"), "codex_invoked": result.get("codex_invoked", False), "error_code": result.get("error_code")})
        self.snapshot.codex_calls += len(result.get("codex_attempts", []))
        self._add_usage("codex", TokenUsage(
            input_tokens=int(result.get("gross_input_tokens", 0)), cached_input_tokens=int(result.get("cached_input_tokens", 0)),
            output_tokens=int(result.get("output_tokens", 0)), available=bool(result.get("codex_invoked")),
        ))
        final = result.get("final_result")
        if final == "COMPLETE_NO_CHANGE":
            item.state, item.final_result = QueueTaskState.COMPLETE_NO_CHANGE, final
        elif final == "COMPLETE" and task.evaluator_type == "deterministic":
            item.state, item.final_result = QueueTaskState.PASS, final
        elif final == "COMPLETE" and task.evaluator_type == "semantic":
            return self._evaluate_semantic(plan, item, task, result)
        elif final == "HUMAN_REVIEW":
            return self._human_review(item.task_id, result.get("human_review_reason") or result.get("error_code") or "TASK_REQUIRES_REVIEW")
        else:
            item.state, item.final_result, item.last_error = QueueTaskState.FAILED, final or "FAILED", result.get("error_code")
            self.snapshot.state, self.snapshot.stop_reason = DayRunState.FAILED, "TASK_FAILED"
        self._finalize_step()
        return self.view()

    def _evaluate_semantic(self, plan: DayPlan, item: QueuedTask, task: ConfiguredTask, result: dict[str, Any]) -> dict[str, Any]:
        if self.snapshot.evaluator_calls >= plan.max_evaluator_calls:
            return self._human_review(item.task_id, "EVALUATOR_CALL_LIMIT_EXCEEDED")
        evaluator = self.evaluators.get(plan.evaluator_provider)
        if evaluator is None:
            return self._human_review(item.task_id, "EVALUATOR_PROVIDER_NOT_CONFIGURED")
        self.snapshot.evaluator_calls += 1
        item.evaluator_invoked = True
        try:
            evaluation = evaluator.evaluate(task_id=item.task_id, metrics=task.evaluation_metrics, result=self._bounded_result(result))
        except RuntimeError as exc:
            return self._human_review(item.task_id, f"EVALUATOR_ERROR:{exc}")
        self._add_usage("evaluator", evaluation.token_usage)
        self._audit(item.task_id, "DAY_EVALUATION_RESULT", {"decision": evaluation.decision, "score": evaluation.score, "blocking_issues": evaluation.blocking_issues})
        if evaluation.decision == "PASS":
            item.state, item.final_result = QueueTaskState.PASS, "COMPLETE"
        elif evaluation.decision == "REPAIR" and item.repair_loops < plan.max_repair_loops_per_task:
            item.repair_loops += 1
            item.state = QueueTaskState.REPAIR_PENDING
            return self._execute_one(plan, item, repair_instruction=evaluation.repair_instruction)
        else:
            return self._human_review(item.task_id, "SEMANTIC_EVALUATION_REQUIRES_REVIEW")
        self._finalize_step()
        return self.view()

    @staticmethod
    def _bounded_result(result: dict[str, Any]) -> dict[str, Any]:
        allowed = ("task_id", "final_result", "precheck_result", "postcheck_result", "changed_files", "error_code")
        return {key: result.get(key) for key in allowed}

    def _finalize_step(self) -> None:
        if all(item.state in {QueueTaskState.PASS, QueueTaskState.COMPLETE_NO_CHANGE} for item in self.snapshot.queue):
            self.snapshot.state, self.snapshot.stop_reason = DayRunState.COMPLETE, "ALL_TASKS_TERMINAL"
        self._save()

    def _human_review(self, task_id: str, reason: str) -> dict[str, Any]:
        item = next((candidate for candidate in self.snapshot.queue if candidate.task_id == task_id), None)
        if item:
            item.state, item.last_error = QueueTaskState.HUMAN_REVIEW, reason
        self.snapshot.human_review_queue.append(HumanReviewItem(task_id=task_id, reason=reason))
        self._audit(task_id, "DAY_HUMAN_REVIEW", {"reason": reason})
        self.snapshot.state, self.snapshot.stop_reason = DayRunState.HUMAN_REVIEW, reason
        self._save()
        return self.view()

    def _plan(self) -> DayPlan | None:
        return self.plans.get(self.snapshot.plan_id) if self.snapshot.plan_id else None

    def _add_usage(self, role: str, usage: TokenUsage) -> None:
        previous = self.snapshot.token_usage[role]
        self.snapshot.token_usage[role] = TokenUsage(
            input_tokens=previous.input_tokens + usage.input_tokens,
            cached_input_tokens=previous.cached_input_tokens + usage.cached_input_tokens,
            output_tokens=previous.output_tokens + usage.output_tokens,
            available=previous.available or usage.available,
        )

    def _save(self) -> None:
        self.snapshot.updated_at = datetime.now(timezone.utc)
        if self.persist:
            self.persist(self.view())

    def _audit(self, task_id: str, event_type: str, details: dict[str, Any]) -> None:
        if self.audit:
            self.audit(task_id, event_type, details)
