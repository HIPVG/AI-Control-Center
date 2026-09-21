from pydantic import BaseModel, Field


class TokenUsage(BaseModel):
    input_tokens: int = Field(default=0, ge=0)
    cached_input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    available: bool = False

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


class TestResult(BaseModel):
    command: str = Field(min_length=1)
    passed: bool
    exit_code: int
    summary: str


class ProcessDiagnostics(BaseModel):
    argv: list[str] = Field(default_factory=list)
    cwd: str | None = None
    exit_code: int | None = None
    timed_out: bool = False
    stdout_event_count: int = Field(default=0, ge=0)
    event_types: list[str] = Field(default_factory=list)
    stderr_summary: str | None = None


class ExecutionResult(BaseModel):
    status: str
    files_changed: list[str] = Field(default_factory=list)
    tests_run: list[str] = Field(default_factory=list)
    test_result: str
    summary: str
    token_usage: TokenUsage = Field(default_factory=TokenUsage)
    exit_code: int | None = None
    error_code: str | None = None
    stderr: str | None = None
    diagnostics: ProcessDiagnostics | None = None
