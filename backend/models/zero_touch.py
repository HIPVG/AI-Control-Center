from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class ZeroTouchStatus(str, Enum):
    COMPLETE = "COMPLETE"
    ATTENTION = "ATTENTION"


class ZeroTouchRun(BaseModel):
    """Bounded end-to-end result; free-form goal text is intentionally absent."""

    run_id: str
    started_at: datetime
    completed_at: datetime
    status: ZeroTouchStatus
    goal_id: str | None = None
    target_type: str | None = None
    target_id: str | None = None
    action_type: str | None = None
    outcome: str | None = None
    completion_reason: str
    human_attention_required: bool = False
