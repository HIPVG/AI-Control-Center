from datetime import datetime, timedelta, timezone
from pathlib import Path
import shutil
import subprocess

from backend.control.local_llm_day_program import LocalLLMDayProgram
from backend.control.run_composition import RunCoordinator, RunPreflightFacts
from backend.control.run_store import JsonRunStore
from backend.models.local_llm_day import LocalLLMDayState


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "day-contract"


def _git(root: Path, *args: str) -> None:
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def _repository(tmp_path: Path) -> Path:
    root = tmp_path / "repository"
    shutil.copytree(FIXTURE_ROOT, root)
    _git(tmp_path, "init", "-b", "main", str(root))
    _git(root, "config", "user.name", "Fixture")
    _git(root, "config", "user.email", "fixture@example.invalid")
    _git(root, "add", ".")
    _git(root, "commit", "-m", "fixture baseline")
    return root


def test_admissible_go_persists_before_one_same_identity_effect(tmp_path):
    root = _repository(tmp_path)
    store = JsonRunStore(tmp_path / "runs")
    calls = []

    def execute(run_id: str, day: int):
        persisted = store.get(run_id)
        assert persisted is not None
        assert persisted.intent.selected_day == day
        calls.append((run_id, day))
        return {"run_id": run_id, "result": "INJECTED_ONLY"}

    coordinator = RunCoordinator(
        LocalLLMDayProgram(root), store,
        preflight_resolver=lambda _day: RunPreflightFacts(True, True),
        executor=execute,
    )

    result = coordinator.go(6)

    assert result["record_persisted"] is True
    assert result["execution_started"] is True
    assert result["run_id"] == result["execution"]["run_id"] == calls[0][0]
    assert calls == [(result["run_id"], 6)]
    assert store.current().control.current_state == LocalLLMDayState.PREFLIGHT


def test_blocked_go_persists_reason_and_starts_no_effect(tmp_path):
    root = _repository(tmp_path)
    store = JsonRunStore(tmp_path / "runs")
    calls = []
    coordinator = RunCoordinator(
        LocalLLMDayProgram(root), store,
        preflight_resolver=lambda _day: RunPreflightFacts(None, True),
        executor=lambda run_id, day: calls.append((run_id, day)),
    )

    result = coordinator.go(6)
    restored = JsonRunStore(tmp_path / "runs").get(result["run_id"])

    assert result["execution_started"] is False
    assert calls == []
    assert restored.control.current_state == LocalLLMDayState.HUMAN_ACTION_REQUIRED
    assert restored.control.blocker == "EFFECTIVE_PERMISSION_UNKNOWN"
    assert restored.control.resume_target == "PREFLIGHT"


def test_duplicate_go_and_legacy_start_share_one_guard_and_one_effect(tmp_path):
    root = _repository(tmp_path)
    store = JsonRunStore(tmp_path / "runs")
    calls = []
    coordinator = RunCoordinator(
        LocalLLMDayProgram(root), store,
        preflight_resolver=lambda _day: RunPreflightFacts(True, True),
        executor=lambda run_id, day: calls.append((run_id, day)) or {"run_id": run_id},
    )

    first = coordinator.legacy_start(6)
    duplicate = coordinator.go(6)

    assert first["source"] == "legacy_direct_start"
    assert duplicate["error_code"] == "RUN_ALREADY_ACTIVE"
    assert duplicate["run_id"] == first["run_id"]
    assert duplicate["execution_started"] is False
    assert calls == [(first["run_id"], 6)]
    assert len(store.records()) == 1


def test_versioned_update_preserves_history_and_rejects_stale_update(tmp_path):
    root = _repository(tmp_path)
    store = JsonRunStore(tmp_path / "runs")
    coordinator = RunCoordinator(
        LocalLLMDayProgram(root), store,
        preflight_resolver=lambda _day: RunPreflightFacts(None, True),
        executor=lambda _run_id, _day: {},
    )
    result = coordinator.go(6)
    original = store.get(result["run_id"])
    updated_control = original.control.model_copy(update={
        "current_state": LocalLLMDayState.PREFLIGHT,
        "state_history": original.control.state_history + (original.control.current_state,),
        "next_action": "Re-evaluate the same run",
        "blocker": None,
        "resume_target": None,
        "updated_at": original.control.updated_at + timedelta(seconds=1),
    })
    updated = original.model_copy(update={"control": updated_control})

    store.update(updated, expected_updated_at=original.control.updated_at)

    assert JsonRunStore(tmp_path / "runs").get(result["run_id"]) == updated
    assert JsonRunStore(tmp_path / "runs").versions(result["run_id"]) == (original, updated)
    try:
        store.update(updated, expected_updated_at=original.control.updated_at)
    except ValueError as exc:
        assert str(exc) == "Stale run update"
    else:
        raise AssertionError("stale update was accepted")


def test_executor_identity_mismatch_is_fail_closed_and_keeps_persisted_run(tmp_path):
    root = _repository(tmp_path)
    store = JsonRunStore(tmp_path / "runs")
    coordinator = RunCoordinator(
        LocalLLMDayProgram(root), store,
        preflight_resolver=lambda _day: RunPreflightFacts(True, True),
        executor=lambda _run_id, _day: {"run_id": "other-run"},
    )

    result = coordinator.go(6)

    assert result["error_code"] == "EXECUTOR_RUN_ID_MISMATCH"
    assert result["execution_started"] is True
    assert store.get(result["run_id"]).control.current_state == LocalLLMDayState.PREFLIGHT
