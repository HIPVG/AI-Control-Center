from datetime import datetime
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field

from backend.models.result import ExecutionResult, TokenUsage


class CodexMode(str, Enum):
    MOCK = "mock"
    REAL = "real"


class CodexRuntimeConfig(BaseModel):
    mode: CodexMode = CodexMode.MOCK
    executable: str = Field(default="codex", min_length=1)
    timeout_seconds: int = Field(default=300, ge=1, le=900)


class RuntimeConfig(BaseModel):
    codex: CodexRuntimeConfig = Field(default_factory=CodexRuntimeConfig)


class SmokeRunResult(BaseModel):
    status: str
    mode: CodexMode
    smoke_path: str | None = None
    deterministic_passed: bool = False
    execution: ExecutionResult | None = None
    error_code: str | None = None


class ProjectSmokeResult(BaseModel):
    """Persisted, bounded evidence for one configured-project smoke workflow."""

    run_id: str
    project_id: str
    project_path: str | None = None
    task_id: str = "CONTROL-CENTER-SMOKE-001"
    state: str
    start_time: datetime
    end_time: datetime | None = None
    fixture_path: str | None = None
    precheck_result: str = "not_run"
    codex_invoked: bool = False
    codex_exit_code: int | None = None
    thread_started: bool = False
    turn_started: bool = False
    turn_completed: bool = False
    postcheck_result: str = "not_run"
    changed_files: list[str] = Field(default_factory=list)
    scope_guard_result: str = "not_run"
    gross_input_tokens: int = Field(default=0, ge=0)
    cached_input_tokens: int = Field(default=0, ge=0)
    uncached_input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    budget_warning: str | None = None
    final_result: str
    error_code: str | None = None


class CommandRunResult(BaseModel):
    argv: list[str] = Field(default_factory=list)
    cwd: str | None = None
    exit_code: int | None = None
    passed: bool = False
    stdout: str | None = None
    stderr: str | None = None
    error_code: str | None = None


class CodexAttemptResult(BaseModel):
    attempt: int = Field(ge=1)
    exit_code: int | None = None
    thread_started: bool = False
    turn_started: bool = False
    turn_completed: bool = False
    gross_input_tokens: int = Field(default=0, ge=0)
    cached_input_tokens: int = Field(default=0, ge=0)
    uncached_input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    error_code: str | None = None


class TaskRunResult(BaseModel):
    run_id: str
    task_id: str
    project_id: str
    source_repo_path: str | None = None
    source_head_sha: str | None = None
    worktree_path: str | None = None
    task_branch: str | None = None
    state: str
    start_time: datetime
    end_time: datetime | None = None
    precheck_result: str = "not_run"
    precheck: CommandRunResult | None = None
    triage_result: str = "not_run"
    codex_invoked: bool = False
    codex_attempts: list[CodexAttemptResult] = Field(default_factory=list)
    codex_exit_code: int | None = None
    thread_started: bool = False
    turn_started: bool = False
    turn_completed: bool = False
    allowed_files: list[str] = Field(default_factory=list)
    changed_files: list[str] = Field(default_factory=list)
    out_of_scope_files: list[str] = Field(default_factory=list)
    scope_guard_result: str = "not_run"
    postcheck_result: str = "not_run"
    postcheck: CommandRunResult | None = None
    context_character_count: int = 0
    context_byte_count: int = 0
    gross_input_tokens: int = Field(default=0, ge=0)
    cached_input_tokens: int = Field(default=0, ge=0)
    uncached_input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    budget_warning: str | None = None
    final_result: str
    human_review_reason: str | None = None
    error_code: str | None = None


class FaultRepairResult(BaseModel):
    """Persisted evidence for one controlled, worktree-only repair validation."""

    run_id: str
    fault_id: str
    task_id: str
    project_id: str
    source_head_sha: str | None = None
    worktree_path: str | None = None
    target_file: str | None = None
    baseline_result: str = "not_run"
    baseline: CommandRunResult | None = None
    fault_injected: bool = False
    precheck_result: str = "not_run"
    precheck: CommandRunResult | None = None
    triage_result: str = "not_run"
    codex_invoked: bool = False
    codex_attempts: list[CodexAttemptResult] = Field(default_factory=list)
    repair_delta_files: list[str] = Field(default_factory=list)
    scope_guard_result: str = "not_run"
    postcheck_result: str = "not_run"
    postcheck: CommandRunResult | None = None
    original_file_match: bool | None = None
    token_usage: TokenUsage = Field(default_factory=TokenUsage)
    context_character_count: int = 0
    context_byte_count: int = 0
    state: str
    final_result: str
    human_review_reason: str | None = None
    error_code: str | None = None


def load_runtime_config(path: Path) -> RuntimeConfig:
    if not path.exists():
        return RuntimeConfig()
    import yaml
    return RuntimeConfig.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")) or {})
