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


def load_runtime_config(path: Path) -> RuntimeConfig:
    if not path.exists():
        return RuntimeConfig()
    import yaml
    return RuntimeConfig.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")) or {})
