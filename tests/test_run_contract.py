from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from backend.control.run_store import JsonRunStore
from backend.models.local_llm_day import (
    LocalLLMDaySnapshot, LocalLLMDayState, RunControl, RunIntent, RunLimits, RunRecord,
)


def record():
    now = datetime.now(timezone.utc)
    intent = RunIntent(
        run_id="fixture-run-01", selected_day=1, go_at=now,
        contract_fingerprint="contract-v1", policy_fingerprint="policy-v1",
        config_fingerprint="config-v1", git_fingerprint="git-base-v1",
        requested_limits=RunLimits(active_work_seconds=1800, max_attempts=2,
                                   max_cost=0, currency="JPY"),
    )
    control = RunControl(
        run_id=intent.run_id, selected_day=1, contract_fingerprint="contract-v1",
        current_state=LocalLLMDayState.STOPPED,
        state_history=(LocalLLMDayState.PREFLIGHT,), next_action="Resolve blocker",
        blocker="Fixture authority missing", resume_target="PREFLIGHT", updated_at=now,
    )
    return RunRecord(intent=intent, control=control)


def test_versioned_json_restart_preserves_current_history_and_unknown(tmp_path):
    original = record()
    JsonRunStore(tmp_path).create(original)
    restored = JsonRunStore(tmp_path).get(original.intent.run_id)
    assert restored == original
    assert restored.schema_version == restored.intent.schema_version == 1
    assert restored.control.current_state == LocalLLMDayState.STOPPED
    assert restored.control.state_history == (LocalLLMDayState.PREFLIGHT,)
    assert restored.control.blocker == "Fixture authority missing"
    assert restored.control.resume_target == "PREFLIGHT"
    assert restored.intent.requested_limits.max_tokens is None
    assert restored.intent.requested_limits.max_cost == 0
    assert JsonRunStore(tmp_path).get("missing") is None


def test_duplicate_run_rejected_without_overwriting_original(tmp_path):
    original = record()
    store = JsonRunStore(tmp_path)
    store.create(original)
    before = list(tmp_path.glob("*.json"))[0].read_bytes()
    with pytest.raises(FileExistsError):
        JsonRunStore(tmp_path).create(original)
    assert list(tmp_path.glob("*.json"))[0].read_bytes() == before


@pytest.mark.parametrize("field,value", [
    ("run_id", "other-run"), ("selected_day", 2),
    ("contract_fingerprint", "different-contract"),
])
def test_mismatched_identity_rejected_before_persistence(tmp_path, field, value):
    original = record()
    bad = original.model_copy(update={
        "control": original.control.model_copy(update={field: value}),
    })
    with pytest.raises(ValidationError, match=field):
        JsonRunStore(tmp_path).create(bad)
    assert not list(tmp_path.iterdir())


def test_unknown_version_and_corrupt_json_fail_closed(tmp_path):
    store = JsonRunStore(tmp_path)
    original = record()
    store.create(original)
    path = list(tmp_path.glob("*.json"))[0]
    payload = original.model_dump(mode="json")
    payload["schema_version"] = 2
    with pytest.raises(ValidationError):
        RunRecord.model_validate(payload)
    path.write_text("{truncated", encoding="utf-8")
    with pytest.raises(ValidationError):
        store.get(original.intent.run_id)
    assert path.read_text(encoding="utf-8") == "{truncated"


def test_existing_snapshot_remains_compatible_and_intent_is_immutable():
    snapshot = LocalLLMDaySnapshot.model_validate({"selected_day": 1, "state": "PAUSED"})
    assert LocalLLMDaySnapshot.model_validate_json(snapshot.model_dump_json()) == snapshot
    with pytest.raises(ValidationError):
        record().intent.selected_day = 2
