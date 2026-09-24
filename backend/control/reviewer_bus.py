"""Deterministic GitHub reviewer-bus watcher for continuing local Codex.

The GitHub Work event Task owns reviewer reasoning. This watcher transports a
matching reviewer response into a fresh bounded Codex exec turn rooted at the
AI-Control-Center repository. Continuity comes from persisted repo/state/history,
not from resuming a desktop/CLI session database.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

REVIEW_REPO = "HIPVG/AI-Control-Center-Review-Bridge"
REVIEW_PR = 1
POLL_SECONDS = 120
REPORT_ID_RE = re.compile(r"(?m)^REPORT_ID:\s*([^\s]+)\s*$")
REPORT_TYPE_RE = re.compile(r"(?m)^REPORT_TYPE:\s*([^\s]+)\s*$")
IN_REPLY_TO_RE = re.compile(r"(?m)^IN_REPLY_TO:\s*([^\s]+)\s*$")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ReviewerBusWatcher:
    """Poll PR #1 for one matching reviewer response and start the continuation turn."""

    def __init__(
        self,
        project_root: Path,
        codex_executable: str = "codex",
        *,
        gh_executable: str = "gh",
        poll_seconds: int = POLL_SECONDS,
        command_runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    ) -> None:
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

        pair = self._latest_ready_pair(comments)
        if pair is None:
            self._set_state(last_error=None)
            return self.status()

        report, response = pair
        report_id = self._extract(REPORT_ID_RE, report.get("body", ""))
        if not report_id:
            self._set_state(last_error="REPORT_ID_MISSING")
            return self.status()

        response_id = int(response.get("id", 0) or 0)
        prompt = self._resume_prompt(report_id, str(response.get("body", "")))
        completed = self._continue_codex(prompt)
        if completed.returncode != 0:
            self._set_state(
                last_report_id=report_id,
                last_response_comment_id=response_id,
                last_error="CODEX_CONTINUATION_FAILED",
                last_codex_exit_code=completed.returncode,
            )
            return self.status()

        self._set_state(
            last_report_id=report_id,
            last_applied_response_comment_id=response_id,
            last_response_comment_id=response_id,
            last_continuation_at=_utc_now(),
            last_codex_exit_code=completed.returncode,
            last_error=None,
        )
        return self.status()

    def _loop(self) -> None:
        while not self._stop.is_set():
            self.run_once()
            self._stop.wait(self.poll_seconds)

    def _fetch_comments(self) -> tuple[list[dict[str, object]], str | None]:
        gh = self._resolve_executable(self.gh_executable) or self.gh_executable
        argv = [
            gh,
            "api",
            f"repos/{REVIEW_REPO}/issues/{REVIEW_PR}/comments?per_page=100",
            "--paginate",
            "--jq",
            ".[] | {id: .id, body: .body, created_at: .created_at}",
        ]
        try:
            completed = self.command_runner(
                argv,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
                check=False,
                shell=False,
            )
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

    def _latest_ready_pair(self, comments: list[dict[str, object]]) -> tuple[dict[str, object], dict[str, object]] | None:
        reports = [
            item for item in comments
            if self._extract(REPORT_ID_RE, str(item.get("body", "")))
            and self._extract(REPORT_TYPE_RE, str(item.get("body", "")))
        ]
        if not reports:
            return None

        latest = max(reports, key=lambda item: int(item["id"]))
        report_id = self._extract(REPORT_ID_RE, str(latest.get("body", "")))
        report_comment_id = int(latest["id"])
        last_applied = int(self._state.get("last_applied_response_comment_id", 0) or 0)

        matching = [
            item for item in comments
            if int(item["id"]) > report_comment_id
            and int(item["id"]) > last_applied
            and self._extract(IN_REPLY_TO_RE, str(item.get("body", ""))) == report_id
        ]
        if not matching:
            return None
        return latest, min(matching, key=lambda item: int(item["id"]))

    def _continue_codex(self, prompt: str) -> subprocess.CompletedProcess[str]:
        codex = self._resolve_executable(self.codex_executable) or self.codex_executable
        argv = [codex, "exec", "--sandbox", "workspace-write", "--json", prompt]
        codex_sqlite_home = (self.project_root / "state" / "codex-sqlite").resolve()
        codex_sqlite_home.mkdir(parents=True, exist_ok=True)
        environment = os.environ.copy()
        if not environment.get("HOME") and environment.get("USERPROFILE"):
            environment["HOME"] = environment["USERPROFILE"]
        environment["CODEX_SQLITE_HOME"] = str(codex_sqlite_home)
        try:
            return self.command_runner(
                argv,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=900,
                check=False,
                shell=False,
                stdin=subprocess.DEVNULL,
                env=environment,
            )
        except (OSError, subprocess.TimeoutExpired):
            return subprocess.CompletedProcess(argv, 1, "", "resume failed")

    @staticmethod
    def _resume_prompt(report_id: str, response_body: str) -> str:
        return (
            "A matching ChatGPT reviewer response arrived on the operational GitHub reviewer bus.\n"
            f"REPORT_ID: {report_id}\n"
            "This is a fresh continuation turn, not a resumed desktop/CLI thread. "
            "Reconstruct authoritative context from the repository: read AGENTS.md, docs/WORKING_RULES.md, docs/CURRENT_WORK.md, relevant engineering history, persisted Day state, and the latest approved plan/runbook before acting. "
            "Apply the complete reviewer response below, then continue only the already-approved work. "
            "Use the minimum sufficient action and do not broaden scope. "
            "Use PR #1 in HIPVG/AI-Control-Center-Review-Bridge for all reviewer-facing reports. "
            "After successfully publishing any reviewer-facing report, END THIS CODEX TURN; "
            "do not poll the PR yourself. The deterministic reviewer-bus watcher will resume the session "
            "when the matching IN_REPLY_TO response arrives.\n\n"
            "REVIEWER_RESPONSE:\n"
            f"{response_body.strip()}\n"
        )

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
            temporary.replace(self.state_path)

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
