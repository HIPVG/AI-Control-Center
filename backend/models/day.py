from datetime import datetime, timezone
from enum import Enum
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field

from backend.models.result import TokenUsage
from backend.models.model_routing import ProfileTokenUsage, RoutingDecision


class DayRunState(str, Enum):
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    STOPPED = "STOPPED"
    COMPLETE = "COMPLETE"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    FAILED = "FAILED"


class DayExecutionMode(str, Enum):
    SINGLE_STEP = "single-step"
    CONTINUOUS = "continuous"


class QueueTaskState(str, Enum):
    PENDING = "PENDING"
    READY = "READY"
    RUNNING = "RUNNING"
    PASS = "PASS"
    COMPLETE_NO_CHANGE = "COMPLETE_NO_CHANGE"
    REPAIR_PENDING = "REPAIR_PENDING"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    FAILED = "FAILED"
    STOPPED = "STOPPED"
    SKIPPED = "SKIPPED"


class ArchitectDecision(BaseModel):
    decision: Literal["RUN_TASK", "SKIP_TASK", "HUMAN_REVIEW", "STOP_DAY", "DAY_COMPLETE"] = "RUN_TASK"
    task_id: str | None = None
    reason: str = Field(min_length=1, max_length=1000)
    priority: int | None = Field(default=None, ge=0, le=100)
    task_complexity: Literal["simple", "normal", "complex"] | None = None
    token_usage: TokenUsage = Field(default_factory=TokenUsage)
    diagnostics: dict[str, object] = Field(default_factory=dict)


class SemanticEvaluation(BaseModel):
    decision: Literal["PASS", "REPAIR", "HUMAN_REVIEW", "NOT_REQUIRED"]
    reason: str = Field(default="", max_length=1000)
    metrics: dict[str, float] = Field(default_factory=dict)
    blocking_issues: list[str] = Field(default_factory=list)
    repair_instruction: str | None = None
    token_usage: TokenUsage = Field(default_factory=TokenUsage)
    diagnostics: dict[str, object] = Field(default_factory=dict)


class DayPlan(BaseModel):
    plan_id: str = Field(min_length=1, max_length=120)
    title: str = Field(min_length=1, max_length=300)
    task_ids: list[str] = Field(min_length=1)
    architect_provider: str = "mock"
    evaluator_provider: str = "mock"
    single_step_default: bool = True
    continuous_mode_supported: bool = True
    validation_day: int = Field(default=3, ge=0, le=365)
    max_tasks_per_run: int = Field(default=10, ge=1, le=100)
    max_codex_calls: int = Field(default=3, ge=0, le=50)
    max_architect_calls: int = Field(default=10, ge=0, le=100)
    max_evaluator_calls: int = Field(default=10, ge=0, le=100)
    max_repair_loops_per_task: int = Field(default=1, ge=0, le=10)
    max_failed_tasks: int = Field(default=1, ge=0, le=100)
    stop_on_human_review: bool = True
    allowed_profile_ids: list[str] = Field(default_factory=lambda: ["economical", "standard", "deep"])
    allow_profile_budget_downgrade: bool = False
    max_profile_escalation_level: int = Field(default=2, ge=0, le=2)


class DayPlanRegistry(BaseModel):
    plans: dict[str, DayPlan] = Field(default_factory=dict)

    def get(self, plan_id: str) -> DayPlan | None:
        return self.plans.get(plan_id)

    def metadata(self) -> list[dict[str, object]]:
        return [
            {
                "plan_id": plan.plan_id,
                "title": plan.title,
                "task_ids": plan.task_ids,
                "single_step_default": plan.single_step_default,
                "continuous_mode_supported": plan.continuous_mode_supported,
            }
            for plan in self.plans.values()
        ]


class QueuedTask(BaseModel):
    task_id: str
    state: QueueTaskState = QueueTaskState.PENDING
    attempts: int = Field(default=0, ge=0)
    repair_loops: int = Field(default=0, ge=0)
    final_result: str | None = None
    last_error: str | None = None
    evaluator_invoked: bool = False
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class HumanReviewItem(BaseModel):
    review_id: str = Field(default_factory=lambda: uuid4().hex)
    plan_id: str | None = None
    task_id: str
    reason: str
    blocking: bool = True
    summary: str | None = None
    changed_files: list[str] = Field(default_factory=list)
    result_reference: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DayRunSnapshot(BaseModel):
    plan_id: str | None = None
    state: DayRunState = DayRunState.IDLE
    mode: DayExecutionMode = DayExecutionMode.SINGLE_STEP
    queue: list[QueuedTask] = Field(default_factory=list)
    human_review_queue: list[HumanReviewItem] = Field(default_factory=list)
    stop_reason: str | None = None
    architect_calls: int = Field(default=0, ge=0)
    evaluator_calls: int = Field(default=0, ge=0)
    codex_calls: int = Field(default=0, ge=0)
    failed_tasks: int = Field(default=0, ge=0)
    tasks_processed_this_run: int = Field(default=0, ge=0)
    day_progress: float = Field(default=0, ge=0, le=100)
    overall_progress: float = Field(default=0, ge=0, le=100)
    budget_warnings: list[str] = Field(default_factory=list)
    token_usage: dict[str, TokenUsage] = Field(default_factory=lambda: {
        "architect": TokenUsage(), "codex": TokenUsage(), "evaluator": TokenUsage(),
    })
    profile_token_usage: dict[str, ProfileTokenUsage] = Field(default_factory=dict)
    model_routing_decisions: list[RoutingDecision] = Field(default_factory=list)
    deterministic_zero_usage_task_ids: list[str] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
