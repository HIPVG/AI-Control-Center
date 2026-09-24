"""Deterministic GitHub reviewer-bus watcher and report transport."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import threading
from datetime import datetime, timezone
from pathlib import Path
from time import monotonic, sleep
from typing import Callable

REVIEW_REPO = "HIPVG/AI-Control-Center-Review-Bridge"
REVIEW_PR = 1
POLL_SECONDS = 120
REPORT_ID_RE = re.compile(r"(?m)^REPORT_ID:\s*([^\s]+)\s*$")
REPORT_TYPE_RE = re.compile(r"(?m)^REPORT_TYPE:\s*([^\s]+)\s*$")
IN_REPLY_TO_RE = re.compile(r"(?m)^IN_REPLY_TO:\s*([^\s]+)\s*$")
REPORT_TYPES = {"PROGRESS_UPDATE", "DECISION_REQUEST", "COMPLETION_REPORT"}
POST_ACTION = "POST_REPORT"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ReviewerBusWatcher:
    """Own reviewer response polling, Codex continuation, and PR publication."""

    def __init__(self, project_root: Path, codex_executable: str = "codex", *, gh_executable: str = "gh", poll_seconds: int = POLL_SECONDS, command_runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run) -> None:
        self.project_root = project_root.resolve()
        self.codex_executable = codex_executable
        self.gh_executable = gh_executable
        self.poll_seconds = max(10, int(poll_seconds))
        self.command_runner = command_runner
        self.state_path = self.project_root / "state" / "reviewer-bus-watcher.json"
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self._state = self._load_state()

    def available(self) -> bool:
        return self._resolve_executable(self.codex_executable) is not None and self._resolve_executable(self.gh_executable) is not None

    def start(self) -> bool:
        if os.environ.get("PYTEST_CURRENT_TEST"):
            return False
        if os.environ.get("AI_CONTROL_CENTER_DISABLE_REVIEWER_BUS") == "1":
            self._set_state(running=False, available=False, last_error="DISABLED_BY_ENV")
            return False
        if not self.available():
            self._set_state(running=False, available=False, last_error="REVIEWER_BUS_PREREQUISITE_MISSING")
            return False
        if self._thread and self._thread.is_alive():
            return True
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, name="reviewer-bus-watcher", daemon=True)
        self._thread.start()
        self._set_state(running=True, available=True, last_error=None)
        return True

    def stop(self) -> None:
        self._stop.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3)
        self._set_state(running=False)

    def status(self) -> dict[str, object]:
        with self._lock:
            return dict(self._state)

    def run_once(self) -> dict[str, object]:
        comments, error = self._fetch_comments()
        self._set_state(last_poll_at=_utc_now())
        if error:
            self._set_state(last_error=error)
            return self.status()

        report = self._current_report(comments)
        if report is None:
            self._set_state(last_error=None)
            return self.status()
        report_id = self._extract(REPORT_ID_RE, str(report.get("body", "")))
        if not report_id:
            self._set_state(last_error="REPORT_ID_MISSING")
            return self.status()

        response = self._pending_or_matching_response(comments, report, report_id)
        if response is None:
            self._nack_unknown_mismatches(comments, report, report_id)
            return self.status()

        response_id = int(response["id"])
        response_body = str(response.get("body", ""))
        self._set_state(last_report_id=report_id, last_response_comment_id=response_id, pending_response_comment_id=response_id, pending_response_body=response_body, pending_response_report_id=report_id, outstanding_report_id=None, last_error=None)
        completed = self._continue_codex(self._resume_prompt(report_id, response_body))
        self._set_state(last_continuation_at=_utc_now(), last_codex_exit_code=completed.returncode)
        if completed.returncode != 0:
            self._set_state(last_error="CODEX_CONTINUATION_FAILED")
            return self.status()

        envelope = self._extract_envelope(completed.stdout)
        if envelope is None:
            self._set_state(last_error="CODEX_CONTINUATION_OUTPUT_INVALID")
            return self.status()
        if envelope.get("action") != POST_ACTION:
            if envelope.get("action") in {"NO_REPORT", "HUMAN_REQUIRED"}:
                self._mark_response_applied(response_id, report_id)
                return self.status()
            self._set_state(last_error="CODEX_CONTINUATION_OUTPUT_INVALID")
            return self.status()

        report_body = self._validated_report_body(envelope)
        if report_body is None:
            self._set_state(last_error="CODEX_CONTINUATION_OUTPUT_INVALID")
            return self.status()
        posted_id = self._post_comment(report_body)
        if posted_id is None:
            self._set_state(last_error="GITHUB_REPORT_DELIVERY_FAILED")
            return self.status()

        new_report_id = str(envelope["report_id"])
        self._mark_response_applied(response_id, report_id, outstanding_report_id=new_report_id, outstanding_report_comment_id=posted_id, last_report_id=new_report_id, last_delivery_comment_id=posted_id, last_delivery_at=_utc_now())
        return self.status()

    def _loop(self) -> None:
        while not self._stop.is_set():
            cycle_started = monotonic()
            self.run_once()
            self._stop.wait(max(0.0, self.poll_seconds - (monotonic() - cycle_started)))

    def _fetch_comments(self) -> tuple[list[dict[str, object]], str | None]:
        gh = self._resolve_executable(self.gh_executable) or self.gh_executable
        argv = [gh, "api", f"repos/{REVIEW_REPO}/issues/{REVIEW_PR}/comments?per_page=100", "--paginate", "--jq", ".[] | {id: .id, body: .body, created_at: .created_at}"]
        try:
            completed = self.command_runner(argv, cwd=self.project_root, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30, check=False, shell=False)
        except (OSError, subprocess.TimeoutExpired):
            return [], "GITHUB_COMMENT_FETCH_FAILED"
        if completed.returncode != 0:
            return [], "GITHUB_COMMENT_FETCH_FAILED"
        comments: list[dict[str, object]] = []
        for line in completed.stdout.splitlines():
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                return [], "GITHUB_COMMENT_OUTPUT_INVALID"
            if isinstance(value, dict) and isinstance(value.get("id"), int) and isinstance(value.get("body"), str):
                comments.append(value)
        comments.sort(key=lambda item: int(item["id"]))
        return comments, None

    def _current_report(self, comments: list[dict[str, object]]) -> dict[str, object] | None:
        reports = [item for item in comments if self._extract(REPORT_ID_RE, str(item.get("body", ""))) and self._extract(REPORT_TYPE_RE, str(item.get("body", "")))]
        if not reports:
            return None
        expected = self._state.get("outstanding_report_id")
        if isinstance(expected, str):
            return next((item for item in reversed(reports) if self._extract(REPORT_ID_RE, str(item["body"])) == expected), None)
        return max(reports, key=lambda item: int(item["id"]))

    def _pending_or_matching_response(self, comments: list[dict[str, object]], report: dict[str, object], report_id: str) -> dict[str, object] | None:
        pending_id = int(self._state.get("pending_response_comment_id", 0) or 0)
        if pending_id:
            return next((item for item in comments if int(item["id"]) == pending_id), None)
        report_comment_id = int(report["id"])
        last_applied = int(self._state.get("last_applied_response_comment_id", 0) or 0)
        matching = [item for item in comments if int(item["id"]) > report_comment_id and int(item["id"]) > last_applied and self._extract(IN_REPLY_TO_RE, str(item.get("body", ""))) == report_id]
        return min(matching, key=lambda item: int(item["id"])) if matching else None

    def _nack_unknown_mismatches(self, comments: list[dict[str, object]], report: dict[str, object], expected: str) -> None:
        known_reports = set(self._state.get("processed_report_ids", []))
        nacked = {int(value) for value in self._state.get("protocol_nack_response_comment_ids", [])}
        for item in comments:
            response_id = int(item["id"])
            received = self._extract(IN_REPLY_TO_RE, str(item.get("body", "")))
            if response_id <= int(report["id"]) or not received or received == expected or received in known_reports or response_id in nacked:
                continue
            body = "\n".join(["PROTOCOL_NACK: yes", f"EXPECTED_REPORT_ID: {expected}", f"RECEIVED_IN_REPLY_TO: {received}", "RESULT: IGNORED", "REASON: response_id_mismatch"])
            if self._post_comment(body) is not None:
                nacked.add(response_id)
                self._set_state(protocol_nack_response_comment_ids=sorted(nacked), last_error=None)
            else:
                self._set_state(last_error="GITHUB_REPORT_DELIVERY_FAILED")
            return

    def _post_comment(self, body: str) -> int | None:
        gh = self._resolve_executable(self.gh_executable) or self.gh_executable
        argv = [gh, "api", "--method", "POST", f"repos/{REVIEW_REPO}/issues/{REVIEW_PR}/comments", "-f", f"body={body}"]
        try:
            completed = self.command_runner(argv, cwd=self.project_root, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30, check=False, shell=False)
        except (OSError, subprocess.TimeoutExpired):
            return None
        if completed.returncode != 0:
            return None
        try:
            result = json.loads(completed.stdout)
        except json.JSONDecodeError:
            return None
        return int(result["id"]) if isinstance(result, dict) and isinstance(result.get("id"), int) else None

    def _continue_codex(self, prompt: str) -> subprocess.CompletedProcess[str]:
        codex = self._resolve_executable(self.codex_executable) or self.codex_executable
        codex_sqlite_home = (self.project_root / "state" / "codex-sqlite").resolve()
        codex_sqlite_home.mkdir(parents=True, exist_ok=True)
        environment = os.environ.copy()
        if not environment.get("HOME") and environment.get("USERPROFILE"):
            environment["HOME"] = environment["USERPROFILE"]
        environment["CODEX_SQLITE_HOME"] = str(codex_sqlite_home)
        try:
            return self.command_runner([codex, "exec", "--sandbox", "workspace-write", "--json", prompt], cwd=self.project_root, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900, check=False, shell=False, stdin=subprocess.DEVNULL, env=environment)
        except (OSError, subprocess.TimeoutExpired):
            return subprocess.CompletedProcess([codex], 1, "", "continuation failed")

    @staticmethod
    def _resume_prompt(report_id: str, response_body: str) -> str:
        return (
            "A matching ChatGPT reviewer response arrived on the operational GitHub reviewer bus.\n"
            f"REPORT_ID: {report_id}\n"
            "This is a fresh continuation turn, not a resumed desktop/CLI thread. Reconstruct authoritative context from AGENTS.md, docs/WORKING_RULES.md, docs/CURRENT_WORK.md, relevant engineering history, persisted Day state, and the active plan/runbook before acting. Apply the complete reviewer response and use the minimum sufficient action. Do not access GitHub or publish a report yourself. End with exactly one JSON object: {\"action\":\"POST_REPORT\"|\"NO_REPORT\"|\"HUMAN_REQUIRED\",\"report_id\":\"...\",\"report_type\":\"PROGRESS_UPDATE\"|\"DECISION_REQUEST\"|\"COMPLETION_REPORT\",\"body\":\"...\"}. For POST_REPORT, body must be the complete report and report_id/report_type must match its fields. The watcher owns GitHub delivery.\n\n"
            "REVIEWER_RESPONSE:\n"
            f"{response_body.strip()}\n"
        )

    @staticmethod
    def _extract_envelope(output: str) -> dict[str, object] | None:
        candidates = [output.strip()]
        for line in output.splitlines():
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                continue
            candidates.extend(ReviewerBusWatcher._json_strings(value))
        for candidate in reversed(candidates):
            try:
                value = json.loads(candidate)
            except json.JSONDecodeError:
                continue
            if isinstance(value, dict) and isinstance(value.get("action"), str):
                return value
        return None

    @staticmethod
    def _json_strings(value: object) -> list[str]:
        if isinstance(value, str):
            return [value]
        if isinstance(value, list):
            return [text for item in value for text in ReviewerBusWatcher._json_strings(item)]
        if isinstance(value, dict):
            return [text for item in value.values() for text in ReviewerBusWatcher._json_strings(item)]
        return []

    @staticmethod
    def _validated_report_body(envelope: dict[str, object]) -> str | None:
        report_id, report_type, body = envelope.get("report_id"), envelope.get("report_type"), envelope.get("body")
        if not isinstance(report_id, str) or not report_id or not isinstance(report_type, str) or report_type not in REPORT_TYPES or not isinstance(body, str):
            return None
        if ReviewerBusWatcher._extract(REPORT_ID_RE, body) != report_id or ReviewerBusWatcher._extract(REPORT_TYPE_RE, body) != report_type:
            return None
        return body

    def _mark_response_applied(self, response_id: int, report_id: str, **changes: object) -> None:
        processed = list(self._state.get("processed_report_ids", []))
        if report_id not in processed:
            processed.append(report_id)
        self._set_state(last_applied_response_comment_id=response_id, processed_report_ids=processed, pending_response_comment_id=None, pending_response_body=None, pending_response_report_id=None, last_error=None, **changes)

    def _load_state(self) -> dict[str, object]:
        try:
            value = json.loads(self.state_path.read_text(encoding="utf-8"))
            return value if isinstance(value, dict) else {}
        except (OSError, UnicodeError, json.JSONDecodeError):
            return {}

    def _set_state(self, **changes: object) -> None:
        with self._lock:
            self._state.update(changes)
            self._state.setdefault("review_repo", REVIEW_REPO)
            self._state.setdefault("review_pr", REVIEW_PR)
            self._state.setdefault("poll_seconds", self.poll_seconds)
            self.state_path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.state_path.with_suffix(".tmp")
            temporary.write_text(json.dumps(self._state, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
            for attempt in range(10):
                try:
                    temporary.replace(self.state_path)
                    return
                except PermissionError:
                    if attempt == 9:
                        raise
                    sleep(0.1)

    @staticmethod
    def _extract(pattern: re.Pattern[str], body: str) -> str | None:
        match = pattern.search(body)
        return match.group(1).strip() if match else None

    @staticmethod
    def _resolve_executable(value: str) -> str | None:
        candidate = Path(value)
        if candidate.is_file():
            return str(candidate.resolve())
        found = shutil.which(value)
        return str(Path(found).resolve()) if found else None
