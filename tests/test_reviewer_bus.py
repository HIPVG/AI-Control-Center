import json
import subprocess
from pathlib import Path

from backend.control.reviewer_bus import ReviewerBusWatcher


def _comment(comment_id: int, body: str) -> dict[str, object]:
    return {"id": comment_id, "body": body, "created_at": "2026-09-24T00:00:00Z"}


def _gh_output(comments: list[dict[str, object]]) -> str:
    return "\n".join(json.dumps(item) for item in comments)


def test_matching_response_starts_one_fresh_codex_continuation(tmp_path: Path, monkeypatch):
    comments = [
        _comment(10, "REPORT_ID: R1\nREPORT_TYPE: PROGRESS_UPDATE"),
        _comment(11, "IN_REPLY_TO: R1\nRESULT: CONTINUE\nNEXT_ACTION: keep going"),
    ]
    calls: list[list[str]] = []

    def runner(argv, **kwargs):
        calls.append(argv)
        if "api" in argv:
            return subprocess.CompletedProcess(argv, 0, _gh_output(comments), "")
        assert argv[1:5] == ["exec", "--sandbox", "workspace-write", "--json"]
        assert "resume" not in argv[1:-1]
        assert "--last" not in argv
        assert "fresh continuation turn" in argv[-1]
        assert "IN_REPLY_TO: R1" in argv[-1]
        assert "END THIS CODEX TURN" in argv[-1]
        assert kwargs["env"]["CODEX_SQLITE_HOME"] == str((tmp_path / "state" / "codex-sqlite").resolve())
        return subprocess.CompletedProcess(argv, 0, "", "")

    watcher = ReviewerBusWatcher(tmp_path, codex_executable="codex", command_runner=runner)
    monkeypatch.setattr(watcher, "_resolve_executable", lambda value: value)

    first = watcher.run_once()
    second = watcher.run_once()

    codex_calls = [call for call in calls if call and call[0] == "codex"]
    assert len(codex_calls) == 1
    assert first["last_report_id"] == "R1"
    assert first["last_applied_response_comment_id"] == 11
    assert first["last_continuation_at"]
    assert second["last_applied_response_comment_id"] == 11


def test_mismatched_response_is_ignored(tmp_path: Path, monkeypatch):
    comments = [
        _comment(20, "REPORT_ID: R2\nREPORT_TYPE: DECISION_REQUEST"),
        _comment(21, "IN_REPLY_TO: OLD\nRESULT: DECISION"),
    ]
    calls: list[list[str]] = []

    def runner(argv, **kwargs):
        calls.append(argv)
        return subprocess.CompletedProcess(argv, 0, _gh_output(comments), "")

    watcher = ReviewerBusWatcher(tmp_path, codex_executable="codex", command_runner=runner)
    monkeypatch.setattr(watcher, "_resolve_executable", lambda value: value)

    result = watcher.run_once()

    assert result.get("last_applied_response_comment_id") is None
    assert all(call[0] != "codex" for call in calls)


def test_only_latest_outstanding_report_can_resume(tmp_path: Path, monkeypatch):
    comments = [
        _comment(30, "REPORT_ID: OLD\nREPORT_TYPE: PROGRESS_UPDATE"),
        _comment(31, "IN_REPLY_TO: OLD\nRESULT: CONTINUE"),
        _comment(32, "REPORT_ID: NEW\nREPORT_TYPE: COMPLETION_REPORT"),
    ]
    calls: list[list[str]] = []

    def runner(argv, **kwargs):
        calls.append(argv)
        return subprocess.CompletedProcess(argv, 0, _gh_output(comments), "")

    watcher = ReviewerBusWatcher(tmp_path, codex_executable="codex", command_runner=runner)
    monkeypatch.setattr(watcher, "_resolve_executable", lambda value: value)

    watcher.run_once()

    assert all(call[0] != "codex" for call in calls)


def test_failed_continuation_is_not_marked_applied_and_will_retry(tmp_path: Path, monkeypatch):
    comments = [
        _comment(40, "REPORT_ID: R4\nREPORT_TYPE: PROGRESS_UPDATE"),
        _comment(41, "IN_REPLY_TO: R4\nRESULT: CONTINUE"),
    ]
    codex_attempts = 0

    def runner(argv, **kwargs):
        nonlocal codex_attempts
        if "api" in argv:
            return subprocess.CompletedProcess(argv, 0, _gh_output(comments), "")
        codex_attempts += 1
        return subprocess.CompletedProcess(argv, 1 if codex_attempts == 1 else 0, "", "failed")

    watcher = ReviewerBusWatcher(tmp_path, codex_executable="codex", command_runner=runner)
    monkeypatch.setattr(watcher, "_resolve_executable", lambda value: value)

    failed = watcher.run_once()
    succeeded = watcher.run_once()

    assert failed["last_error"] == "CODEX_CONTINUATION_FAILED"
    assert failed.get("last_applied_response_comment_id") is None
    assert succeeded["last_applied_response_comment_id"] == 41
    assert codex_attempts == 2


def test_loop_does_not_add_full_poll_delay_after_long_continuation(tmp_path: Path, monkeypatch):
    watcher = ReviewerBusWatcher(tmp_path, poll_seconds=120)
    timeline = iter([0.0, 150.0])
    monkeypatch.setattr("backend.control.reviewer_bus.monotonic", lambda: next(timeline))

    class StopOnce:
        def __init__(self):
            self.checks = 0
            self.waits: list[float] = []

        def is_set(self):
            self.checks += 1
            return self.checks > 1

        def wait(self, timeout):
            self.waits.append(timeout)

    stop = StopOnce()
    watcher._stop = stop
    watcher.run_once = lambda: {}

    watcher._loop()

    assert stop.waits == [0.0]
