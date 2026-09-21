from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class LocalRuntimeReadinessState(str, Enum):
    READY = "READY"
    STARTED = "STARTED"
    EXTERNAL_ACTION_REQUIRED = "EXTERNAL_ACTION_REQUIRED"


class LocalRuntimeReadiness(BaseModel):
    """Bounded state for a server-owned local runtime readiness check."""

    runtime_id: str = "ollama"
    state: LocalRuntimeReadinessState
    reason_code: str
    attempts: int = Field(ge=0, le=8)
    started_by_control_center: bool = False
    checked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
