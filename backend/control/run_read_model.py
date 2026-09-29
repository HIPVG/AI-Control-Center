"""WC-09 read-only projection; persisted state is not runtime-liveness proof."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from backend.models.local_llm_day import RunRecord, RunTelemetry


class AdmissionProjection(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    run_id: str
    status: Literal["ADMISSIBLE", "BLOCKED"]
    reason_code: str | None = None
    observed_at: datetime
    source: str = Field(min_length=1)


class CriterionProjection(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    run_id: str
    criterion_id: str
    satisfied: bool
    evidence_record_ids: tuple[str, ...] = ()
    observed_at: datetime
    source: str = Field(min_length=1)


class ReviewProjection(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    run_id: str
    report_id: str
    state: str
    response_id: str | None = None
    observed_at: datetime
    source: str = Field(min_length=1)


class HumanDecisionProjection(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    run_id: str
    decision_id: str
    subject_type: str
    target_commit: str
    decision_effect: str
    human_response_state: str
    human_message_id: str | None = None
    human_source_class: str | None = None
    reviewer_confirmation_state: str
    confirmation_report_id: str | None = None
    confirmation_response_id: str | None = None
    observed_at: datetime
    source: str = Field(min_length=1)


class RuntimeObservation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    run_id: str
    running: bool
    observed_at: datetime
    source: str = Field(min_length=1)


class RunReadModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    current: RunRecord | None = None
    history: tuple[RunRecord, ...] = ()
    admission: AdmissionProjection | None = None
    criteria: tuple[CriterionProjection, ...] = ()
    review: ReviewProjection | None = None
    telemetry: RunTelemetry | None = None
    human_decision: HumanDecisionProjection | None = None
    runtime_observation: RuntimeObservation | None = None
    projection_errors: tuple[str, ...] = ()
    projected_at: datetime
    source: str = Field(min_length=1)

    @field_validator("projected_at")
    @classmethod
    def projected_at_has_timezone(cls, value: datetime) -> datetime:
        if value.utcoffset() is None:
            raise ValueError("projection time must include timezone")
        return value

    @model_validator(mode="after")
    def matching_run_identity(self) -> "RunReadModel":
        if self.current is None:
            if any((self.admission, self.criteria, self.review, self.telemetry,
                    self.human_decision, self.runtime_observation)):
                raise ValueError("Current run is required for run-bound projection data")
            return self
        run_id = self.current.intent.run_id
        bound = [self.admission, self.review, self.telemetry,
                 self.human_decision, self.runtime_observation, *self.criteria]
        if any(item is not None and item.run_id != run_id for item in bound):
            raise ValueError("Read projection run ID mismatch")
        return self

    def read(self) -> dict[str, object]:
        current = self.current
        current_view = None
        if current is not None:
            runtime = self.runtime_observation
            liveness = "UNKNOWN" if runtime is None else (
                "OBSERVED_RUNNING" if runtime.running else "OBSERVED_NOT_RUNNING"
            )
            current_view = {
                "run_id": current.intent.run_id,
                "selected_day": current.intent.selected_day,
                "state": current.control.current_state.value,
                "state_updated_at": current.control.updated_at.isoformat(),
                "next_action": current.control.next_action,
                "blocker": current.control.blocker,
                "resume_target": current.control.resume_target,
                "liveness": liveness,
                "runtime_observed_at": runtime.observed_at.isoformat() if runtime else None,
                "runtime_source": runtime.source if runtime else None,
                "source": "RunRecord",
            }
        return {
            "read_only": True,
            "projected_at": self.projected_at.isoformat(),
            "projection_source": self.source,
            "projection_errors": list(self.projection_errors),
            "selected": current is not None,
            "current": current_view,
            "history": [{
                "run_id": item.intent.run_id,
                "selected_day": item.intent.selected_day,
                "state": item.control.current_state.value,
                "state_updated_at": item.control.updated_at.isoformat(),
                "source": "RunRecord history",
                "is_current": False,
            } for item in self.history],
            "admission": self.admission.model_dump(mode="json") if self.admission else None,
            "unmet_criteria": [item.model_dump(mode="json") for item in self.criteria if not item.satisfied],
            "review": self.review.model_dump(mode="json") if self.review else None,
            "telemetry": self.telemetry.model_dump(mode="json") if self.telemetry else None,
            "human_decision": self.human_decision.model_dump(mode="json") if self.human_decision else None,
        }


def empty_run_read_model(
    *, at: datetime, projection_errors: tuple[str, ...] = ()
) -> RunReadModel:
    return RunReadModel(
        projected_at=at,
        source="No current RunRecord selected",
        projection_errors=projection_errors,
    )
