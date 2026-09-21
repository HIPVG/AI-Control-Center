from enum import Enum

from pydantic import BaseModel, Field


class WorkflowState(str, Enum):
    IDLE = "IDLE"
    PLANNING = "PLANNING"
    PRECHECK = "PRECHECK"
    RUNNING_TEST = "RUNNING_TEST"
    TRIAGE = "TRIAGE"
    CODEX_FIX = "CODEX_FIX"
    EVALUATING = "EVALUATING"
    COMPLETE = "COMPLETE"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    FAILED = "FAILED"
    STOPPED = "STOPPED"


class RunState(BaseModel):
    state: WorkflowState = WorkflowState.IDLE
    task_id: str | None = None
    retry_count: int = Field(default=0, ge=0)
    reason: str | None = None
