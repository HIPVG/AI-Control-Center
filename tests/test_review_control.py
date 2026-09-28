from datetime import datetime, timedelta, timezone

from backend.control.review_control import ReviewControl


NOW = datetime(2026, 9, 29, tzinfo=timezone.utc)


def _response(report_id="R-001", response_id="RESP-001"):
    return {"response_id": response_id, "in_reply_to": report_id, "result": "CONTINUE"}


def test_matching_response_applies_once_and_requires_downstream_evidence_to_verify():
    control = ReviewControl()
    assert control.send("R-001", at=NOW)["state"] == "SENT"
    assert control.receive(_response(), at=NOW + timedelta(seconds=5), watcher_available=True)["state"] == "RECEIVED"
    assert control.apply(response_id="RESP-001", at=NOW + timedelta(seconds=6))["state"] == "APPLIED"
    assert control.verify(downstream_evidence_id="REPORT-R-002", at=NOW + timedelta(seconds=7))["state"] == "VERIFIED"
    terminal = control._view("UNCHANGED", None)
    assert terminal["day_state_changed"] is False
    assert terminal["outstanding_report_id"] is None

    duplicate = control.receive(_response(), at=NOW + timedelta(seconds=8), watcher_available=True)
    assert duplicate["reason_code"] == "DUPLICATE_RESPONSE"
    assert duplicate["state"] == "VERIFIED"


def test_wrong_in_reply_to_is_not_applied_and_outstanding_remains_sent():
    control = ReviewControl()
    control.send("R-001", at=NOW)

    result = control.receive(_response(report_id="R-OTHER"), at=NOW + timedelta(seconds=1), watcher_available=True)

    assert result["reason_code"] == "IN_REPLY_TO_MISMATCH"
    assert result["state"] == "SENT"
    assert result["outstanding_report_id"] == "R-001"
    assert result["response_id"] is None
    assert control.apply(response_id="RESP-001", at=NOW + timedelta(seconds=2))["reason_code"] == "MATCHING_RESPONSE_NOT_RECEIVED"


def test_watcher_unavailable_fails_closed_without_receiving_response():
    control = ReviewControl()
    control.send("R-001", at=NOW)

    result = control.receive(_response(), at=NOW + timedelta(seconds=1), watcher_available=False)

    assert result["state"] == "DELIVERY_FAILED"
    assert result["reason_code"] == "WATCHER_UNAVAILABLE"
    assert result["response_id"] is None
    assert result["outstanding_report_id"] is None
    assert result["day_state_changed"] is False


def test_deadline_expiry_fails_closed_and_late_response_cannot_apply():
    control = ReviewControl(timeout_seconds=600)
    control.send("R-001", at=NOW)

    expired = control.check_deadline(at=NOW + timedelta(seconds=601))
    late = control.receive(_response(), at=NOW + timedelta(seconds=602), watcher_available=True)

    assert expired["state"] == "DELIVERY_FAILED"
    assert expired["reason_code"] == "REVIEW_RESPONSE_TIMEOUT"
    assert expired["outstanding_report_id"] is None
    assert late["reason_code"] == "NO_SENT_OUTSTANDING_REPORT"
    assert control.apply(response_id="RESP-001", at=NOW + timedelta(seconds=603))["reason_code"] == "MATCHING_RESPONSE_NOT_RECEIVED"


def test_second_outstanding_report_is_rejected_until_terminal_state():
    control = ReviewControl()
    control.send("R-001", at=NOW)

    result = control.send("R-002", at=NOW + timedelta(seconds=1))

    assert result["reason_code"] == "OUTSTANDING_REPORT_EXISTS"
    assert result["report_id"] == "R-001"
    assert result["state"] == "SENT"
