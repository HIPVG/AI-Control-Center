"""Isolated, typed Architect and Evaluator providers for Day orchestration."""

import json
import os
import re
from time import monotonic
from typing import Any, Callable, Protocol

from backend.models.day import ArchitectDecision, SemanticEvaluation
from backend.models.orchestration import ProviderSettings
from backend.models.result import TokenUsage


class ProviderConfigurationError(RuntimeError):
    pass


class ProviderTimeoutError(RuntimeError):
    pass


class ProviderRequestError(RuntimeError):
    pass


class DayArchitect(Protocol):
    def choose(self, request: dict[str, Any]) -> ArchitectDecision: ...


class DayEvaluator(Protocol):
    def evaluate(self, request: dict[str, Any]) -> SemanticEvaluation: ...


class MockDayArchitect:
    def choose(self, request: dict[str, Any]) -> ArchitectDecision:
        eligible = request.get("eligible_tasks", [])
        task_id = eligible[0]["task_id"] if eligible else None
        return ArchitectDecision(decision="RUN_TASK" if task_id else "DAY_COMPLETE", task_id=task_id, reason="first trusted eligible queue item")


class MockSemanticEvaluator:
    """Deterministic fake used only by tests and explicit mock plans."""

    def __init__(self, decisions: dict[str, SemanticEvaluation] | None = None) -> None:
        self.decisions = decisions or {}

    def evaluate(self, request: dict[str, Any]) -> SemanticEvaluation:
        task_id = str(request["task_id"])
        metrics = request.get("rubric", {}).get("metrics", [])
        return self.decisions.get(task_id, SemanticEvaluation(decision="PASS", reason="mock semantic pass", metrics={metric: 5.0 for metric in metrics}))


class _OpenAIStructuredProvider:
    """Lazy SDK client: app startup remains safe without credentials or SDK use."""

    provider_name = "openai"

    def __init__(self, settings: ProviderSettings | None = None, *, client_factory: Callable[..., Any] | None = None) -> None:
        self.settings = settings or ProviderSettings(provider="openai")
        self.client_factory = client_factory

    def _client(self) -> Any:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key or not self.settings.model:
            raise ProviderConfigurationError("OPENAI_API_KEY and configured model are required")
        if self.client_factory:
            return self.client_factory(api_key=api_key, timeout=self.settings.timeout_seconds, max_retries=0)
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise ProviderConfigurationError("OpenAI Python SDK is not installed") from exc
        return OpenAI(api_key=api_key, timeout=self.settings.timeout_seconds, max_retries=0)

    def _request(self, *, instructions: str, payload: dict[str, Any], result_type: type[ArchitectDecision] | type[SemanticEvaluation]) -> tuple[dict[str, Any], TokenUsage, dict[str, object]]:
        started = monotonic()
        client = self._client()
        last_error: Exception | None = None
        for attempt in range(self.settings.max_transient_retries + 1):
            try:
                response = client.responses.create(
                    model=self.settings.model,
                    store=False,
                    instructions=instructions,
                    input=json.dumps(payload, ensure_ascii=False),
                    text={"format": {"type": "json_schema", "name": result_type.__name__.lower(), "strict": True, "schema": result_type.model_json_schema()}},
                )
                output_text = _read(response, "output_text")
                if not isinstance(output_text, str):
                    raise ProviderRequestError("provider returned no structured output")
                parsed = json.loads(output_text)
                usage = _token_usage(_read(response, "usage"))
                return parsed, usage, {"provider": self.provider_name, "model": self.settings.model, "duration_ms": round((monotonic() - started) * 1000, 2), "attempts": attempt + 1, "success": True}
            except (json.JSONDecodeError, ValueError) as exc:
                raise ProviderRequestError("provider returned invalid structured output") from exc
            except ProviderRequestError:
                raise
            except Exception as exc:  # SDK exceptions are normalized at this boundary.
                last_error = exc
                if not _is_transient(exc) or attempt >= self.settings.max_transient_retries:
                    if "timeout" in type(exc).__name__.lower():
                        raise ProviderTimeoutError("provider request timed out") from exc
                    raise ProviderRequestError("provider request failed") from exc
        raise ProviderRequestError("provider request failed") from last_error


class OpenAIDayArchitect(_OpenAIStructuredProvider):
    def choose(self, request: dict[str, Any]) -> ArchitectDecision:
        parsed, usage, diagnostics = self._request(
            instructions="Choose only from eligible configured task IDs. Do not create tasks, commands, paths, budgets, or acceptance criteria.",
            payload=request, result_type=ArchitectDecision,
        )
        return ArchitectDecision.model_validate({**parsed, "token_usage": usage, "diagnostics": diagnostics})


class OpenAISemanticEvaluator(_OpenAIStructuredProvider):
    def evaluate(self, request: dict[str, Any]) -> SemanticEvaluation:
        parsed, usage, diagnostics = self._request(
            instructions="Evaluate only the supplied bounded evidence and trusted rubric. Return no commands, paths, or replacement acceptance criteria.",
            payload=request, result_type=SemanticEvaluation,
        )
        result = SemanticEvaluation.model_validate({**parsed, "token_usage": usage, "diagnostics": diagnostics})
        if result.repair_instruction and (len(result.repair_instruction) > 1000 or "\n" in result.repair_instruction or re.search(r"(?i)(\\\\|/|--|\\b(?:python|powershell|cmd|git)\\b|\\.py\\b)", result.repair_instruction)):
            raise ProviderRequestError("repair instruction exceeds bounded plain-text policy")
        return result


def _read(value: Any, name: str) -> Any:
    return value.get(name) if isinstance(value, dict) else getattr(value, name, None)


def _token_usage(usage: Any) -> TokenUsage:
    details = _read(usage, "input_tokens_details") or {}
    cached = _read(details, "cached_tokens") or 0
    return TokenUsage(input_tokens=int(_read(usage, "input_tokens") or 0), cached_input_tokens=int(cached), output_tokens=int(_read(usage, "output_tokens") or 0), available=usage is not None)


def _is_transient(exc: Exception) -> bool:
    name = type(exc).__name__.lower()
    return any(token in name for token in ("timeout", "connection", "rate", "internalserver"))
