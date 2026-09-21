from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field

from backend.models.result import TokenUsage


class DayRunState(str, Enum):
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    STOPPED = "STOPPED"
    COMPLETE = "COMPLETE"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    FAILED = "FAILED"


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


class ArchitectDecision(BaseModel):
    task_id: str | None = None
    reason: str = Field(min_length=1, max_length=1000)
    token_usage: TokenUsage = Field(default_factory=TokenUsage)


class SemanticEvaluation(BaseModel):
    decision: str
    score: dict[str, float] = Field(default_factory=dict)
    blocking_issues: list[str] = Field(default_factory=list)
    repair_instruction: str | None = None
    token_usage: TokenUsage = Field(default_factory=TokenUsage)


class DayPlan(BaseModel):
    plan_id: str = Field(min_length=1, max_length=120)
    title: str = Field(min_length=1, max_length=300)
    task_ids: list[str] = Field(min_length=1)
    architect_provider: str = "mock"
    evaluator_provider: str = "mock"
    single_step_default: bool = True
    continuous_mode_supported: bool = False
    max_codex_calls: int = Field(default=3, ge=0, le=50)
    max_architect_calls: int = Field(default=10, ge=0, le=100)
    max_evaluator_calls: int = Field(default=10, ge=0, le=100)
    max_repair_loops_per_task: int = Field(default=1, ge=0, le=10)
    stop_on_human_review: bool = True


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
    task_id: str
    reason: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DayRunSnapshot(BaseModel):
    plan_id: str | None = None
    state: DayRunState = DayRunState.IDLE
    queue: list[QueuedTask] = Field(default_factory=list)
    human_review_queue: list[HumanReviewItem] = Field(default_factory=list)
    stop_reason: str | None = None
    architect_calls: int = Field(default=0, ge=0)
    evaluator_calls: int = Field(default=0, ge=0)
    codex_calls: int = Field(default=0, ge=0)
    token_usage: dict[str, TokenUsage] = Field(default_factory=lambda: {
        "architect": TokenUsage(), "codex": TokenUsage(), "evaluator": TokenUsage(),
    })
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
