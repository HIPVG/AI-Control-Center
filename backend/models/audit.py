from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from backend.models.state import WorkflowState


class AuditEventType(str, Enum):
    TASK_STARTED = "TASK_STARTED"
    STATE_TRANSITION = "STATE_TRANSITION"
    DETERMINISTIC_CHECK = "DETERMINISTIC_CHECK"
    TRIAGE = "TRIAGE"
    CONTEXT_CREATED = "CONTEXT_CREATED"
    CODEX_RESULT = "CODEX_RESULT"
    TEST_RESULT = "TEST_RESULT"
    EVALUATION_RESULT = "EVALUATION_RESULT"
    PROGRESS_UPDATED = "PROGRESS_UPDATED"
    WORKFLOW_SKIPPED = "WORKFLOW_SKIPPED"
    LEGACY_EVENT = "LEGACY_EVENT"


class AuditEvent(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    task_id: str
    event_type: AuditEventType
    message: str
    from_state: WorkflowState | None = None
    to_state: WorkflowState | None = None
    details: dict[str, Any] = Field(default_factory=dict)
