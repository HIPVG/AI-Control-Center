from pydantic import BaseModel, Field


class TokenUsage(BaseModel):
    input_tokens: int = Field(default=0, ge=0)
    cached_input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


class TestResult(BaseModel):
    command: str = Field(min_length=1)
    passed: bool
    exit_code: int
    summary: str


class ExecutionResult(BaseModel):
    status: str
    files_changed: list[str] = Field(default_factory=list)
    tests_run: list[str] = Field(default_factory=list)
    test_result: str
    summary: str
    token_usage: TokenUsage = Field(default_factory=TokenUsage)
