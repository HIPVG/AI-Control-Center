import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from backend.control.context_broker import TaskContext
from backend.models.result import ExecutionResult, ProcessDiagnostics, TokenUsage
from backend.models.runtime import CodexRuntimeConfig

SMOKE_FILENAME = "smoke.txt"
SMOKE_CONTENT = "AI Control Center Codex smoke test PASS"
MAX_CAPTURE_CHARS = 2000


class JsonlParseResult(BaseModel):
    event_count: int = 0
    malformed_lines: int = 0
    token_usage: TokenUsage = Field(default_factory=TokenUsage)
    event_types: list[str] = Field(default_factory=list)
    thread_started: bool = False
    turn_started: bool = False
    turn_completed: bool = False
    turn_failed: bool = False
    error_event: bool = False


class SmokeWorkspace:
    """Owns the only directory that a smoke runner may use."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def create_run(self) -> Path:
        self.root.mkdir(parents=True, exist_ok=True)
        run_directory = (self.root / uuid4().hex).resolve()
        self._ensure_within_root(run_directory)
        run_directory.mkdir()
        return run_directory

    def result_path(self, run_directory: Path) -> Path:
        resolved_run = run_directory.resolve()
        self._ensure_within_root(resolved_run)
        target = (resolved_run / SMOKE_FILENAME).resolve()
        self._ensure_within_root(target)
        return target

    def accepts(self, target: Path) -> bool:
        return self.acceptance_error(target) is None

    def acceptance_error(self, target: Path) -> str | None:
        resolved_target = target.resolve()
        self._ensure_within_root(resolved_target)
        if not resolved_target.is_file():
            return "SMOKE_RESULT_MISSING"
        try:
            return None if resolved_target.read_text(encoding="utf-8") == SMOKE_CONTENT else "SMOKE_CONTENT_MISMATCH"
        except (OSError, UnicodeError):
            return "SMOKE_CONTENT_MISMATCH"

    def _ensure_within_root(self, candidate: Path) -> None:
        try:
            candidate.relative_to(self.root)
        except ValueError as exc:
            raise ValueError("smoke path must remain inside the configured smoke directory") from exc


class CodexRunner:
    """Isolated adapter boundary for `codex exec --json`."""

    @staticmethod
    def parse_usage(raw_json: str) -> TokenUsage:
        try:
            payload = json.loads(raw_json)
        except json.JSONDecodeError:
            return TokenUsage()
        return CodexRunner._usage_from_payload(payload)

    @classmethod
    def parse_jsonl(cls, raw_jsonl: str) -> JsonlParseResult:
        parsed = JsonlParseResult()
        latest_usage = TokenUsage()
        for line in raw_jsonl.splitlines():
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                parsed.malformed_lines += 1
                continue
            parsed.event_count += 1
            if isinstance(payload, dict) and isinstance(payload.get("type"), str):
                event_type = payload["type"]
                if event_type not in parsed.event_types:
                    parsed.event_types.append(event_type)
                parsed.thread_started = parsed.thread_started or event_type == "thread.started"
                parsed.turn_started = parsed.turn_started or event_type == "turn.started"
                parsed.turn_completed = parsed.turn_completed or event_type == "turn.completed"
                parsed.turn_failed = parsed.turn_failed or event_type == "turn.failed"
                parsed.error_event = parsed.error_event or event_type == "error"
            usage = cls._usage_from_payload(payload)
            if usage.available:
                latest_usage = usage
        parsed.token_usage = latest_usage
        return parsed

    @staticmethod
    def _usage_from_payload(payload: Any) -> TokenUsage:
        latest = TokenUsage()

        def visit(value: Any) -> None:
            nonlocal latest
            if isinstance(value, dict):
                keys = {"input_tokens", "cached_input_tokens", "output_tokens"}
                if keys.intersection(value):
                    latest = TokenUsage(
                        input_tokens=CodexRunner._safe_token(value.get("input_tokens")),
                        cached_input_tokens=CodexRunner._safe_token(value.get("cached_input_tokens")),
                        output_tokens=CodexRunner._safe_token(value.get("output_tokens")),
                        available=True,
                    )
                for child in value.values():
                    visit(child)
            elif isinstance(value, list):
                for child in value:
                    visit(child)

        visit(payload)
        return latest

    @staticmethod
    def _safe_token(value: Any) -> int:
        return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else 0


class MockCodexRunner(CodexRunner):
    def run(self, context: TaskContext) -> ExecutionResult:
        return ExecutionResult(
            status="completed",
            files_changed=[context.allowed_files[0]],
            tests_run=context.acceptance_tests,
            test_result="pass",
            summary="Mock builder applied an in-scope change.",
            token_usage=TokenUsage(),
        )


class RealCodexRunner(CodexRunner):
    def __init__(self, config: CodexRuntimeConfig) -> None:
        self.config = config

    def run_smoke(self, smoke_directory: Path, target: Path) -> ExecutionResult:
        prompt = f"Create {target.name} in the current working directory containing exactly this text and no newline: {SMOKE_CONTENT}"
        executable_path, command = self.build_smoke_command(prompt)
        try:
            completed = subprocess.run(
                command,
                cwd=smoke_directory,
                capture_output=True,
                text=True,
                timeout=self.config.timeout_seconds,
                check=False,
                shell=False,
                stdin=subprocess.DEVNULL,
                env=self._process_environment(),
            )
        except FileNotFoundError:
            return ExecutionResult(
                status="failed",
                test_result="not_run",
                summary="Configured Codex executable was not found.",
                error_code="CODEX_NOT_FOUND",
                diagnostics=self._diagnostics(command, smoke_directory, executable_path=executable_path),
            )
        except subprocess.TimeoutExpired as exc:
            return ExecutionResult(
                status="failed",
                test_result="not_run",
                summary="Codex smoke execution timed out.",
                error_code="CODEX_TIMEOUT",
                stderr=self._truncate(exc.stderr),
                diagnostics=self._diagnostics(
                    command,
                    smoke_directory,
                    executable_path=executable_path,
                    timed_out=True,
                    stderr=exc.stderr,
                ),
            )

        parsed = self.parse_jsonl(completed.stdout)
        diagnostics = self._diagnostics(
            command,
            smoke_directory,
            executable_path=executable_path,
            exit_code=completed.returncode,
            parsed=parsed,
            stderr=completed.stderr,
        )
        if completed.returncode != 0:
            return ExecutionResult(
                status="failed",
                test_result="not_run",
                summary="Codex smoke execution returned a non-zero exit code.",
                token_usage=parsed.token_usage,
                exit_code=completed.returncode,
                error_code="CODEX_TURN_FAILED" if parsed.turn_failed else "CODEX_EXIT_NONZERO",
                stderr=self._truncate(completed.stderr),
                diagnostics=diagnostics,
            )
        if parsed.malformed_lines or parsed.turn_failed or parsed.error_event or not parsed.turn_completed:
            return ExecutionResult(
                status="failed",
                test_result="not_run",
                summary="Codex did not produce a successful completed turn event.",
                token_usage=parsed.token_usage,
                exit_code=completed.returncode,
                error_code="CODEX_TURN_FAILED" if parsed.turn_failed else "CODEX_OUTPUT_INVALID",
                stderr=self._truncate(completed.stderr),
                diagnostics=diagnostics,
            )
        return ExecutionResult(
            status="completed",
            files_changed=[target.name],
            tests_run=["deterministic smoke file check"],
            test_result="pending",
            summary="Codex smoke execution completed.",
            token_usage=parsed.token_usage,
            exit_code=completed.returncode,
            stderr=self._truncate(completed.stderr),
            diagnostics=diagnostics,
        )

    def build_smoke_command(self, prompt: str) -> tuple[str | None, list[str]]:
        executable_path = self.resolve_executable()
        executable = executable_path or self.config.executable
        arguments = [
            executable,
            "exec",
            "--sandbox",
            "workspace-write",
            "--skip-git-repo-check",
            "--json",
            prompt,
        ]
        if Path(executable).suffix.lower() in {".cmd", ".bat"}:
            # A Windows command shim cannot be launched reliably with
            # CreateProcess. Invoke cmd explicitly while retaining shell=False.
            command_processor = os.environ.get("COMSPEC", r"C:\Windows\System32\cmd.exe")
            return executable_path, [command_processor, "/d", "/s", "/c", subprocess.list2cmdline(arguments)]
        return executable_path, arguments

    def resolve_executable(self) -> str | None:
        configured = Path(self.config.executable)
        if configured.is_file():
            return str(configured.resolve())
        resolved = shutil.which(self.config.executable)
        return str(Path(resolved).resolve()) if resolved else None

    @staticmethod
    def _process_environment() -> dict[str, str]:
        """Supply the Windows profile through HOME when Codex requires it."""
        environment = os.environ.copy()
        if not environment.get("HOME") and environment.get("USERPROFILE"):
            environment["HOME"] = environment["USERPROFILE"]
        return environment

    @staticmethod
    def _diagnostics(
        command: list[str],
        smoke_directory: Path,
        *,
        executable_path: str | None = None,
        exit_code: int | None = None,
        timed_out: bool = False,
        parsed: JsonlParseResult | None = None,
        stderr: str | bytes | None = None,
    ) -> ProcessDiagnostics:
        return ProcessDiagnostics(
            executable_path=executable_path,
            argv=command,
            cwd=str(smoke_directory),
            exit_code=exit_code,
            timed_out=timed_out,
            stdin_closed=True,
            stdout_event_count=parsed.event_count if parsed else 0,
            event_types=parsed.event_types if parsed else [],
            thread_started=parsed.thread_started if parsed else False,
            turn_started=parsed.turn_started if parsed else False,
            turn_completed=parsed.turn_completed if parsed else False,
            turn_failed=parsed.turn_failed if parsed else False,
            error_event=parsed.error_event if parsed else False,
            stderr_summary=RealCodexRunner._truncate(stderr),
        )

    @staticmethod
    def _truncate(value: str | bytes | None) -> str | None:
        if value is None:
            return None
        if isinstance(value, bytes):
            value = value.decode("utf-8", errors="replace")
        return value[:MAX_CAPTURE_CHARS] or None
