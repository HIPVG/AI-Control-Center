import json
import subprocess
from pathlib import Path
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from backend.control.context_broker import TaskContext
from backend.models.result import ExecutionResult, TokenUsage
from backend.models.runtime import CodexRuntimeConfig

SMOKE_FILENAME = "smoke-result.txt"
SMOKE_CONTENT = "AI Control Center Codex smoke test PASS"
MAX_CAPTURE_CHARS = 2000


class JsonlParseResult(BaseModel):
    event_count: int = 0
    malformed_lines: int = 0
    token_usage: TokenUsage = Field(default_factory=TokenUsage)


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
        resolved_target = target.resolve()
        self._ensure_within_root(resolved_target)
        try:
            return resolved_target.read_text(encoding="utf-8") == SMOKE_CONTENT
        except (OSError, UnicodeError):
            return False

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
        prompt = (
            "Run the bounded AI Control Center smoke test. In the current directory only, "
            f"create {target.name} with exactly this UTF-8 content and no newline: {SMOKE_CONTENT}. "
            "Do not read or modify any other files. Do not run git."
        )
        command = [self.config.executable, "exec", "--json", prompt]
        try:
            completed = subprocess.run(
                command,
                cwd=smoke_directory,
                capture_output=True,
                text=True,
                timeout=self.config.timeout_seconds,
                check=False,
                shell=False,
            )
        except FileNotFoundError:
            return ExecutionResult(
                status="failed",
                test_result="not_run",
                summary="Configured Codex executable was not found.",
                error_code="CODEX_NOT_FOUND",
            )
        except subprocess.TimeoutExpired as exc:
            return ExecutionResult(
                status="failed",
                test_result="not_run",
                summary="Codex smoke execution timed out.",
                error_code="CODEX_TIMEOUT",
                stderr=self._truncate(exc.stderr),
            )

        parsed = self.parse_jsonl(completed.stdout)
        if completed.returncode != 0:
            return ExecutionResult(
                status="failed",
                test_result="not_run",
                summary="Codex smoke execution returned a non-zero exit code.",
                token_usage=parsed.token_usage,
                exit_code=completed.returncode,
                error_code="CODEX_EXIT_NONZERO",
                stderr=self._truncate(completed.stderr),
            )
        if parsed.malformed_lines:
            return ExecutionResult(
                status="failed",
                test_result="not_run",
                summary="Codex returned malformed JSONL output.",
                token_usage=parsed.token_usage,
                exit_code=completed.returncode,
                error_code="MALFORMED_JSONL",
                stderr=self._truncate(completed.stderr),
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
        )

    @staticmethod
    def _truncate(value: str | bytes | None) -> str | None:
        if value is None:
            return None
        if isinstance(value, bytes):
            value = value.decode("utf-8", errors="replace")
        return value[:MAX_CAPTURE_CHARS] or None
