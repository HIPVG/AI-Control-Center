"""The narrow, server-owned Day 1-14 runner for LocalLLM-Lab.

This intentionally has no browser-supplied commands, paths, prompts, or file
scope.  It reads the authoritative runbook at execution time and only runs
actions whose command and safety boundary are already trusted in code.
"""

import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from threading import Event, RLock, Thread
from typing import Callable

from backend.models.local_llm_day import LocalLLMDayReport, LocalLLMDaySnapshot, LocalLLMDayState


class LocalLLMDayProgram:
    RUNBOOK = Path("docs/runbooks/work-plan-day1-14.md")

    def __init__(
        self,
        root: Path,
        *,
        saved: dict[str, object] | None = None,
        persist: Callable[[dict[str, object]], None] | None = None,
        audit: Callable[[str, str, dict[str, object]], None] | None = None,
    ) -> None:
        self.root = root.resolve()
        self.persist = persist
        self.audit = audit
        self.snapshot = LocalLLMDaySnapshot.model_validate(saved or {})
        self._lock, self._stop = RLock(), Event()
        self._thread: Thread | None = None
        if self.snapshot.state == LocalLLMDayState.RUNNING:
            self.snapshot.state = LocalLLMDayState.PAUSED
            self.snapshot.activity = "Interrupted by restart; press Resume to rerun the selected Day safely."
            self.snapshot.stop_reason = "INTERRUPTED_REQUIRES_RESUME"
            self._save()

    def days(self) -> list[dict[str, object]]:
        return [
            {"day": number, "objective": objective}
            for number, objective in sorted(self._objectives().items())
        ]

    def view(self) -> dict[str, object]:
        with self._lock:
            return self.snapshot.model_dump(mode="json")

    def start(self, day: int) -> dict[str, object]:
        objectives = self._objectives()
        if day not in objectives:
            return {"error_code": "DAY_NOT_CONFIGURED", **self.view()}
        with self._lock:
            if self.snapshot.state == LocalLLMDayState.RUNNING:
                return {"error_code": "DAY_ALREADY_RUNNING", **self.view()}
            self._stop.clear()
            self.snapshot = LocalLLMDaySnapshot(
                selected_day=day,
                state=LocalLLMDayState.RUNNING,
                objective=objectives[day],
                activity="Reading the Day objective and trusted repository state.",
                progress=5,
            )
            self._audit("LOCAL_LLM_DAY_STARTED", {"day": day, "objective": objectives[day]})
            self._save()
            # Keep a controlled Day alive through a normal server shutdown so
            # its persisted result cannot be abandoned by a transient host.
            self._thread = Thread(target=self._execute, args=(day, objectives[day]), name=f"local-llm-day-{day}")
            self._thread.start()
            return self.snapshot.model_dump(mode="json")

    def resume(self) -> dict[str, object]:
        with self._lock:
            day = self.snapshot.selected_day
            if day is None or self.snapshot.state not in {LocalLLMDayState.PAUSED, LocalLLMDayState.STOPPED}:
                return {"error_code": "DAY_NOT_RESUMABLE", **self.view()}
        return self.start(day)

    def stop(self) -> dict[str, object]:
        with self._lock:
            if self.snapshot.state == LocalLLMDayState.RUNNING:
                self._stop.set()
                self.snapshot.activity = "Stop requested; waiting for the current trusted command to finish."
                self._save()
        return self.view()

    def join(self, timeout: float | None = None) -> None:
        thread = self._thread
        if thread:
            thread.join(timeout)

    def _execute(self, day: int, objective: str) -> None:
        try:
            if day == 1:
                self._run_day_one(day, objective)
            else:
                self._set_terminal(
                    LocalLLMDayState.FAILED,
                    LocalLLMDayReport(
                        day=day,
                        objective=objective,
                        result="NO_TRUSTED_DAY_ACTION",
                        summary="The objective was read, but this Day has no configured deterministic command or bounded Builder WorkOrder yet.",
                        evidence={"runbook": str(self.RUNBOOK), "day": day},
                    ),
                )
        except Exception as exc:  # The report deliberately avoids process output and source content.
            self._set_terminal(
                LocalLLMDayState.FAILED,
                LocalLLMDayReport(day=day, objective=objective, result="HARNESS_FAILURE", summary=f"The Day runner stopped safely: {type(exc).__name__}.", evidence={}),
            )

    def _run_day_one(self, day: int, objective: str) -> None:
        repo = self._inspect_repository()
        if self._stopped(day, objective):
            return
        self._progress("Verified trusted repository state.", 30, "repository_state")
        missing_docs = self._missing_docs()
        if self._stopped(day, objective):
            return
        self._progress("Inspected baseline documentation sources.", 50, "documentation")
        tests = self._run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"])
        if self._stopped(day, objective):
            return
        self._progress("Ran the LocalLLM-Lab regression suite.", 90, "tests")
        evidence = {
            "branch": repo["branch"],
            "head": repo["head"],
            "origin": repo["origin"],
            "working_tree_clean": not bool(repo["status"]),
            "staged_files": repo["staged_count"],
            "missing_documentation": missing_docs,
            "tests_exit_code": tests,
        }
        if tests != 0:
            result, summary, state = "TEST_FAILURE", "Regression tests failed; their result is preserved as Day evidence and no repair was attempted.", LocalLLMDayState.FAILED
        elif repo["status"] or repo["staged_count"] or missing_docs:
            result, summary, state = "BASELINE_REQUIRES_RECONCILIATION", "The audit found uncommitted work, staged work, or missing baseline documentation; no target-repository change was made.", LocalLLMDayState.FAILED
        else:
            result, summary, state = "DAY_COMPLETE", "Repository baseline, documentation sources, and regression tests are trusted for the Day 1 freeze.", LocalLLMDayState.COMPLETE
        self._set_terminal(state, LocalLLMDayReport(day=day, objective=objective, result=result, summary=summary, evidence=evidence))

    def _inspect_repository(self) -> dict[str, object]:
        return {
            "status": self._output(["git", "status", "--short"]),
            "branch": self._output(["git", "branch", "--show-current"]),
            "head": self._output(["git", "rev-parse", "HEAD"]),
            "origin": self._output(["git", "remote", "get-url", "origin"]),
            "staged_count": len([line for line in self._output(["git", "diff", "--cached", "--name-only"]).splitlines() if line]),
        }

    def _output(self, arguments: list[str]) -> str:
        completed = subprocess.run(self._git(arguments), cwd=self.root, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30, check=False)
        return completed.stdout.strip() if completed.returncode == 0 else ""

    def _run(self, arguments: list[str]) -> int:
        process = subprocess.Popen(arguments, cwd=self.root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        while process.poll() is None:
            if self._stop.wait(0.1):
                process.terminate()
                process.wait(timeout=10)
                return -1
        return process.returncode

    def _git(self, arguments: list[str]) -> list[str]:
        if not arguments or arguments[0] != "git":
            return arguments
        return ["git", "-c", f"safe.directory={self.root.as_posix()}", *arguments[1:]]

    def _objectives(self) -> dict[int, str]:
        path = self.root / self.RUNBOOK
        if not path.is_file():
            return {}
        objectives: dict[int, str] = {}
        for line in path.read_text(encoding="utf-8").splitlines():
            match = re.match(r"^## Day ([1-9]|1[0-4]) - (.+)$", line)
            if match:
                objectives[int(match.group(1))] = match.group(2).strip()
        return objectives

    def _missing_docs(self) -> list[str]:
        required_docs = [
            self.RUNBOOK,
            Path("docs/architecture/decision-reasoning-architecture.md"),
            Path("docs/handoff/handoff-2026-09-18.md"),
        ]
        return [str(path) for path in required_docs if not (self.root / path).is_file()]

    def _stopped(self, day: int, objective: str) -> bool:
        if not self._stop.is_set():
            return False
        self._set_terminal(LocalLLMDayState.STOPPED, LocalLLMDayReport(day=day, objective=objective, result="STOPPED", summary="Stopped by the user before the Day was complete.", evidence={}))
        return True

    def _progress(self, activity: str, progress: int, step: str) -> None:
        with self._lock:
            self.snapshot.activity, self.snapshot.progress = activity, progress
            self.snapshot.completed_steps.append(step)
            self._save()

    def _set_terminal(self, state: LocalLLMDayState, report: LocalLLMDayReport) -> None:
        with self._lock:
            self.snapshot.state, self.snapshot.report = state, report
            self.snapshot.activity, self.snapshot.progress = report.summary, 100
            self.snapshot.stop_reason = report.result
            self.snapshot.completed_steps.append("complete")
            self._audit("LOCAL_LLM_DAY_COMPLETE", {"day": report.day, "state": state.value, "result": report.result})
            self._save()

    def _save(self) -> None:
        self.snapshot.updated_at = datetime.now(timezone.utc)
        if self.persist:
            self.persist(self.snapshot.model_dump(mode="json"))

    def _audit(self, event: str, details: dict[str, object]) -> None:
        if self.audit:
            self.audit("LOCAL_LLM_DAY", event, details)
