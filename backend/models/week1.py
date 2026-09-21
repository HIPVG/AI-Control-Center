from enum import Enum

from typing import Any

from pydantic import BaseModel, Field


class Week1DayStatus(str, Enum):
    PENDING = "PENDING"
    COMPLETE = "COMPLETE"
    EXTERNAL_ACTION_REQUIRED = "EXTERNAL_ACTION_REQUIRED"
    HUMAN_DECISION_REQUIRED = "HUMAN_DECISION_REQUIRED"


class Week1DayRecord(BaseModel):
    day: int = Field(ge=4, le=7)
    status: Week1DayStatus = Week1DayStatus.PENDING
    reason_code: str | None = None
    evidence: dict[str, Any] = Field(default_factory=dict)
