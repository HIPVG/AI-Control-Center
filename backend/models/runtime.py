from datetime import datetime
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field

from backend.models.result import ExecutionResult


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


def load_runtime_config(path: Path) -> RuntimeConfig:
    if not path.exists():
        return RuntimeConfig()
    import yaml
    return RuntimeConfig.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")) or {})
