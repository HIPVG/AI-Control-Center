"""One-shot RG-04 production Watcher probe with an isolated validation ledger."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from backend.control.reviewer_bus import REPORT_ID_RE, ReviewerBusWatcher


REPORT_ID = "G8-RG04-REVIEW-PATH-PROBE-20261001-002"
RUNTIME = ROOT / "state" / "rg04-review-path-validation-20261001-002"
STATE = RUNTIME / "watcher-state.json"
TRACE = RUNTIME / "probe-trace.json"
LOG = RUNTIME / "probe-events.jsonl"
TIMEOUT_SECONDS = 720


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def event(kind: str, **fields: object) -> None:
    payload = {"at": now(), "event": kind, **fields}
    with LOG.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")


def autostart_counts() -> dict[str, object]:
    marker = str(RUNTIME).lower()
    script = (
        "$m=$args[0].ToLowerInvariant();"
        "$services=@(Get-CimInstance Win32_Service -ErrorAction Stop | "
        "Where-Object { (($_.PathName)+'').ToLowerInvariant().Contains($m) });"
        "$tasks=@(Get-ScheduledTask -ErrorAction Stop | Where-Object { "
        "$joined=(($_.Actions | ForEach-Object { (($_.Execute)+' '+($_.Arguments)) }) -join ' ');"
        "$joined.ToLowerInvariant().Contains($m) });"
        "[ordered]@{services=$services.Count;scheduled_tasks=$tasks.Count}|ConvertTo-Json -Compress"
    )
    completed = subprocess.run(
        ["powershell", "-NoProfile", "-Command", script, marker],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
        check=False,
    )
    if completed.returncode != 0:
        return {
            "status": "ERROR",
            "exit_code": completed.returncode,
            "stderr_sha256": sha256_bytes(completed.stderr.encode("utf-8")),
        }
    try:
        value = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return {
            "status": "INVALID_OUTPUT",
            "exit_code": completed.returncode,
            "stdout_sha256": sha256_bytes(completed.stdout.encode("utf-8")),
        }
    return {"status": "OK", **value}


def main() -> int:
    RUNTIME.mkdir(parents=True, exist_ok=False)
    original_state = ROOT / "state" / "reviewer-bus-watcher.json"
    original_bytes = original_state.read_bytes()
    managed_home = (ROOT / "state" / "codex-sqlite").resolve()
    if not managed_home.is_dir():
        raise RuntimeError("CODEX_SQLITE_HOME_NOT_FOUND")
    event(
        "PROBE_PROCESS_STARTED",
        pid=os.getpid(),
        original_state_sha256=sha256_bytes(original_bytes),
    )

    observer = ReviewerBusWatcher(ROOT)
    report = None
    wait_started = time.monotonic()
    while time.monotonic() - wait_started < TIMEOUT_SECONDS:
        comments, error = observer._fetch_comments()
        if error:
            event("REPORT_FETCH_ERROR", error=error)
            time.sleep(5)
            continue
        report = next(
            (
                item
                for item in comments
                if observer._extract(REPORT_ID_RE, str(item.get("body", "")))
                == REPORT_ID
            ),
            None,
        )
        if report:
            break
        time.sleep(2)
    if report is None:
        event("PROBE_STOPPED", result="REPORT_NOT_OBSERVED")
        return 2

    event(
        "REPORT_OBSERVED",
        comment_id=report["id"],
        created_at=report.get("created_at"),
        body_sha256=sha256_bytes(str(report["body"]).encode("utf-8")),
    )
    watcher = ReviewerBusWatcher(ROOT, poll_seconds=120)
    watcher.state_path = STATE
    watcher._state = {}
    continuation: dict[str, object] = {
        "count": 0,
        "started_at": None,
        "finished_at": None,
        "exit_code": None,
        "stdout_sha256": None,
        "stderr_sha256": None,
    }
    post_attempts: list[dict[str, object]] = []
    real_continue = watcher._continue_codex

    def measured_continue(prompt: str) -> subprocess.CompletedProcess[str]:
        continuation["count"] = int(continuation["count"]) + 1
        continuation["started_at"] = now()
        continuation["prompt_sha256"] = sha256_bytes(prompt.encode("utf-8"))
        completed = real_continue(prompt)
        continuation["finished_at"] = now()
        continuation["exit_code"] = completed.returncode
        continuation["stdout_sha256"] = sha256_bytes(completed.stdout.encode("utf-8"))
        continuation["stderr_sha256"] = sha256_bytes(completed.stderr.encode("utf-8"))
        return completed

    def block_followup(body: str) -> None:
        post_attempts.append(
            {"at": now(), "body_sha256": sha256_bytes(body.encode("utf-8"))}
        )
        return None

    watcher._continue_codex = measured_continue  # type: ignore[method-assign]
    watcher._post_comment = block_followup  # type: ignore[method-assign]
    started_at = now()
    started = watcher.start()
    event("WATCHER_START", started=started, status=watcher.status())
    deadline = time.monotonic() + TIMEOUT_SECONDS
    result = "TIMEOUT"
    try:
        while time.monotonic() < deadline:
            status = watcher.status()
            entry = status.get("report_registry", {}).get(REPORT_ID, {})
            if entry.get("state") == "APPLIED":
                result = "PASS"
                break
            if entry.get("state") in {
                "CONTINUATION_FAILED",
                "HUMAN_REQUIRED",
                "CONFIRMATION_BLOCKED",
            }:
                result = str(entry.get("state"))
                break
            if status.get("last_error") in {
                "CODEX_CONTINUATION_FAILED",
                "CODEX_CONTINUATION_OUTPUT_INVALID",
                "GITHUB_REPORT_DELIVERY_FAILED",
                "REVIEW_RESPONSE_CORRELATION_MISMATCH",
            }:
                result = str(status["last_error"])
                break
            time.sleep(1)
    finally:
        watcher.stop()
    stopped_at = now()
    final_status = watcher.status()
    comments, fetch_error = watcher._fetch_comments()
    responses = (
        [
            item
            for item in comments
            if watcher._response_target(str(item.get("body", ""))) == REPORT_ID
        ]
        if not fetch_error
        else []
    )
    original_after = original_state.read_bytes()
    trace = {
        "schema": "ai-control-center.rg04-review-path-probe.v1",
        "validation_id": "G8-RG04-REVIEW-PATH-VALIDATION-20261001-002",
        "authority_id": "UTH-G8-RG04-REVIEW-PATH-RETRY-20261001-001",
        "report_id": REPORT_ID,
        "result": result,
        "started_at": started_at,
        "stopped_at": stopped_at,
        "watcher_start_count": 1,
        "watcher_stop_count": 1,
        "poll_seconds": 120,
        "isolated_state_path": str(STATE),
        "project_root": str(ROOT),
        "codex_sqlite_home": str(managed_home),
        "original_registry": {
            "path": str(original_state),
            "sha256_before": sha256_bytes(original_bytes),
            "sha256_after": sha256_bytes(original_after),
            "unchanged": original_bytes == original_after,
        },
        "report": {
            "comment_id": report["id"],
            "created_at": report.get("created_at"),
            "body_sha256": sha256_bytes(str(report["body"]).encode("utf-8")),
        },
        "matching_responses": [
            {
                "comment_id": item["id"],
                "created_at": item.get("created_at"),
                "body_sha256": sha256_bytes(str(item["body"]).encode("utf-8")),
            }
            for item in responses
        ],
        "continuation": continuation,
        "followup_post_attempts": post_attempts,
        "final_watcher_status": final_status,
        "autostart_after_stop": autostart_counts(),
        "scope": {
            "day_go": 0,
            "model_execution": 0,
            "product_state_change": 0,
            "credential_change": 0,
            "release": 0,
        },
    }
    TRACE.write_text(
        json.dumps(trace, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
        newline="\n",
    )
    event("PROBE_STOPPED", result=result, trace_sha256=sha256_bytes(TRACE.read_bytes()))
    return 0 if result == "PASS" and continuation["count"] == 1 and not post_attempts else 3


if __name__ == "__main__":
    sys.exit(main())
