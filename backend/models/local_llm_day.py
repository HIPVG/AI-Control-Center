from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class LocalLLMDayState(str, Enum):
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"
    STOPPED = "STOPPED"


class LocalLLMDayReport(BaseModel):
    day: int = Field(ge=1, le=14)
    objective: str
    result: str
    summary: str
    evidence: dict[str, object] = Field(default_factory=dict)
    completed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class LocalLLMDaySnapshot(BaseModel):
    selected_day: int | None = Field(default=None, ge=1, le=14)
    state: LocalLLMDayState = LocalLLMDayState.IDLE
    objective: str | None = None
    activity: str = "Waiting for a Day selection."
    progress: int = Field(default=0, ge=0, le=100)
    completed_steps: list[str] = Field(default_factory=list)
    report: LocalLLMDayReport | None = None
    stop_reason: str | None = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
