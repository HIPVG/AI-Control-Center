from enum import Enum

from pydantic import BaseModel


class NextActionType(str, Enum):
    NO_FURTHER_ACTION = "NO_FURTHER_ACTION"
    COMPLETE_VERIFIED_WORK = "COMPLETE_VERIFIED_WORK"
    RUN_TRUSTED_EXPERIMENT = "RUN_TRUSTED_EXPERIMENT"
    RUN_WEEK1_DAY = "RUN_WEEK1_DAY"
    EXTERNAL_ACTION_REQUIRED = "EXTERNAL_ACTION_REQUIRED"
    HUMAN_DECISION_REQUIRED = "HUMAN_DECISION_REQUIRED"


class NextAction(BaseModel):
    """A deterministic, policy-bounded continuation recommendation."""

    action_type: NextActionType
    target_id: str | None = None
    summary: str
    reason: str
    reasoning_required: bool = False
    human_attention_required: bool = False
    policy_result: str
