from pydantic import BaseModel, Field


class ProviderSettings(BaseModel):
    provider: str = "mock"
    model: str | None = None
    timeout_seconds: int = Field(default=30, ge=1, le=120)
    max_transient_retries: int = Field(default=1, ge=0, le=1)


class ProviderBudget(BaseModel):
    daily_input_tokens: int = Field(default=150000, ge=0)
    daily_output_tokens: int = Field(default=20000, ge=0)
    max_calls: int = Field(default=10, ge=0)


class OrchestrationSettings(BaseModel):
    architect: ProviderSettings = Field(default_factory=ProviderSettings)
    evaluator: ProviderSettings = Field(default_factory=ProviderSettings)
    architect_budget: ProviderBudget = Field(default_factory=ProviderBudget)
    evaluator_budget: ProviderBudget = Field(default_factory=ProviderBudget)


class OrchestrationConfig(BaseModel):
    orchestration: OrchestrationSettings = Field(default_factory=OrchestrationSettings)
