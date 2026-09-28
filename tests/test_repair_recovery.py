from datetime import datetime, timezone

from backend.control.repair_recovery import RepairRecoveryController
from backend.models.local_llm_day import LocalLLMDayState, RunControl, RunIntent, RunLimits, RunRecord


def _record():
    now = datetime.now(timezone.utc)
    intent = RunIntent(
        run_id="run-wc06-fixture", selected_day=6, go_at=now,
        contract_fingerprint="contract-v1", policy_fingerprint="policy-v1",
        config_fingerprint="config-v1", git_fingerprint="git-base-v1",
        requested_limits=RunLimits(active_work_seconds=1800, max_attempts=2, max_cost=0, currency="JPY"),
    )
    control = RunControl(
        run_id=intent.run_id, selected_day=6, contract_fingerprint=intent.contract_fingerprint,
        current_state=LocalLLMDayState.DIAGNOSING_GAP, next_action="Repair one bounded gap",
        updated_at=now,
    )
    return RunRecord(intent=intent, control=control)


def _attempt(**updates):
    value = {
        "run_id": "run-wc06-fixture", "selected_day": 6,
        "failure_fingerprint": "failure-0001", "action_fingerprint": "action-00001",
        "changed_paths": ["src/temporal.py"], "git_fingerprint": "git-base-v1",
        "active_work_seconds": 60, "verification_passed": False,
    }
    value.update(updates)
    return value


def test_scope_git_and_budget_guards_reject_without_consuming_attempt():
    controller = RepairRecoveryController(_record(), allowed_paths={"src/temporal.py"})

    assert controller.record_attempt(_attempt(changed_paths=["outside.txt"]))["reason_code"] == "REPAIR_SCOPE_REJECTED"
    assert controller.record_attempt(_attempt(git_fingerprint="git-other"))["reason_code"] == "GIT_FINGERPRINT_MISMATCH"
    result = controller.record_attempt(_attempt(active_work_seconds=1801))

    assert result["reason_code"] == "ACTIVE_WORK_BUDGET_EXCEEDED"
    assert result["attempt_count"] == 0
    assert result["control"]["current_state"] == "DIAGNOSING_GAP"


def test_verified_bounded_repair_enters_deterministic_revalidation_only():
    controller = RepairRecoveryController(_record(), allowed_paths={"src/temporal.py"})

    result = controller.record_attempt(_attempt(verification_passed=True))

    assert result["status"] == "REVALIDATING"
    assert result["control"]["current_state"] == "REVALIDATING"
    assert result["repair_executed"] is False
    assert result["day_execution_started"] is False


def test_same_failure_twice_requires_human_and_forbids_third_attempt():
    controller = RepairRecoveryController(_record(), allowed_paths={"src/temporal.py"})

    first = controller.record_attempt(_attempt())
    second = controller.record_attempt(_attempt(action_fingerprint="action-00002"))
    third = controller.record_attempt(_attempt(action_fingerprint="action-00003"))

    assert first["status"] == "DIAGNOSING_GAP"
    assert second["status"] == "HUMAN_ACTION_REQUIRED"
    assert second["control"]["resume_target"] == "PREFLIGHT"
    assert second["review_request_id"]
    assert third["reason_code"] == "ATTEMPT_LIMIT_EXHAUSTED"
    assert third["attempt_count"] == 2


def test_only_matching_review_returns_same_run_and_day_to_preflight():
    controller = RepairRecoveryController(_record(), allowed_paths={"src/temporal.py"})
    controller.record_attempt(_attempt())
    waiting = controller.record_attempt(_attempt(action_fingerprint="action-00002"))
    request_id = waiting["review_request_id"]

    mismatch = controller.apply_review({
        "request_id": request_id, "run_id": "run-other", "selected_day": 6,
        "failure_fingerprint": "failure-0001", "result": "RECHECK",
    })
    assert mismatch["reason_code"] == "REVIEW_CORRELATION_MISMATCH"
    assert mismatch["control"]["current_state"] == "HUMAN_ACTION_REQUIRED"

    resumed = controller.apply_review({
        "request_id": request_id, "run_id": "run-wc06-fixture", "selected_day": 6,
        "failure_fingerprint": "failure-0001", "result": "RECHECK",
    })
    assert resumed["status"] == "PREFLIGHT"
    assert resumed["run_id"] == "run-wc06-fixture"
    assert resumed["selected_day"] == 6
    assert resumed["attempt_count"] == 2
    assert resumed["control"]["blocker"] is None
    assert resumed["control"]["resume_target"] is None
    assert resumed["day_execution_started"] is False

    exhausted = controller.record_attempt(_attempt(action_fingerprint="action-00003"))
    assert exhausted["reason_code"] == "ATTEMPT_LIMIT_EXHAUSTED"
