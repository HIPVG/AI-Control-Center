from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class GoalPlanStatus(str, Enum):
    PROPOSED = "PROPOSED"
    REJECTED = "REJECTED"
    EXECUTED = "EXECUTED"


class GoalSubmission(BaseModel):
    """The only browser-supplied field for the bounded Goal-to-Plan route."""

    model_config = ConfigDict(extra="forbid")
    goal: str = Field(min_length=1, max_length=280)

    @field_validator("goal")
    @classmethod
    def bounded_text(cls, value: str) -> str:
        normalized = " ".join(value.split())
        if not normalized or any(ord(character) < 32 for character in normalized):
            raise ValueError("goal must contain bounded printable text")
        return normalized


class GoalPlan(BaseModel):
    goal_id: str
    created_at: datetime
    status: GoalPlanStatus
    goal_digest: str = Field(min_length=64, max_length=64)
    summary: str
    target_type: str | None = None
    target_id: str | None = None
    policy_reason: str
    executed_at: datetime | None = None
    execution_result: str | None = None
