from enum import Enum

from pydantic import BaseModel


class NextActionType(str, Enum):
    RUN_TRUSTED_EXPERIMENT = "RUN_TRUSTED_EXPERIMENT"
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
