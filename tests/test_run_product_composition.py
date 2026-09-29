from datetime import datetime, timedelta, timezone
from pathlib import Path
import shutil
import subprocess

from fastapi.testclient import TestClient

import backend.app as control_app
from backend.control.human_decision import DecisionRequest, HumanResponse, SubjectType
from backend.control.projects import ConfiguredProject, ProjectRegistry
from backend.control.run_composition import RunPreflightFacts
from backend.control.run_store import JsonRunStore
from backend.control.run_telemetry_store import JsonRunTelemetryStore
from backend.models.local_llm_day import (
    LocalLLMDaySnapshot,
    LocalLLMDayState,
    RunTelemetry,
    TelemetryMetric,
)
from backend.models.runtime import RuntimeConfig
from backend.orchestrator.engine import ControlCenterEngine, JsonStateStore


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "day-contract"
NOW = datetime(2026, 9, 29, 12, 0, tzinfo=timezone.utc)


def _engine(tmp_path, *, admitted=True):
    holder = {}
    calls = []

    def execute(run_id, day):
        engine = holder["engine"]
        contract = engine.local_llm_day_program._load_contracts()[day]
        engine.local_llm_day_program.snapshot = LocalLLMDaySnapshot(
            run_id=run_id,
            selected_day=day,
            state=LocalLLMDayState.PREFLIGHT,
            objective=contract.objective,
            contract=contract,
            contract_fingerprint=engine.local_llm_day_program._contract_fingerprint(contract),
            activity="Injected executor reached the production composition root.",
        )
        engine.local_llm_day_program._save()
        calls.append((run_id, day))
        return {"run_id": run_id, "result": "INJECTED_ONLY"}

    fixture_repository = tmp_path / "repository"
    if not fixture_repository.exists():
        shutil.copytree(FIXTURE_ROOT, fixture_repository)
        subprocess.run(
            ["git", "init", "-b", "main", str(fixture_repository)],
            check=True, capture_output=True, text=True,
        )
        subprocess.run(
            ["git", "-C", str(fixture_repository), "config", "user.name", "Fixture"],
            check=True, capture_output=True, text=True,
        )
        subprocess.run(
            ["git", "-C", str(fixture_repository), "config", "user.email", "fixture@example.invalid"],
            check=True, capture_output=True, text=True,
        )
        subprocess.run(
            ["git", "-C", str(fixture_repository), "add", "."],
            check=True, capture_output=True, text=True,
        )
        subprocess.run(
            ["git", "-C", str(fixture_repository), "commit", "-m", "fixture baseline"],
            check=True, capture_output=True, text=True,
        )
    registry = ProjectRegistry(projects={
        "local_llm_lab": ConfiguredProject(
            name="LocalLLM-Lab", path=fixture_repository.resolve(), default_branch="main"
        )
    })
    engine = ControlCenterEngine(
        state_store=JsonStateStore(tmp_path / "control-center.json"),
        runtime_config=RuntimeConfig(),
        project_registry=registry,
        local_llm_run_store=JsonRunStore(tmp_path / "runs"),
        local_llm_telemetry_store=JsonRunTelemetryStore(tmp_path / "telemetry"),
        local_llm_preflight_resolver=lambda _day: RunPreflightFacts(admitted, admitted),
        local_llm_run_executor=execute,
    )
    holder["engine"] = engine
    return engine, calls


def _api(engine):
    previous = control_app.engine
    control_app.engine = engine
    client = TestClient(control_app.app)

    def restore():
        client.close()
        control_app.engine = previous

    return client, restore


def _evidence(run_id, criterion_id, evidence_type, config_fingerprint, value):
    return {
        "run_id": run_id,
        "criterion_id": criterion_id,
        "evidence_type": evidence_type,
        "provider_id": "ri03-injected-executor",
        "provider_version": "v1",
        "source_fingerprint": "s" * 64,
        "configuration_fingerprint": config_fingerprint,
        "value": value,
    }


def _evidence_value(evidence_type):
    return {
        "schema_contract": {"schema_path": "schema.json", "schema_version": "v1"},
        "source_check": {"checked_paths": ["src/state.py"], "assertions": ["states differ"]},
        "provenance_test": {"exit_code": 0, "commands": ["pytest provenance"], "passed": 1, "failed": 0},
        "deterministic_tests": {"exit_code": 0, "commands": ["pytest temporal"], "passed": 1, "failed": 0},
        "architecture_check": {"checked_documents": ["docs/architecture.md"], "assertions": ["server owns state"]},
    }[evidence_type]


def _metric(value, unit, source):
    return TelemetryMetric(value=value, unit=unit, source=source, observed_at=NOW)


def test_actual_api_to_evidence_telemetry_terminal_readback_uses_one_run(tmp_path):
    engine, calls = _engine(tmp_path)
    client, restore = _api(engine)
    try:
        before = client.get("/api/local-llm/runs").json()
        go = client.post("/api/local-llm/day/go", json={"selected_day": 6}).json()
        run_id = go["run_id"]

        assert before["selected"] is False
        assert go["execution_started"] is True
        assert calls == [(run_id, 6)]
        assert go["execution"]["run_id"] == run_id

        record = engine.local_llm_run_store.get(run_id)
        contract = engine.local_llm_day_program.snapshot.contract
        for criterion in contract.completion_criteria:
            results = [
                _evidence(
                    run_id, criterion.criterion_id, evidence_type,
                    record.intent.config_fingerprint, _evidence_value(evidence_type),
                )
                for evidence_type in criterion.required_evidence
            ]
            result = engine.local_llm_run_product.execution.evaluate_criterion(
                run_id, criterion_id=criterion.criterion_id, results=results
            )
            assert result["criterion_satisfied"] is True

        engine.local_llm_day_program.snapshot.state = LocalLLMDayState.COMPLETE
        engine.local_llm_day_program.snapshot.activity = "All declared evidence validated."
        engine.local_llm_day_program._save()
        projected = engine.local_llm_run_product.execution.project_day_state(run_id)
        telemetry = RunTelemetry(
            run_id=run_id,
            manual_relay_count=_metric(0, "count", "RI-03 fixture"),
            attempt_count=_metric(1, "attempts", "RI-03 fixture"),
            attempt_limit=_metric(2, "attempts", "RunIntent"),
            input_tokens=TelemetryMetric(value=None, unit="tokens", observed_at=NOW, unknown_reason="not measured"),
            output_tokens=TelemetryMetric(value=None, unit="tokens", observed_at=NOW, unknown_reason="not measured"),
            cost=_metric(0, "JPY", "authorized fixture limit"),
            captured_at=NOW,
        )
        assert engine.local_llm_run_product.record_telemetry(run_id, telemetry)["outcome"] == "ACCEPTED"
        readback = client.get("/api/local-llm/runs").json()

        assert projected["control"]["current_state"] == "COMPLETE"
        assert readback["current"]["run_id"] == run_id
        assert readback["current"]["state"] == "COMPLETE"
        assert readback["telemetry"]["run_id"] == run_id
        assert readback["unmet_criteria"] == []

        restarted, restarted_calls = _engine(tmp_path)
        restarted_readback = restarted.local_llm_run_read_model()
        assert restarted_calls == []
        assert restarted_readback["current"]["run_id"] == run_id
        assert restarted_readback["current"]["state"] == "COMPLETE"
        assert restarted_readback["telemetry"]["run_id"] == run_id
    finally:
        restore()


def test_failure_controls_preserve_one_run_and_reject_unauthorized_effects(tmp_path):
    engine, calls = _engine(tmp_path)
    client, restore = _api(engine)
    try:
        go = client.post("/api/local-llm/day/go", json={"selected_day": 6}).json()
        run_id = go["run_id"]
        record = engine.local_llm_run_store.get(run_id)
        criterion = engine.local_llm_day_program.snapshot.contract.completion_criteria[0]
        invalid = [_evidence(
            "other-run", criterion.criterion_id, criterion.required_evidence[0],
            record.intent.config_fingerprint, _evidence_value(criterion.required_evidence[0]),
        )]
        rejected = engine.local_llm_run_product.execution.evaluate_criterion(
            run_id, criterion_id=criterion.criterion_id, results=invalid
        )
        assert rejected["criterion_satisfied"] is False
        assert engine.local_llm_run_store.get(run_id).control.current_state == LocalLLMDayState.PREFLIGHT

        execution = engine.local_llm_run_product.execution
        execution.begin_repair(run_id, allowed_paths={"src/temporal.py"})
        attempt = {
            "run_id": run_id, "selected_day": 6,
            "failure_fingerprint": "failure-0001", "action_fingerprint": "action-00001",
            "changed_paths": ["src/temporal.py"], "git_fingerprint": record.intent.git_fingerprint,
            "active_work_seconds": 60, "verification_passed": False,
        }
        execution.record_repair_attempt(run_id, attempt)
        second = execution.record_repair_attempt(run_id, {**attempt, "action_fingerprint": "action-00002"})
        third = execution.record_repair_attempt(run_id, {**attempt, "action_fingerprint": "action-00003"})
        assert second["status"] == "HUMAN_ACTION_REQUIRED"
        assert third["reason_code"] == "ATTEMPT_LIMIT_EXHAUSTED"

        execution.request_review(run_id, "REPORT-RI03", at=NOW)
        stale = execution.apply_review_response(
            run_id, {"response_id": "RESP-OLD", "in_reply_to": "REPORT-OLD", "result": "CONTINUE"},
            comment_id="COMMENT-OLD", at=NOW + timedelta(seconds=1), exit_code=0,
            envelope_valid=True, envelope_validation_reason="valid",
            downstream_effect_id="EFFECT-OLD", observed_effect_id="EFFECT-OLD",
        )
        assert stale["reason_code"] == "IN_REPLY_TO_MISMATCH"
        waiting = engine.local_llm_run_store.get(run_id)
        assert waiting.control.current_state == LocalLLMDayState.HUMAN_ACTION_REQUIRED

        matched = execution.apply_review_response(
            run_id, {"response_id": "RESP-RI03", "in_reply_to": "REPORT-RI03", "result": "CONTINUE"},
            comment_id="COMMENT-RI03", at=NOW + timedelta(seconds=2), exit_code=0,
            envelope_valid=True, envelope_validation_reason="identity valid",
            downstream_effect_id="EFFECT-RI03", observed_effect_id="EFFECT-RI03",
        )
        assert matched["review"]["state"] == "VERIFIED"
        assert engine.local_llm_run_store.get(run_id).control.current_state == LocalLLMDayState.PREFLIGHT

        decision = DecisionRequest(
            decision_id="DECISION-RI03", revision=1,
            subject_type=SubjectType.EXECUTION_AUTHORITY,
            decision_subject="Resume the same fixture run", target_commit="a" * 40,
            requested_effect="RETURN_TO_PREFLIGHT",
        )
        execution.bind_human_decision(run_id, decision)
        received = execution.receive_human_decision(
            run_id,
            HumanResponse(
                exact_text="承認します", decider="広瀬剛", channel="Codex Work chat",
                message_id="MSG-RI03", source_class="RECORDED_DIRECT_CONVERSATION",
                received_at=NOW + timedelta(seconds=3), decision_id="DECISION-RI03",
                revision=1, subject_type=SubjectType.EXECUTION_AUTHORITY,
                target_commit="a" * 40, decision_effect="RETURN_TO_PREFLIGHT",
                subject_basis="The bound RI-03 decision request",
            ),
        )
        execution.build_human_confirmation(
            run_id, received["record_id"], confirmation_report_id="CONFIRM-RI03",
            confirms_report_id="REPORT-HUMAN-RI03", confirms_response_id="RESP-HUMAN-RI03",
            authority_record="AUTH-RI03",
        )
        confirmed = execution.apply_human_confirmation(
            run_id, received["record_id"],
            {
                "RESPONSE_ID": "CONFIRM-RESP-RI03", "IN_REPLY_TO": "CONFIRM-RI03",
                "CONFIRMS_REPORT_ID": "REPORT-HUMAN-RI03",
                "CONFIRMS_RESPONSE_ID": "RESP-HUMAN-RI03",
                "DECISION_ID": "DECISION-RI03", "DECISION_REVISION": 1,
                "REVIEWED_COMMIT": "a" * 40, "SUBJECT_TYPE": "EXECUTION_AUTHORITY",
                "DECISION_EFFECT": "RETURN_TO_PREFLIGHT", "RESULT": "CONTINUE",
            },
            continuation_succeeded=True, effect_evidence_id="HUMAN-EFFECT-RI03",
        )
        assert confirmed["effect_applied"] is True
        assert confirmed["run_id"] == run_id
        assert engine.local_llm_run_store.get(run_id).control.current_state == LocalLLMDayState.PREFLIGHT
        assert calls == [(run_id, 6)]
    finally:
        restore()


def test_blocked_admission_persists_reason_and_never_calls_executor(tmp_path):
    engine, calls = _engine(tmp_path, admitted=None)
    client, restore = _api(engine)
    try:
        result = client.post("/api/local-llm/day/go", json={"selected_day": 6}).json()
        assert result["execution_started"] is False
        assert result["run_record"]["control"]["current_state"] == "HUMAN_ACTION_REQUIRED"
        assert result["run_record"]["control"]["blocker"] == "EFFECTIVE_PERMISSION_UNKNOWN"
        assert calls == []
    finally:
        restore()
