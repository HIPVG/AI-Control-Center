from enum import Enum

from pydantic import BaseModel, Field


class EvaluationDecision(str, Enum):
    PASS = "PASS"
    REPAIR = "REPAIR"
    HUMAN_REVIEW = "HUMAN_REVIEW"


class EvaluationResult(BaseModel):
    decision: EvaluationDecision
    score: dict[str, float] = Field(default_factory=dict)
    blocking_issues: list[str] = Field(default_factory=list)
    repair_instruction: str | None = None
