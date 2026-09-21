from enum import Enum

from pydantic import BaseModel, Field, field_validator


class RoutingRole(str, Enum):
    ARCHITECT = "architect"
    EVALUATOR = "evaluator"
    CODEX = "codex"


class TaskComplexity(str, Enum):
    SIMPLE = "simple"
    NORMAL = "normal"
    COMPLEX = "complex"


class FailureType(str, Enum):
    REASONING = "reasoning_failure"
    UNKNOWN = "unknown"
    NETWORK = "network_failure"
    MISSING_DEPENDENCY = "missing_dependency"
    SANDBOX = "sandbox_failure"
    PERMISSION = "permission_failure"
    ENVIRONMENT = "environment_failure"
    INVALID_CONFIGURATION = "invalid_configuration"
    SCOPE_GUARD = "scope_guard_failure"
    GIT_SAFETY = "git_safety_failure"


class ModelProfile(BaseModel):
    provider: str = Field(min_length=1, max_length=80)
    model: str = Field(min_length=1, max_length=160)
    reasoning_effort: str = Field(min_length=1, max_length=40)
    timeout_seconds: int = Field(default=30, ge=1, le=900)
    max_output_tokens: int = Field(default=4000, ge=0)
    estimated_input_tokens: int = Field(default=0, ge=0)
    estimated_output_tokens: int = Field(default=0, ge=0)


class ModelProfileRegistry(BaseModel):
    model_profiles: dict[str, ModelProfile] = Field(default_factory=dict)

    @field_validator("model_profiles")
    @classmethod
    def profile_ids_are_stable(cls, value: dict[str, ModelProfile]) -> dict[str, ModelProfile]:
        required = {"economical", "standard", "deep"}
        missing = required - set(value)
        if missing:
            raise ValueError(f"missing required model profiles: {', '.join(sorted(missing))}")
        if any(not profile_id.replace("-", "").replace("_", "").isalnum() for profile_id in value):
            raise ValueError("model profile IDs must be simple stable identifiers")
        return value


class RoutingPolicy(BaseModel):
    allowed_profile_ids: list[str] = Field(default_factory=lambda: ["economical", "standard", "deep"])
    allow_budget_downgrade: bool = False
    max_escalation_level: int = Field(default=2, ge=0, le=2)


class RoutingRequest(BaseModel):
    role: RoutingRole
    task_type: str = Field(min_length=1, max_length=120)
    task_complexity: TaskComplexity = TaskComplexity.NORMAL
    previous_attempt_count: int = Field(default=0, ge=0)
    previous_failure_type: FailureType | None = None
    context_size: int = Field(default=0, ge=0)
    remaining_role_input_tokens: int = Field(default=0, ge=0)
    remaining_role_output_tokens: int = Field(default=0, ge=0)
    remaining_day_input_tokens: int = Field(default=0, ge=0)
    remaining_day_output_tokens: int = Field(default=0, ge=0)
    plan_policy: RoutingPolicy = Field(default_factory=RoutingPolicy)


class RoutingDecision(BaseModel):
    outcome: str = Field(pattern="^(SELECTED|HUMAN_REVIEW)$")
    role: RoutingRole
    profile_id: str | None = None
    provider: str | None = None
    model: str | None = None
    reasoning_effort: str | None = None
    timeout_seconds: int | None = None
    max_output_tokens: int | None = None
    selection_reason: str = Field(min_length=1, max_length=1000)
    escalation_level: int = Field(default=0, ge=0, le=2)
    escalation_reason: str | None = Field(default=None, max_length=1000)
    context_size: int = Field(default=0, ge=0)


class ProfileTokenUsage(BaseModel):
    gross_input_tokens: int = Field(default=0, ge=0)
    cached_input_tokens: int = Field(default=0, ge=0)
    uncached_input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    call_count: int = Field(default=0, ge=0)
    duration_ms: float = Field(default=0, ge=0)
