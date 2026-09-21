from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ExperimentOutcome(str, Enum):
    RESULT_RECORDED = "RESULT_RECORDED"
    MODEL_QUALITY_FINDING = "MODEL_QUALITY_FINDING"
    ENGINE_UNAVAILABLE = "ENGINE_UNAVAILABLE"
    MODEL_NOT_FOUND = "MODEL_NOT_FOUND"
    TIMEOUT = "TIMEOUT"
    CONFIGURATION_BLOCKED = "CONFIGURATION_BLOCKED"
    HARNESS_FAILURE = "HARNESS_FAILURE"


class TrustedExperiment(BaseModel):
    experiment_id: str
    project_id: str
    runner: str
    model: str
    cases: list[str] = Field(min_length=1)
    timeout_seconds: int = Field(default=120, ge=1, le=900)
    output_root: str


class ExperimentRun(BaseModel):
    experiment_id: str
    project_id: str
    started_at: datetime
    completed_at: datetime | None = None
    outcome: ExperimentOutcome
    runner_exit_code: int | None = None
    artifact_path: str | None = None
    model: str | None = None
    engine: str | None = None
    response_count: int = 0
    success_count: int = 0
    failed_count: int = 0
    classification_reason: str
    builder_invoked: bool = False
