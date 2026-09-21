"""Trusted, deterministic selection of logical reasoning profiles."""

from backend.models.model_routing import (
    FailureType,
    ModelProfile,
    ModelProfileRegistry,
    ProfileTokenUsage,
    RoutingDecision,
    RoutingRequest,
    RoutingRole,
    TaskComplexity,
)
from backend.models.result import TokenUsage
from pathlib import Path


class ModelRouter:
    """Selects a profile only; it never changes authority or execution scope."""

    _ORDER = ("economical", "standard", "deep")
    _NON_ESCALATABLE = {
        FailureType.NETWORK,
        FailureType.MISSING_DEPENDENCY,
        FailureType.SANDBOX,
        FailureType.PERMISSION,
        FailureType.ENVIRONMENT,
        FailureType.INVALID_CONFIGURATION,
        FailureType.SCOPE_GUARD,
        FailureType.GIT_SAFETY,
    }

    def __init__(self, profiles: ModelProfileRegistry) -> None:
        self.profiles = profiles

    def select(self, request: RoutingRequest) -> RoutingDecision:
        profile_id, escalation_level, escalation_reason = self._preferred_profile(request)
        allowed = [profile_id for profile_id in request.plan_policy.allowed_profile_ids if profile_id in self.profiles.model_profiles]
        if profile_id not in allowed:
            return self._review(request, escalation_level, escalation_reason, "preferred profile is not allowed by trusted plan policy")
        if escalation_level > request.plan_policy.max_escalation_level:
            return self._review(request, escalation_level, escalation_reason, "maximum escalation level reached")
        profile = self.profiles.model_profiles[profile_id]
        if not self._within_budget(profile, request):
            lower = self._lower_profile(profile_id, allowed, request) if request.plan_policy.allow_budget_downgrade else None
            if lower is None:
                return self._review(request, escalation_level, escalation_reason, "selected profile exceeds remaining trusted budget")
            profile_id, profile = lower
            selection_reason = f"budget policy explicitly allowed downgrade to {profile_id}"
        else:
            selection_reason = self._selection_reason(request, profile_id, escalation_reason)
        if request.execution_provider == "mock":
            return RoutingDecision(
                outcome="SELECTED", role=request.role, profile_id=profile_id,
                provider="mock", selection_reason=selection_reason,
                escalation_level=escalation_level, escalation_reason=escalation_reason,
                context_size=request.context_size,
            )
        resolved = self._resolve_provider_profile(profile, request.execution_provider)
        if resolved is None:
            return self._review(
                request, escalation_level, escalation_reason,
                f"selected profile has no trusted mapping for execution provider {request.execution_provider}",
            )
        return RoutingDecision(
            outcome="SELECTED", role=request.role, profile_id=profile_id,
            provider=request.execution_provider, model=resolved.model, reasoning_effort=resolved.reasoning_effort,
            timeout_seconds=resolved.timeout_seconds, max_output_tokens=resolved.max_output_tokens,
            selection_reason=selection_reason, escalation_level=escalation_level,
            escalation_reason=escalation_reason, context_size=request.context_size,
        )

    @staticmethod
    def _resolve_provider_profile(profile: ModelProfile, execution_provider: str):
        if execution_provider == profile.provider:
            return profile
        return profile.provider_profiles.get(execution_provider)

    def _preferred_profile(self, request: RoutingRequest) -> tuple[str, int, str | None]:
        if request.role == RoutingRole.ARCHITECT:
            base = "economical" if request.task_complexity == TaskComplexity.SIMPLE else "standard"
        elif request.role == RoutingRole.EVALUATOR:
            base = "economical" if request.task_complexity == TaskComplexity.SIMPLE else "standard"
        else:
            base = {TaskComplexity.SIMPLE: "economical", TaskComplexity.NORMAL: "standard", TaskComplexity.COMPLEX: "deep"}[request.task_complexity]
        if request.task_complexity == TaskComplexity.COMPLEX:
            base = "deep"
        if request.previous_failure_type in self._NON_ESCALATABLE:
            return base, 0, f"{request.previous_failure_type.value} is not eligible for reasoning escalation"
        if request.previous_failure_type in {FailureType.REASONING, FailureType.UNKNOWN}:
            next_index = min(self._ORDER.index(base) + 1, len(self._ORDER) - 1)
            return self._ORDER[next_index], next_index, f"previous {request.previous_failure_type.value}"
        return base, self._ORDER.index(base), None

    def _within_budget(self, profile: ModelProfile, request: RoutingRequest) -> bool:
        return (
            profile.estimated_input_tokens <= request.remaining_role_input_tokens
            and profile.estimated_output_tokens <= request.remaining_role_output_tokens
            and profile.estimated_input_tokens <= request.remaining_day_input_tokens
            and profile.estimated_output_tokens <= request.remaining_day_output_tokens
        )

    def _lower_profile(self, selected: str, allowed: list[str], request: RoutingRequest) -> tuple[str, ModelProfile] | None:
        for profile_id in reversed(self._ORDER[:self._ORDER.index(selected)]):
            profile = self.profiles.model_profiles.get(profile_id)
            if profile_id in allowed and profile and self._within_budget(profile, request):
                return profile_id, profile
        return None

    def _selection_reason(self, request: RoutingRequest, profile_id: str, escalation_reason: str | None) -> str:
        if escalation_reason:
            return f"{escalation_reason}; selected lowest permitted sufficient profile {profile_id}"
        return f"{request.role.value} {request.task_complexity.value} task selected lowest permitted sufficient profile {profile_id}"

    def _review(self, request: RoutingRequest, level: int, reason: str | None, detail: str) -> RoutingDecision:
        return RoutingDecision(
            outcome="HUMAN_REVIEW", role=request.role, selection_reason=detail,
            escalation_level=level, escalation_reason=reason, context_size=request.context_size,
        )


def accumulate_profile_usage(current: ProfileTokenUsage, usage: TokenUsage, duration_ms: float = 0) -> ProfileTokenUsage:
    return ProfileTokenUsage(
        gross_input_tokens=current.gross_input_tokens + usage.gross_input_tokens,
        cached_input_tokens=current.cached_input_tokens + usage.cached_input_tokens,
        uncached_input_tokens=current.uncached_input_tokens + usage.uncached_input_tokens,
        output_tokens=current.output_tokens + usage.output_tokens,
        call_count=current.call_count + 1,
        duration_ms=current.duration_ms + max(duration_ms, 0),
    )


def load_model_profile_registry(path: Path) -> ModelProfileRegistry:
    """Load only trusted local profile configuration; invalid profiles fail closed."""
    import yaml

    return ModelProfileRegistry.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")) or {})
