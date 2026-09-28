"""WC-07 review correlation control, independent from Day state and transport."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class ReviewControlState(str, Enum):
    SENT = "SENT"
    RECEIVED = "RECEIVED"
    APPLIED = "APPLIED"
    VERIFIED = "VERIFIED"
    DELIVERY_FAILED = "DELIVERY_FAILED"


class ReviewResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    response_id: str = Field(min_length=1, max_length=120)
    in_reply_to: str = Field(min_length=1, max_length=160)
    result: str = Field(min_length=1, max_length=80)


class ReviewControl:
    """Keep one review request correlated without changing any Day state."""

    def __init__(self, *, timeout_seconds: int = 600) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self.timeout_seconds = timeout_seconds
        self.report_id: str | None = None
        self.state: ReviewControlState | None = None
        self.sent_at: datetime | None = None
        self.received_at: datetime | None = None
        self.applied_at: datetime | None = None
        self.verified_at: datetime | None = None
        self.response: ReviewResponse | None = None
        self.processed_response_ids: set[str] = set()
        self.failure_reason: str | None = None
        self.downstream_evidence_id: str | None = None

    def send(self, report_id: str, *, at: datetime) -> dict[str, object]:
        if self.report_id is not None and self.state not in {
            ReviewControlState.VERIFIED, ReviewControlState.DELIVERY_FAILED
        }:
            return self._view("REJECTED", "OUTSTANDING_REPORT_EXISTS")
        self.report_id = report_id
        self.state = ReviewControlState.SENT
        self.sent_at = self._aware(at)
        self.received_at = self.applied_at = self.verified_at = None
        self.response = None
        self.failure_reason = None
        self.downstream_evidence_id = None
        return self._view("ACCEPTED", None)

    def receive(self, raw: object, *, at: datetime, watcher_available: bool) -> dict[str, object]:
        response = ReviewResponse.model_validate(raw)
        now = self._aware(at)
        if response.response_id in self.processed_response_ids:
            return self._view("IGNORED", "DUPLICATE_RESPONSE")
        if self.state != ReviewControlState.SENT or self.report_id is None or self.sent_at is None:
            return self._view("REJECTED", "NO_SENT_OUTSTANDING_REPORT")
        if not watcher_available:
            return self._fail("WATCHER_UNAVAILABLE")
        if now > self.sent_at + timedelta(seconds=self.timeout_seconds):
            return self._fail("REVIEW_RESPONSE_TIMEOUT")
        if response.in_reply_to != self.report_id:
            return self._view("REJECTED", "IN_REPLY_TO_MISMATCH")
        self.response = response
        self.received_at = now
        self.state = ReviewControlState.RECEIVED
        self.processed_response_ids.add(response.response_id)
        return self._view("ACCEPTED", None)

    def apply(self, *, response_id: str, at: datetime) -> dict[str, object]:
        if self.state != ReviewControlState.RECEIVED or self.response is None:
            return self._view("REJECTED", "MATCHING_RESPONSE_NOT_RECEIVED")
        if response_id != self.response.response_id:
            return self._view("REJECTED", "RESPONSE_ID_MISMATCH")
        self.applied_at = self._aware(at)
        self.state = ReviewControlState.APPLIED
        return self._view("ACCEPTED", None)

    def verify(self, *, downstream_evidence_id: str, at: datetime) -> dict[str, object]:
        if self.state != ReviewControlState.APPLIED or not downstream_evidence_id:
            return self._view("REJECTED", "APPLIED_RESPONSE_EVIDENCE_MISSING")
        self.downstream_evidence_id = downstream_evidence_id
        self.verified_at = self._aware(at)
        self.state = ReviewControlState.VERIFIED
        return self._view("ACCEPTED", None)

    def check_deadline(self, *, at: datetime) -> dict[str, object]:
        now = self._aware(at)
        if (self.state == ReviewControlState.SENT and self.sent_at is not None
                and now > self.sent_at + timedelta(seconds=self.timeout_seconds)):
            return self._fail("REVIEW_RESPONSE_TIMEOUT")
        return self._view("UNCHANGED", None)

    def _fail(self, reason: str) -> dict[str, object]:
        self.state = ReviewControlState.DELIVERY_FAILED
        self.failure_reason = reason
        return self._view("FAILED", reason)

    @staticmethod
    def _aware(value: datetime) -> datetime:
        if value.utcoffset() is None:
            raise ValueError("review timestamps must include timezone")
        return value.astimezone(timezone.utc)

    def _view(self, outcome: str, reason_code: str | None) -> dict[str, object]:
        outstanding = self.report_id if self.state in {
            ReviewControlState.SENT, ReviewControlState.RECEIVED, ReviewControlState.APPLIED
        } else None
        return {
            "outcome": outcome,
            "reason_code": reason_code,
            "report_id": self.report_id,
            "outstanding_report_id": outstanding,
            "state": self.state.value if self.state else None,
            "response_id": self.response.response_id if self.response else None,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "received_at": self.received_at.isoformat() if self.received_at else None,
            "applied_at": self.applied_at.isoformat() if self.applied_at else None,
            "verified_at": self.verified_at.isoformat() if self.verified_at else None,
            "failure_reason": self.failure_reason,
            "downstream_evidence_id": self.downstream_evidence_id,
            "day_state_changed": False,
        }
