from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class LocalLLMDayState(str, Enum):
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"
    STOPPED = "STOPPED"


class LocalLLMWorkItemState(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"
    DEFERRED = "DEFERRED"
    BLOCKED = "BLOCKED"


class DayIssueClassification(str, Enum):
    IMPLEMENTATION_DEFECT = "IMPLEMENTATION_DEFECT"
    TEST_OR_CONTRACT_DEFECT = "TEST_OR_CONTRACT_DEFECT"
    MODEL_QUALITY_FINDING = "MODEL_QUALITY_FINDING"
    EXPERIMENT_CONFIGURATION_ISSUE = "EXPERIMENT_CONFIGURATION_ISSUE"
    MISSING_EXTERNAL_AUTHORITY = "MISSING_EXTERNAL_AUTHORITY"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class DayCriterion(BaseModel):
    criterion_id: str = Field(min_length=1, max_length=100)
    statement: str = Field(min_length=1, max_length=1200)
    required_evidence: list[str] = Field(default_factory=list, max_length=12)
    satisfied: bool = False
    evidence: dict[str, object] = Field(default_factory=dict)


class LocalLLMDayContract(BaseModel):
    """The durable WHAT contract; it intentionally contains no task recipe."""

    day: int = Field(ge=1, le=14)
    title: str = Field(min_length=1, max_length=300)
    version: str = Field(default="v1", min_length=1, max_length=80)
    objective: str = Field(min_length=1, max_length=1600)
    completion_criteria: list[DayCriterion] = Field(min_length=1, max_length=20)
    constraints: list[str] = Field(min_length=1, max_length=20)
    authoritative_sources: list[str] = Field(min_length=1, max_length=20)
    satisfied_criteria: list[str] = Field(default_factory=list, max_length=20)
    remaining_gaps: list[str] = Field(default_factory=list, max_length=20)


class LocalLLMDayWorkItem(BaseModel):
    """A bounded planner output, persisted independently from the Day contract."""

    item_id: str = Field(min_length=1, max_length=80)
    title: str = Field(min_length=1, max_length=300)
    objective: str = Field(min_length=1, max_length=1200)
    kind: str = Field(default="EVIDENCE_CHECK", max_length=60)
    engine_task_id: str | None = Field(default=None, max_length=120)
    dynamic_work_order: "DynamicDayWorkOrder | None" = None
    criterion_ids: list[str] = Field(default_factory=list, max_length=12)
    state: LocalLLMWorkItemState = LocalLLMWorkItemState.PENDING
    evidence: dict[str, object] = Field(default_factory=dict)
    blocked_reason: str | None = None


class DynamicDayWorkOrder(BaseModel):
    """Server-validated authority for one new Day engineering task.

    It deliberately describes a bounded edit and deterministic test files, not
    a shell command.  The engine derives commands and always runs in a managed
    worktree.
    """

    task_id: str = Field(min_length=6, max_length=120, pattern=r"^day-[0-9]{1,2}-[a-z0-9-]+$")
    project_id: str = Field(default="local_llm_lab", pattern=r"^local_llm_lab$")
    task_type: str = Field(default="code_fix", pattern=r"^(code_fix|config|plan)$")
    allowed_files: list[str] = Field(min_length=1, max_length=8)
    context_files: list[str] = Field(min_length=1, max_length=10)
    acceptance_test_files: list[str] = Field(min_length=1, max_length=5)

    @staticmethod
    def _safe_paths(values: list[str], *, tests_only: bool = False) -> list[str]:
        normalized = [value.replace("\\\\", "/").strip() for value in values]
        if any(not value or value.startswith("/") or ":" in value or ".." in value.split("/") for value in normalized):
            raise ValueError("dynamic work-order paths must be safe relative paths")
        if tests_only and any(not value.startswith("tests/") or not value.endswith(".py") for value in normalized):
            raise ValueError("dynamic acceptance tests must be repository test files")
        if len(normalized) != len(set(normalized)):
            raise ValueError("dynamic work-order paths must be unique")
        return normalized

    @field_validator("allowed_files", "context_files")
    @classmethod
    def safe_paths(cls, values: list[str]) -> list[str]:
        return cls._safe_paths(values)

    @field_validator("acceptance_test_files")
    @classmethod
    def safe_test_paths(cls, values: list[str]) -> list[str]:
        return cls._safe_paths(values, tests_only=True)


class LocalLLMDayReport(BaseModel):
    day: int = Field(ge=1, le=14)
    objective: str
    result: str
    summary: str
    evidence: dict[str, object] = Field(default_factory=dict)
    completed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class LocalLLMRepairCard(BaseModel):
    """A proposal audit record. It never grants source-edit authority."""

    problem_id: str = Field(min_length=1, max_length=120)
    title: str = Field(min_length=1, max_length=300)
    cause: str = Field(min_length=1, max_length=1000)
    investigation: str = Field(min_length=1, max_length=1000)
    resolution_logic: str = Field(min_length=1, max_length=1200)
    verification: str = Field(min_length=1, max_length=1000)
    status: str = Field(default="PROPOSAL", max_length=40)
    uses: int = Field(default=0, ge=0)
    failure_class: str | None = Field(default=None, max_length=160)
    failed_work_item: str | None = Field(default=None, max_length=80)


class LocalLLMDaySnapshot(BaseModel):
    selected_day: int | None = Field(default=None, ge=1, le=14)
    state: LocalLLMDayState = LocalLLMDayState.IDLE
    objective: str | None = None
    contract: LocalLLMDayContract | None = None
    activity: str = "Waiting for a Day selection."
    progress: int = Field(default=0, ge=0, le=100)
    completed_steps: list[str] = Field(default_factory=list)
    work_items: list[LocalLLMDayWorkItem] = Field(default_factory=list, max_length=30)
    smoke_report: LocalLLMDayReport | None = None
    repair_deadline_seconds: int = Field(default=300, ge=1, le=300)
    repair_attempted: bool = False
    repair_knowledge: list[LocalLLMRepairCard] = Field(default_factory=list, max_length=30)
    codex_handoff: dict[str, object] | None = None
    issue_classification: DayIssueClassification | None = None
    replan_count: int = Field(default=0, ge=0, le=3)
    report: LocalLLMDayReport | None = None
    stop_reason: str | None = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
