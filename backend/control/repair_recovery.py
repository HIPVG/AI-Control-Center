"""Deterministic WC-06 repair/recovery control boundary.

The controller records guarded fixture outcomes only. It never edits files,
executes a Day, grants authority, or resets an exhausted attempt budget.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from backend.models.local_llm_day import LocalLLMDayState, RunControl, RunRecord


class RepairAttemptInput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    run_id: str = Field(min_length=1, max_length=120)
    selected_day: int = Field(ge=1, le=14)
    failure_fingerprint: str = Field(min_length=8, max_length=128)
    action_fingerprint: str = Field(min_length=8, max_length=128)
    changed_paths: tuple[str, ...] = ()
    git_fingerprint: str = Field(min_length=8, max_length=128)
    active_work_seconds: int = Field(ge=0)
    verification_passed: bool


class RepairReviewInput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    request_id: str = Field(min_length=8, max_length=128)
    run_id: str = Field(min_length=1, max_length=120)
    selected_day: int = Field(ge=1, le=14)
    failure_fingerprint: str = Field(min_length=8, max_length=128)
    result: Literal["RECHECK", "REJECT"]


class RepairRecoveryController:
    """Fail-closed repair episode bound to one immutable RunRecord."""

    def __init__(self, record: RunRecord, *, allowed_paths: set[str]) -> None:
        self.record = record
        self.allowed_paths = frozenset(path.replace("\\", "/") for path in allowed_paths)
        self.attempts: list[dict[str, object]] = []
        self.review_request_id: str | None = None
        self.repeated_failure_fingerprint: str | None = None

    def record_attempt(self, raw: object) -> dict[str, object]:
        attempt = RepairAttemptInput.model_validate(raw)
        reason = self._guard_reason(attempt)
        if reason is not None:
            return self._view("REJECTED", reason)

        self.attempts.append(attempt.model_dump(mode="json"))
        if attempt.verification_passed:
            self._set_control(
                LocalLLMDayState.REVALIDATING,
                "Evaluate validator-owned Evidence for the same criterion.",
            )
            return self._view("REVALIDATING", None)

        same_failure_count = sum(
            item["failure_fingerprint"] == attempt.failure_fingerprint
            for item in self.attempts
        )
        if same_failure_count >= self.record.intent.requested_limits.max_attempts:
            self.repeated_failure_fingerprint = attempt.failure_fingerprint
            self.review_request_id = hashlib.sha256(
                f"{attempt.run_id}|{attempt.selected_day}|{attempt.failure_fingerprint}".encode("utf-8")
            ).hexdigest()[:32]
            self._set_control(
                LocalLLMDayState.HUMAN_ACTION_REQUIRED,
                "Await a matching review, then re-enter same-run PREFLIGHT checks.",
                blocker="REPEATED_FAILURE_ATTEMPT_LIMIT",
                resume_target="PREFLIGHT",
            )
            return self._view("HUMAN_ACTION_REQUIRED", "REPEATED_FAILURE_ATTEMPT_LIMIT")

        self._set_control(
            LocalLLMDayState.DIAGNOSING_GAP,
            "One bounded repair attempt remains for this failure fingerprint.",
        )
        return self._view("DIAGNOSING_GAP", "DETERMINISTIC_REVALIDATION_FAILED")

    def apply_review(self, raw: object) -> dict[str, object]:
        review = RepairReviewInput.model_validate(raw)
        expected = (
            self.record.control.current_state == LocalLLMDayState.HUMAN_ACTION_REQUIRED
            and self.review_request_id is not None
            and review.request_id == self.review_request_id
            and review.run_id == self.record.intent.run_id
            and review.selected_day == self.record.intent.selected_day
            and review.failure_fingerprint == self.repeated_failure_fingerprint
        )
        if not expected:
            return self._view("REVIEW_REJECTED", "REVIEW_CORRELATION_MISMATCH")
        if review.result == "REJECT":
            return self._view("HUMAN_ACTION_REQUIRED", "REVIEW_REJECTED_REPAIR")

        self._set_control(
            LocalLLMDayState.PREFLIGHT,
            "Recheck contract, authority, Git, budget, attempt limit and Evidence for the same run.",
        )
        return self._view("PREFLIGHT", None)

    def _guard_reason(self, attempt: RepairAttemptInput) -> str | None:
        if attempt.run_id != self.record.intent.run_id or attempt.selected_day != self.record.intent.selected_day:
            return "RUN_IDENTITY_MISMATCH"
        if len(self.attempts) >= self.record.intent.requested_limits.max_attempts:
            return "ATTEMPT_LIMIT_EXHAUSTED"
        if attempt.active_work_seconds > self.record.intent.requested_limits.active_work_seconds:
            return "ACTIVE_WORK_BUDGET_EXCEEDED"
        if attempt.git_fingerprint != self.record.intent.git_fingerprint:
            return "GIT_FINGERPRINT_MISMATCH"
        normalized = {path.replace("\\", "/") for path in attempt.changed_paths}
        if not normalized or not normalized.issubset(self.allowed_paths):
            return "REPAIR_SCOPE_REJECTED"
        return None

    def _set_control(
        self,
        state: LocalLLMDayState,
        next_action: str,
        *,
        blocker: str | None = None,
        resume_target: Literal["PREFLIGHT"] | None = None,
    ) -> None:
        prior = self.record.control
        history = (*prior.state_history, prior.current_state)
        control = RunControl(
            run_id=prior.run_id,
            selected_day=prior.selected_day,
            contract_fingerprint=prior.contract_fingerprint,
            current_state=state,
            state_history=history,
            next_action=next_action,
            blocker=blocker,
            resume_target=resume_target,
            updated_at=datetime.now(timezone.utc),
        )
        self.record = RunRecord(intent=self.record.intent, control=control)

    def _view(self, status: str, reason_code: str | None) -> dict[str, object]:
        return {
            "status": status,
            "reason_code": reason_code,
            "run_id": self.record.intent.run_id,
            "selected_day": self.record.intent.selected_day,
            "control": self.record.control.model_dump(mode="json"),
            "attempt_count": len(self.attempts),
            "review_request_id": self.review_request_id,
            "failure_fingerprint": self.repeated_failure_fingerprint,
            "repair_executed": False,
            "day_execution_started": False,
        }
