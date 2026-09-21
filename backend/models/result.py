from pydantic import BaseModel, Field, model_validator


class TokenUsage(BaseModel):
    """Reported usage preserves gross input while exposing cache-adjusted input."""

    input_tokens: int = Field(default=0, ge=0)
    cached_input_tokens: int = Field(default=0, ge=0)
    gross_input_tokens: int = Field(default=0, ge=0)
    uncached_input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    available: bool = False

    @model_validator(mode="after")
    def derive_input_breakdown(self) -> "TokenUsage":
        self.gross_input_tokens = self.input_tokens
        self.uncached_input_tokens = max(self.input_tokens - self.cached_input_tokens, 0)
        return self

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


class TestResult(BaseModel):
    command: str = Field(min_length=1)
    passed: bool
    exit_code: int
    summary: str


class ProcessDiagnostics(BaseModel):
    executable_path: str | None = None
    argv: list[str] = Field(default_factory=list)
    cwd: str | None = None
    exit_code: int | None = None
    timed_out: bool = False
    stdin_closed: bool = False
    stdout_line_count: int = Field(default=0, ge=0)
    stdout_event_count: int = Field(default=0, ge=0)
    invalid_json_lines: int = Field(default=0, ge=0)
    invalid_line_summary: str | None = None
    event_types: list[str] = Field(default_factory=list)
    first_error_event: str | None = None
    thread_started: bool = False
    turn_started: bool = False
    turn_completed: bool = False
    turn_failed: bool = False
    error_event: bool = False
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
