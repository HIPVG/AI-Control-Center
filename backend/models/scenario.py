from enum import Enum

from pydantic import BaseModel, Field


class ScenarioKind(str, Enum):
    CHECKPOINT = "CHECKPOINT"
    REPEAT_EXPERIMENT = "REPEAT_EXPERIMENT"


class Scenario(BaseModel):
    scenario_id: str
    title: str
    kind: ScenarioKind
    capability_id: str | None = None
    max_runs: int = Field(default=0, ge=0, le=20)
    required_successes: int = Field(default=0, ge=0, le=20)
    checkpoint_reference: str | None = None
