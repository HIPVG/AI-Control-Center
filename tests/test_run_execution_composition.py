from datetime import datetime, timedelta, timezone
from pathlib import Path

from backend.control.human_decision import DecisionRequest, HumanResponse, SubjectType
from backend.control.local_llm_day_program import LocalLLMDayProgram
from backend.control.run_execution_composition import RunExecutionComposition
from backend.control.run_store import JsonRunStore
from backend.models.local_llm_day import (
    LocalLLMDaySnapshot,
    LocalLLMDayState,
    RunControl,
    RunIntent,
    RunLimits,
    RunRecord,
)


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "day-contract"
NOW = datetime(2026, 9, 29, 9, 0, tzinfo=timezone.utc)


def _fixture(tmp_path):
    program = LocalLLMDayProgram(FIXTURE_ROOT)
    contract = program._load_contracts()[6]
    program.snapshot = LocalLLMDaySnapshot(
        run_id="run-ri01",
        selected_day=6,
        state=LocalLLMDayState.PREFLIGHT,
        contract=contract,
        contract_fingerprint=program._contract_fingerprint(contract),
        activity="Run same identity through preflight.",
    )
    intent = RunIntent(
        run_id="run-ri01", selected_day=6, go_at=NOW,
        contract_fingerprint=program._contract_fingerprint(contract),
        policy_fingerprint="p" * 64, config_fingerprint="c" * 64,
        git_fingerprint="g" * 64,
        requested_limits=RunLimits(
            active_work_seconds=1800, max_attempts=2, max_cost=0, currency="JPY"
        ),
    )
    record = RunRecord(
        intent=intent,
        control=RunControl(
            run_id=intent.run_id, selected_day=6,
            contract_fingerprint=intent.contract_fingerprint,
            current_state=LocalLLMDayState.PREFLIGHT,
            next_action="Run preflight.", updated_at=NOW,
        ),
    )
    store = JsonRunStore(tmp_path / "runs")
    store.create(record)
    composition = RunExecutionComposition(
        program, store, clock=lambda: NOW + timedelta(seconds=10)
    )
    return composition, program, store, contract, intent


def _evidence(intent, criterion, evidence_type, value, **updates):
    result = {
        "run_id": intent.run_id,
        "criterion_id": criterion.criterion_id,
        "evidence_type": evidence_type,
        "provider_id": "ri01-fixture",
        "provider_version": "v1",
        "source_fingerprint": "s" * 64,
        "configuration_fingerprint": intent.config_fingerprint,
        "value": value,
    }
    result.update(updates)
    return result


def _value(evidence_type):
    return {
        "schema_contract": {"schema_path": "schema.json", "schema_version": "v1"},
        "source_check": {
            "checked_paths": ["src/state.py"],
            "assertions": ["planned and actual are distinct"],
        },
        "provenance_test": {
            "exit_code": 0, "commands": ["pytest focused"], "passed": 1, "failed": 0,
        },
    }[evidence_type]


def test_evidence_is_retained_only_for_exact_run_criterion_and_config(tmp_path):
    composition, program, store, contract, intent = _fixture(tmp_path)
    criterion = contract.completion_criteria[0]
    invalid = [
        _evidence(intent, criterion, name, _value(name), run_id="run-other")
        for name in criterion.required_evidence
    ]

    rejected = composition.evaluate_criterion(
        intent.run_id, criterion_id=criterion.criterion_id, results=invalid
    )

    assert rejected["criterion_satisfied"] is False
    assert program.snapshot.evidence_store == {}
    assert store.get(intent.run_id).control.current_state == LocalLLMDayState.PREFLIGHT

    valid = [
        _evidence(intent, criterion, name, _value(name))
        for name in criterion.required_evidence
    ]
    accepted = composition.evaluate_criterion(
        intent.run_id, criterion_id=criterion.criterion_id, results=valid
    )
    assert accepted["criterion_satisfied"] is True
    assert set(criterion.evidence_record_ids) == set(criterion.required_evidence)
    assert all(item.run_id == intent.run_id for item in program.snapshot.evidence_store.values())


def test_complete_day_state_cannot_project_without_all_validator_evidence(tmp_path):
    composition, program, store, _contract, intent = _fixture(tmp_path)
    program.snapshot.state = LocalLLMDayState.COMPLETE
    before = store.get(intent.run_id)

    result = composition.project_day_state(intent.run_id)

    assert result["reason_code"] == "VALIDATOR_EVIDENCE_INCOMPLETE"
    assert store.get(intent.run_id) == before


def test_day_projection_rejects_noncurrent_and_mismatched_snapshot_run_without_mutation(tmp_path):
    composition, program, store, contract, intent = _fixture(tmp_path)
    newer_intent = intent.model_copy(update={
        "run_id": "run-ri01-newer",
        "go_at": intent.go_at + timedelta(seconds=1),
    })
    newer = RunRecord(
        intent=newer_intent,
        control=RunControl(
            run_id=newer_intent.run_id,
            selected_day=newer_intent.selected_day,
            contract_fingerprint=newer_intent.contract_fingerprint,
            current_state=LocalLLMDayState.PREFLIGHT,
            next_action="Current same-Day run.",
            updated_at=NOW + timedelta(seconds=1),
        ),
    )
    store.create(newer)
    old_before = store.get(intent.run_id)
    current_before = store.get(newer_intent.run_id)

    historical = composition.project_day_state(intent.run_id)

    assert historical["reason_code"] == "RUN_NOT_CURRENT"
    assert store.get(intent.run_id) == old_before
    assert store.get(newer_intent.run_id) == current_before

    program.snapshot.run_id = intent.run_id
    mismatch = composition.project_day_state(newer_intent.run_id)

    assert mismatch["reason_code"] == "DAY_SNAPSHOT_RUN_ID_MISMATCH"
    assert store.get(intent.run_id) == old_before
    assert store.get(newer_intent.run_id) == current_before


def test_repair_attempts_persist_same_run_and_exhaustion_does_not_mutate_again(tmp_path):
    composition, _program, store, _contract, intent = _fixture(tmp_path)
    composition.begin_repair(intent.run_id, allowed_paths={"src/temporal.py"})
    base = {
        "run_id": intent.run_id, "selected_day": 6,
        "failure_fingerprint": "failure-0001", "action_fingerprint": "action-00001",
        "changed_paths": ["src/temporal.py"], "git_fingerprint": intent.git_fingerprint,
        "active_work_seconds": 60, "verification_passed": False,
    }

    composition.record_repair_attempt(intent.run_id, base)
    second = composition.record_repair_attempt(
        intent.run_id, {**base, "action_fingerprint": "action-00002"}
    )
    waiting = store.get(intent.run_id)
    third = composition.record_repair_attempt(
        intent.run_id, {**base, "action_fingerprint": "action-00003"}
    )

    assert second["status"] == "HUMAN_ACTION_REQUIRED"
    assert waiting.intent.run_id == intent.run_id
    assert waiting.control.current_state == LocalLLMDayState.HUMAN_ACTION_REQUIRED
    assert waiting.control.resume_target == "PREFLIGHT"
    assert third["reason_code"] == "ATTEMPT_LIMIT_EXHAUSTED"
    assert store.get(intent.run_id) == waiting


def test_stale_review_and_absent_effect_keep_same_run_waiting(tmp_path):
    composition, _program, store, _contract, intent = _fixture(tmp_path)
    composition.request_review(intent.run_id, "REPORT-001", at=NOW)
    waiting = store.get(intent.run_id)

    stale = composition.apply_review_response(
        intent.run_id,
        {"response_id": "RESP-OLD", "in_reply_to": "REPORT-OLD", "result": "CONTINUE"},
        comment_id="COMMENT-OLD", at=NOW + timedelta(seconds=1), exit_code=0,
        envelope_valid=True, envelope_validation_reason="valid",
        downstream_effect_id="EFFECT-OLD", observed_effect_id="EFFECT-OLD",
    )
    absent = composition.apply_review_response(
        intent.run_id,
        {"response_id": "RESP-001", "in_reply_to": "REPORT-001", "result": "CONTINUE"},
        comment_id="COMMENT-001", at=NOW + timedelta(seconds=2), exit_code=0,
        envelope_valid=True, envelope_validation_reason="valid",
        downstream_effect_id=None, observed_effect_id=None,
    )

    assert stale["reason_code"] == "IN_REPLY_TO_MISMATCH"
    assert absent["continuation"]["reason_code"] == "DOWNSTREAM_EFFECT_NOT_OBSERVED"
    assert store.get(intent.run_id) == waiting


def test_only_matching_review_with_read_back_effect_returns_same_run_to_preflight(tmp_path):
    composition, _program, store, _contract, intent = _fixture(tmp_path)
    composition.request_review(intent.run_id, "REPORT-001", at=NOW)

    result = composition.apply_review_response(
        intent.run_id,
        {"response_id": "RESP-001", "in_reply_to": "REPORT-001", "result": "CONTINUE"},
        comment_id="COMMENT-001", at=NOW + timedelta(seconds=1), exit_code=0,
        envelope_valid=True, envelope_validation_reason="schema and identity valid",
        downstream_effect_id="EFFECT-001", observed_effect_id="EFFECT-001",
    )
    resumed = store.get(intent.run_id)
    duplicate = composition.apply_review_response(
        intent.run_id,
        {"response_id": "RESP-001", "in_reply_to": "REPORT-001", "result": "CONTINUE"},
        comment_id="COMMENT-001", at=NOW + timedelta(seconds=2), exit_code=0,
        envelope_valid=True, envelope_validation_reason="valid",
        downstream_effect_id="EFFECT-002", observed_effect_id="EFFECT-002",
    )

    assert result["review"]["state"] == "VERIFIED"
    assert resumed.intent.run_id == intent.run_id
    assert resumed.control.current_state == LocalLLMDayState.PREFLIGHT
    assert duplicate["reason_code"] == "DUPLICATE_RESPONSE"
    assert store.get(intent.run_id) == resumed


def test_human_decision_is_bound_to_one_run_and_mismatch_has_no_effect(tmp_path):
    composition, _program, store, _contract, intent = _fixture(tmp_path)
    request = DecisionRequest(
        decision_id="DECISION-001", revision=1,
        subject_type=SubjectType.EXECUTION_AUTHORITY,
        decision_subject="Resume the same run", target_commit="a" * 40,
        requested_effect="RETURN_TO_PREFLIGHT",
    )
    composition.bind_human_decision(intent.run_id, request)
    waiting = store.get(intent.run_id)
    response = HumanResponse(
        exact_text="承認します", decider="広瀬剛", channel="Codex Work chat",
        message_id="MSG-001", source_class="RECORDED_DIRECT_CONVERSATION",
        received_at=NOW + timedelta(seconds=1), decision_id="DECISION-OTHER",
        revision=1, subject_type=SubjectType.EXECUTION_AUTHORITY,
        target_commit="a" * 40, decision_effect="RETURN_TO_PREFLIGHT",
        subject_basis="The named decision request",
    )

    result = composition.receive_human_decision(intent.run_id, response)

    assert result["state"] == "HUMAN_RESPONSE_UNCLASSIFIED"
    assert result["reason_code"] == "DECISION_SUBJECT_NOT_BOUND"
    assert store.get(intent.run_id) == waiting
    assert waiting.control.current_state == LocalLLMDayState.HUMAN_ACTION_REQUIRED


def test_confirmed_human_effect_returns_only_bound_run_to_preflight(tmp_path):
    composition, _program, store, _contract, intent = _fixture(tmp_path)
    request = DecisionRequest(
        decision_id="DECISION-001", revision=1,
        subject_type=SubjectType.EXECUTION_AUTHORITY,
        decision_subject="Resume the same run", target_commit="a" * 40,
        requested_effect="RETURN_TO_PREFLIGHT",
    )
    composition.bind_human_decision(intent.run_id, request)
    received = composition.receive_human_decision(
        intent.run_id,
        HumanResponse(
            exact_text="承認します", decider="広瀬剛", channel="Codex Work chat",
            message_id="MSG-001", source_class="RECORDED_DIRECT_CONVERSATION",
            received_at=NOW + timedelta(seconds=1), decision_id="DECISION-001",
            revision=1, subject_type=SubjectType.EXECUTION_AUTHORITY,
            target_commit="a" * 40, decision_effect="RETURN_TO_PREFLIGHT",
            subject_basis="The named decision request",
        ),
    )
    composition.build_human_confirmation(
        intent.run_id, received["record_id"],
        confirmation_report_id="CONFIRM-001", confirms_report_id="REPORT-001",
        confirms_response_id="RESP-001", authority_record="AUTH-001",
    )

    result = composition.apply_human_confirmation(
        intent.run_id,
        received["record_id"],
        {
            "RESPONSE_ID": "CONFIRM-RESP-001", "IN_REPLY_TO": "CONFIRM-001",
            "CONFIRMS_REPORT_ID": "REPORT-001", "CONFIRMS_RESPONSE_ID": "RESP-001",
            "DECISION_ID": "DECISION-001", "DECISION_REVISION": 1,
            "REVIEWED_COMMIT": "a" * 40, "SUBJECT_TYPE": "EXECUTION_AUTHORITY",
            "DECISION_EFFECT": "RETURN_TO_PREFLIGHT", "RESULT": "CONTINUE",
        },
        continuation_succeeded=True,
        effect_evidence_id="EFFECT-001",
    )

    assert result["effect_applied"] is True
    assert result["run_id"] == intent.run_id
    assert store.get(intent.run_id).control.current_state == LocalLLMDayState.PREFLIGHT
    assert store.get(intent.run_id).control.resume_target is None
