import json
import subprocess
from pathlib import Path

from backend.control.reviewer_bus import ReviewerBusWatcher


def _comment(comment_id: int, body: str) -> dict[str, object]:
    return {"id": comment_id, "body": body, "created_at": "2026-09-24T00:00:00Z"}


def _comments_output(comments: list[dict[str, object]]) -> str:
    return "\n".join(json.dumps(item) for item in comments)


def _envelope(report_id="R1-NEXT"):
    body = f"REPORT_ID: {report_id}\nREPORT_TYPE: PROGRESS_UPDATE\nCURRENT_ACTION: bounded acknowledgement"
    return json.dumps({"action": "POST_REPORT", "report_id": report_id, "report_type": "PROGRESS_UPDATE", "body": body})


def _watcher(tmp_path, runner, monkeypatch):
    watcher = ReviewerBusWatcher(tmp_path, codex_executable="codex", command_runner=runner)
    monkeypatch.setattr(watcher, "_resolve_executable", lambda value: value)
    monkeypatch.setattr(watcher, "_set_state", lambda **changes: watcher._state.update(changes))
    return watcher


def test_matching_response_posts_envelope_and_sets_new_outstanding(tmp_path: Path, monkeypatch):
    comments = [_comment(10, "REPORT_ID: R1\nREPORT_TYPE: PROGRESS_UPDATE"), _comment(11, "IN_REPLY_TO: R1\nRESULT: CONTINUE")]
    calls = []

    def runner(argv, **kwargs):
        calls.append(argv)
        if argv[0] == "gh" and "--method" not in argv:
            return subprocess.CompletedProcess(argv, 0, _comments_output(comments), "")
        if argv[0] == "codex":
            assert "Do not access GitHub" in argv[-1]
            return subprocess.CompletedProcess(argv, 0, _envelope(), "")
        assert "--method" in argv
        return subprocess.CompletedProcess(argv, 0, json.dumps({"id": 12}), "")

    result = _watcher(tmp_path, runner, monkeypatch).run_once()

    assert result["last_applied_response_comment_id"] == 11
    assert result["outstanding_report_id"] == "R1-NEXT"
    assert result["last_delivery_comment_id"] == 12
    assert len([call for call in calls if call[0] == "codex"]) == 1
    assert len([call for call in calls if "--method" in call]) == 1


def test_exit_zero_without_payload_is_not_delivery_success(tmp_path: Path, monkeypatch):
    comments = [_comment(20, "REPORT_ID: R2\nREPORT_TYPE: PROGRESS_UPDATE"), _comment(21, "IN_REPLY_TO: R2\nRESULT: CONTINUE")]

    def runner(argv, **kwargs):
        if argv[0] == "gh":
            return subprocess.CompletedProcess(argv, 0, _comments_output(comments), "")
        return subprocess.CompletedProcess(argv, 0, "not an envelope", "")

    result = _watcher(tmp_path, runner, monkeypatch).run_once()

    assert result["last_codex_exit_code"] == 0
    assert result["last_error"] == "CODEX_CONTINUATION_OUTPUT_INVALID"
    assert result.get("last_applied_response_comment_id") is None
    assert result.get("last_delivery_comment_id") is None


def test_current_mismatch_posts_one_protocol_nack_without_continuation(tmp_path: Path, monkeypatch):
    comments = [_comment(30, "REPORT_ID: R3\nREPORT_TYPE: PROGRESS_UPDATE"), _comment(31, "IN_REPLY_TO: OTHER\nRESULT: CONTINUE")]
    posts = []
    calls = []

    def runner(argv, **kwargs):
        calls.append(argv)
        if "--method" not in argv:
            return subprocess.CompletedProcess(argv, 0, _comments_output(comments), "")
        posts.append(argv[-1])
        return subprocess.CompletedProcess(argv, 0, json.dumps({"id": 32}), "")

    watcher = _watcher(tmp_path, runner, monkeypatch)
    watcher.run_once()
    watcher.run_once()

    assert len(posts) == 1
    assert "PROTOCOL_NACK: yes" in posts[0]
    assert "REPORT_TYPE:" not in posts[0]
    assert all(call[0] != "codex" for call in calls)


def test_known_old_response_is_silently_ignored(tmp_path: Path, monkeypatch):
    comments = [_comment(40, "REPORT_ID: R4\nREPORT_TYPE: PROGRESS_UPDATE"), _comment(41, "IN_REPLY_TO: OLD\nRESULT: CONTINUE")]
    calls = []

    def runner(argv, **kwargs):
        calls.append(argv)
        return subprocess.CompletedProcess(argv, 0, _comments_output(comments), "")

    watcher = _watcher(tmp_path, runner, monkeypatch)
    watcher._state["processed_report_ids"] = ["OLD"]
    watcher.run_once()

    assert all("--method" not in call and call[0] != "codex" for call in calls)


def test_failed_continuation_keeps_response_pending_for_retry(tmp_path: Path, monkeypatch):
    comments = [_comment(50, "REPORT_ID: R5\nREPORT_TYPE: PROGRESS_UPDATE"), _comment(51, "IN_REPLY_TO: R5\nRESULT: CONTINUE")]
    attempts = 0

    def runner(argv, **kwargs):
        nonlocal attempts
        if argv[0] == "gh" and "--method" not in argv:
            return subprocess.CompletedProcess(argv, 0, _comments_output(comments), "")
        if argv[0] == "codex":
            attempts += 1
            return subprocess.CompletedProcess(argv, 1 if attempts == 1 else 0, _envelope(), "")
        return subprocess.CompletedProcess(argv, 0, json.dumps({"id": 52}), "")

    watcher = _watcher(tmp_path, runner, monkeypatch)
    failed = watcher.run_once()
    succeeded = watcher.run_once()

    assert failed["last_error"] == "CODEX_CONTINUATION_FAILED"
    assert failed["pending_response_comment_id"] == 51
    assert succeeded["last_applied_response_comment_id"] == 51
    assert attempts == 2


def test_loop_keeps_cadence_after_long_continuation(tmp_path: Path, monkeypatch):
    watcher = ReviewerBusWatcher(tmp_path, poll_seconds=120)
    timeline = iter([0.0, 150.0])
    monkeypatch.setattr("backend.control.reviewer_bus.monotonic", lambda: next(timeline))

    class StopOnce:
        def __init__(self):
            self.checks, self.waits = 0, []

        def is_set(self):
            self.checks += 1
            return self.checks > 1

        def wait(self, timeout):
            self.waits.append(timeout)

    watcher._stop = StopOnce()
    watcher.run_once = lambda: {}
    watcher._loop()
    assert watcher._stop.waits == [0.0]
