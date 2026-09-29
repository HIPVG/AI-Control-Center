from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

import backend.app as control_app
from backend.control.run_read_model import (
    AdmissionProjection,
    CriterionProjection,
    HumanDecisionProjection,
    ReviewProjection,
    RunReadModel,
    RuntimeObservation,
    empty_run_read_model,
)
from backend.models.local_llm_day import (
    LocalLLMDayState,
    RunControl,
    RunIntent,
    RunLimits,
    RunRecord,
    RunTelemetry,
    TelemetryMetric,
)


NOW = datetime(2026, 9, 29, tzinfo=timezone.utc)


def record(run_id="run-001", state=LocalLLMDayState.PREFLIGHT, day=6):
    intent = RunIntent(run_id=run_id, selected_day=day, go_at=NOW,
                       contract_fingerprint="contract-v1", policy_fingerprint="policy-v1",
                       config_fingerprint="config-v1", git_fingerprint="git-base-v1",
                       requested_limits=RunLimits(active_work_seconds=1800, max_attempts=2,
                                                  max_cost=0, currency="JPY"))
    return RunRecord(intent=intent, control=RunControl(
        run_id=run_id, selected_day=day, contract_fingerprint="contract-v1",
        current_state=state, state_history=(LocalLLMDayState.IDLE,),
        next_action="Resolve the recorded blocker" if state == LocalLLMDayState.STOPPED else "Validate preflight",
        blocker="AUTHORITY_UNKNOWN" if state == LocalLLMDayState.STOPPED else None,
        resume_target="PREFLIGHT" if state == LocalLLMDayState.STOPPED else None,
        updated_at=NOW,
    ))


def metric(value, unit, source=None, reason=None):
    return TelemetryMetric(value=value, unit=unit, source=source, observed_at=NOW,
                           unknown_reason=reason)


def telemetry():
    return RunTelemetry(run_id="run-001",
                        manual_relay_count=metric(0, "count", "review registry"),
                        attempt_count=metric(0, "attempts", "repair history"),
                        attempt_limit=metric(2, "attempts", "RunIntent"),
                        input_tokens=metric(None, "tokens", reason="not observed"),
                        output_tokens=metric(None, "tokens", reason="not observed"),
                        cost=metric(0.0, "JPY", "fixture authority"), captured_at=NOW)


def test_api_is_get_only_and_unselected_is_explicit(monkeypatch):
    monkeypatch.setattr(
        control_app.engine,
        "local_llm_run_read_model",
        lambda: empty_run_read_model(at=NOW).read(),
    )
    client = TestClient(control_app.app)
    body = client.get("/api/local-llm/runs").json()
    assert body["read_only"] is True
    assert body["selected"] is False and body["current"] is None
    assert body["history"] == []
    assert body["projection_source"] == "No current RunRecord selected"
    assert client.post("/api/local-llm/runs", json={"state": "RUNNING"}).status_code == 405


def test_preflight_projection_keeps_run_time_source_and_unmet_criterion(monkeypatch):
    read_model = RunReadModel(
        current=record(),
        admission=AdmissionProjection(run_id="run-001", status="ADMISSIBLE",
                                      observed_at=NOW, source="WC-02 fixture"),
        criteria=(CriterionProjection(run_id="run-001", criterion_id="C1", satisfied=False,
                                      observed_at=NOW, source="Evidence evaluator"),),
        projected_at=NOW, source="fixture aggregation",
    )
    monkeypatch.setattr(control_app.engine, "local_llm_run_read_model", read_model.read)
    model = TestClient(control_app.app).get("/api/local-llm/runs").json()
    assert model["current"]["run_id"] == "run-001"
    assert model["current"]["state"] == "PREFLIGHT"
    assert model["current"]["liveness"] == "UNKNOWN"
    assert model["unmet_criteria"][0]["criterion_id"] == "C1"
    assert model["admission"]["source"] == "WC-02 fixture"


def test_stopped_current_history_and_unknown_telemetry_stay_distinct():
    body = RunReadModel(current=record(state=LocalLLMDayState.STOPPED),
                        history=(record("run-old", LocalLLMDayState.COMPLETE, 1),),
                        telemetry=telemetry(), projected_at=NOW, source="fixture aggregation").read()
    assert body["current"]["state"] == "STOPPED"
    assert body["current"]["blocker"] == "AUTHORITY_UNKNOWN"
    assert body["history"][0]["run_id"] == "run-old"
    assert body["history"][0]["is_current"] is False
    assert body["telemetry"]["input_tokens"]["value"] is None
    assert body["telemetry"]["input_tokens"]["unknown_reason"] == "not observed"


def test_persisted_running_state_without_runtime_observation_is_not_live_proof():
    unknown = RunReadModel(current=record(state=LocalLLMDayState.RUNNING),
                           projected_at=NOW, source="fixture aggregation").read()
    observed = RunReadModel(current=record(state=LocalLLMDayState.RUNNING),
                            runtime_observation=RuntimeObservation(
                                run_id="run-001", running=False, observed_at=NOW,
                                source="process probe"), projected_at=NOW,
                            source="fixture aggregation").read()
    assert unknown["current"]["liveness"] == "UNKNOWN"
    assert unknown["current"]["runtime_source"] is None
    assert observed["current"]["liveness"] == "OBSERVED_NOT_RUNNING"
    assert observed["current"]["runtime_source"] == "process probe"


def test_human_response_and_reviewer_confirmation_are_separate_states():
    decision = HumanDecisionProjection(
        run_id="run-001", decision_id="D1", subject_type="GATE_EXIT",
        target_commit="a" * 40, decision_effect="complete G6 exit",
        human_response_state="HUMAN_DECISION_RECEIVED", human_message_id="M1",
        human_source_class="RECORDED_DIRECT_CONVERSATION",
        reviewer_confirmation_state="REVIEW_CONFIRMATION_PENDING",
        confirmation_report_id="R2", confirmation_response_id=None,
        observed_at=NOW, source="HumanDecision record",
    )
    review = ReviewProjection(run_id="run-001", report_id="R2", state="SENT",
                              observed_at=NOW, source="Review Control")
    body = RunReadModel(current=record(), human_decision=decision, review=review,
                        projected_at=NOW, source="fixture aggregation").read()
    assert body["human_decision"]["human_response_state"] == "HUMAN_DECISION_RECEIVED"
    assert body["human_decision"]["reviewer_confirmation_state"] == "REVIEW_CONFIRMATION_PENDING"
    assert body["human_decision"]["confirmation_response_id"] is None
    assert body["review"]["state"] == "SENT"


@pytest.mark.parametrize("field,value", [
    ("admission", AdmissionProjection(run_id="wrong", status="BLOCKED", reason_code="X",
                                      observed_at=NOW, source="fixture")),
    ("criteria", (CriterionProjection(run_id="wrong", criterion_id="C1", satisfied=False,
                                      observed_at=NOW, source="fixture"),)),
    ("runtime_observation", RuntimeObservation(run_id="wrong", running=True,
                                               observed_at=NOW, source="probe")),
])
def test_inconsistent_run_identity_fails_before_projection(field, value):
    with pytest.raises(ValidationError, match="run ID mismatch"):
        RunReadModel(current=record(), projected_at=NOW, source="fixture", **{field: value})
