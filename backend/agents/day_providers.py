"""Isolated, typed Architect and Evaluator providers for Day orchestration."""

import json
import os
import re
from time import monotonic
from typing import Any, Callable, Protocol

from pydantic import BaseModel

from backend.models.day import ArchitectDecision, ArchitectProviderOutput, EvaluatorProviderOutput, SemanticEvaluation
from backend.models.model_routing import ProviderExecutionConfig
from backend.models.orchestration import ProviderSettings
from backend.models.result import TokenUsage


class ProviderConfigurationError(RuntimeError):
    pass


class ProviderRequestError(RuntimeError):
    """A sanitized provider failure safe to persist in Human Review."""

    def __init__(self, code: str, message: str, *, diagnostics: dict[str, object] | None = None) -> None:
        super().__init__(code)
        self.code = code
        self.safe_message = message
        self.diagnostics = diagnostics or {}


class ProviderTimeoutError(ProviderRequestError):
    pass


class DayArchitect(Protocol):
    def choose(self, request: dict[str, Any], execution: ProviderExecutionConfig) -> ArchitectDecision: ...


class DayEvaluator(Protocol):
    def evaluate(self, request: dict[str, Any], execution: ProviderExecutionConfig) -> SemanticEvaluation: ...


class MockDayArchitect:
    def choose(self, request: dict[str, Any], execution: ProviderExecutionConfig) -> ArchitectDecision:
        eligible = request.get("eligible_tasks", [])
        task_id = eligible[0]["task_id"] if eligible else None
        return ArchitectDecision(
            decision="RUN_TASK" if task_id else "DAY_COMPLETE", task_id=task_id,
            reason="first trusted eligible queue item", diagnostics={"provider": "mock", "execution": execution.model_dump(mode="json")},
        )


class MockSemanticEvaluator:
    """Deterministic fake used only by tests and explicit mock plans."""

    def __init__(self, decisions: dict[str, SemanticEvaluation] | None = None) -> None:
        self.decisions = decisions or {}

    def evaluate(self, request: dict[str, Any], execution: ProviderExecutionConfig) -> SemanticEvaluation:
        task_id = str(request["task_id"])
        metrics = request.get("rubric", {}).get("metrics", [])
        result = self.decisions.get(task_id, SemanticEvaluation(decision="PASS", reason="mock semantic pass", metrics={metric: 5.0 for metric in metrics}))
        return result.model_copy(update={"diagnostics": {"provider": "mock", "execution": execution.model_dump(mode="json")}})


class _OpenAIStructuredProvider:
    """Lazy SDK client: app startup remains safe without credentials or SDK use."""

    provider_name = "openai"

    def __init__(self, settings: ProviderSettings | None = None, *, client_factory: Callable[..., Any] | None = None) -> None:
        self.settings = settings or ProviderSettings(provider="openai")
        self.client_factory = client_factory

    def _client(self, execution: ProviderExecutionConfig) -> Any:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key or not execution.model or not execution.reasoning_effort or not execution.timeout_seconds:
            raise ProviderConfigurationError("OPENAI_API_KEY and a routed OpenAI execution configuration are required")
        if execution.provider != self.provider_name:
            raise ProviderConfigurationError("routed provider does not match OpenAI provider")
        if self.client_factory:
            return self.client_factory(api_key=api_key, timeout=execution.timeout_seconds, max_retries=0)
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise ProviderConfigurationError("OpenAI Python SDK is not installed") from exc
        return OpenAI(api_key=api_key, timeout=execution.timeout_seconds, max_retries=0)

    def _request(self, *, instructions: str, payload: dict[str, Any], output_type: type[BaseModel], execution: ProviderExecutionConfig) -> tuple[BaseModel, TokenUsage, dict[str, object]]:
        started = monotonic()
        client = self._client(execution)
        last_error: Exception | None = None
        schema = strict_provider_schema(output_type)
        for attempt in range(self.settings.max_transient_retries + 1):
            try:
                response = client.responses.create(
                    model=execution.model,
                    reasoning={"effort": execution.reasoning_effort},
                    max_output_tokens=execution.max_output_tokens,
                    store=False,
                    instructions=instructions,
                    input=json.dumps(payload, ensure_ascii=False),
                    text={"format": {"type": "json_schema", "name": output_type.__name__.lower(), "strict": True, "schema": schema}},
                )
                output_text = _read(response, "output_text")
                if not isinstance(output_text, str):
                    raise ProviderRequestError("OPENAI_INVALID_STRUCTURED_OUTPUT", "provider returned no structured output", diagnostics={"provider_error_type": "MissingOutput", "request_stage": "structured_output"})
                parsed = output_type.model_validate(json.loads(output_text))
                usage = _token_usage(_read(response, "usage"))
                return parsed, usage, {
                    "provider": self.provider_name, "profile_id": execution.profile_id,
                    "model": execution.model, "reasoning_effort": execution.reasoning_effort,
                    "timeout_seconds": execution.timeout_seconds, "max_output_tokens": execution.max_output_tokens,
                    "duration_ms": round((monotonic() - started) * 1000, 2), "attempts": attempt + 1,
                    "success": True, "request_stage": "responses.create",
                }
            except (json.JSONDecodeError, ValueError) as exc:
                raise ProviderRequestError(
                    "OPENAI_INVALID_STRUCTURED_OUTPUT", "provider returned invalid structured output",
                    diagnostics={"provider_error_type": type(exc).__name__, "request_stage": "structured_output"},
                ) from exc
            except ProviderRequestError:
                raise
            except Exception as exc:  # SDK exceptions are normalized at this boundary.
                last_error = exc
                if not _is_transient(exc) or attempt >= self.settings.max_transient_retries:
                    error = _sanitize_openai_error(exc, stage="responses.create")
                    if error.code == "OPENAI_TIMEOUT":
                        raise ProviderTimeoutError(error.code, error.safe_message, diagnostics=error.diagnostics) from exc
                    raise error from exc
        raise ProviderRequestError("OPENAI_REQUEST_FAILED", "provider request failed") from last_error


class OpenAIDayArchitect(_OpenAIStructuredProvider):
    def choose(self, request: dict[str, Any], execution: ProviderExecutionConfig) -> ArchitectDecision:
        output, usage, diagnostics = self._request(
            instructions="Choose only from eligible configured task IDs. Do not create tasks, commands, paths, budgets, or acceptance criteria.",
            payload=request, output_type=ArchitectProviderOutput, execution=execution,
        )
        return ArchitectDecision.model_validate({**output.model_dump(), "token_usage": usage, "diagnostics": diagnostics})


class OpenAISemanticEvaluator(_OpenAIStructuredProvider):
    def evaluate(self, request: dict[str, Any], execution: ProviderExecutionConfig) -> SemanticEvaluation:
        output, usage, diagnostics = self._request(
            instructions="Evaluate only the supplied bounded evidence and trusted rubric. Return no commands, paths, or replacement acceptance criteria.",
            payload=request, output_type=EvaluatorProviderOutput, execution=execution,
        )
        assert isinstance(output, EvaluatorProviderOutput)
        allowed_metrics = set(request.get("rubric", {}).get("metrics", []))
        metrics = {metric.name: metric.score for metric in output.metrics}
        if len(metrics) != len(output.metrics) or not set(metrics).issubset(allowed_metrics):
            raise ProviderRequestError(
                "OPENAI_INVALID_STRUCTURED_OUTPUT", "provider returned unsupported evaluation metrics",
                diagnostics={"provider_error_type": "MetricValidation", "request_stage": "structured_output"},
            )
        result = SemanticEvaluation.model_validate({
            **output.model_dump(exclude={"metrics"}), "metrics": metrics,
            "token_usage": usage, "diagnostics": diagnostics,
        })
        if result.repair_instruction and (len(result.repair_instruction) > 1000 or "\n" in result.repair_instruction or re.search(r"(?i)(\\\\|/|--|\\b(?:python|powershell|cmd|git)\\b|\\.py\\b)", result.repair_instruction)):
            raise ProviderRequestError(
                "OPENAI_INVALID_STRUCTURED_OUTPUT",
                "repair instruction exceeds bounded plain-text policy",
                diagnostics={
                    "provider_error_type": "RepairInstructionPolicy",
                    "request_stage": "structured_output",
                },
            )
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


def strict_provider_schema(output_type: type[BaseModel]) -> dict[str, Any]:
    """Return an API-safe strict Structured Outputs schema or fail before I/O."""
    schema = output_type.model_json_schema()
    validate_strict_provider_schema(schema)
    return schema


def validate_strict_provider_schema(schema: dict[str, Any]) -> None:
    """Validate the OpenAI strict-schema subset relied on by provider DTOs."""
    if schema.get("type") != "object" or "anyOf" in schema:
        raise ValueError("strict provider schema root must be an object without anyOf")
    definitions = schema.get("$defs", {})
    if not isinstance(definitions, dict):
        raise ValueError("strict provider schema definitions must be an object")
    _validate_schema_node(schema, definitions, "$")
    for name, definition in definitions.items():
        if not isinstance(definition, dict):
            raise ValueError(f"strict provider schema definition {name} must be an object")
        _validate_schema_node(definition, definitions, f"$defs.{name}")


def _validate_schema_node(node: dict[str, Any], definitions: dict[str, Any], path: str) -> None:
    supported = {"$ref", "additionalProperties", "anyOf", "description", "enum", "items", "properties", "required", "title", "type", "$defs"}
    unsupported = set(node) - supported
    if unsupported:
        raise ValueError(f"strict provider schema has unsupported keywords at {path}: {', '.join(sorted(unsupported))}")
    if "$ref" in node:
        reference = node["$ref"]
        if not isinstance(reference, str) or not reference.startswith("#/$defs/") or reference.removeprefix("#/$defs/") not in definitions:
            raise ValueError(f"strict provider schema has unsupported reference at {path}")
        return
    if node.get("type") == "object" or "properties" in node:
        properties = node.get("properties")
        if not isinstance(properties, dict) or node.get("additionalProperties") is not False:
            raise ValueError(f"strict provider schema object must forbid additional properties at {path}")
        if set(node.get("required", [])) != set(properties):
            raise ValueError(f"strict provider schema requires every property at {path}")
        for name, child in properties.items():
            if not isinstance(child, dict):
                raise ValueError(f"strict provider schema property must be a schema at {path}.{name}")
            _validate_schema_node(child, definitions, f"{path}.{name}")
    if node.get("type") == "array":
        items = node.get("items")
        if not isinstance(items, dict):
            raise ValueError(f"strict provider schema array items must be a schema at {path}")
        _validate_schema_node(items, definitions, f"{path}[]")
    if "anyOf" in node:
        variants = node["anyOf"]
        if not isinstance(variants, list) or not variants:
            raise ValueError(f"strict provider schema anyOf must be non-empty at {path}")
        for index, variant in enumerate(variants):
            if not isinstance(variant, dict):
                raise ValueError(f"strict provider schema anyOf member must be a schema at {path}[{index}]")
            _validate_schema_node(variant, definitions, f"{path}[{index}]")


def _sanitize_openai_error(exc: Exception, *, stage: str) -> ProviderRequestError:
    status = getattr(exc, "status_code", getattr(exc, "status", None))
    api_code = getattr(exc, "code", None)
    error_type = type(exc).__name__
    raw_message = (str(exc).splitlines() or [""])[0][:240]
    lowered = f"{error_type} {api_code or ''} {raw_message}".lower()
    if "timeout" in lowered:
        code, message = "OPENAI_TIMEOUT", "OpenAI request timed out"
    elif "quota" in lowered or "insufficient_quota" in lowered:
        code, message = "OPENAI_QUOTA", "OpenAI quota is unavailable"
    elif "rate" in lowered or status == 429:
        code, message = "OPENAI_RATE_LIMIT", "OpenAI rate limit reached"
    elif "schema" in lowered or "json_schema" in lowered or "invalid_json" in lowered:
        code, message = "OPENAI_SCHEMA_INVALID", "OpenAI rejected the structured output schema"
    elif "permission" in lowered or status == 403 or "model" in lowered and status in {400, 404}:
        code, message = "OPENAI_MODEL_ACCESS", "OpenAI model access was rejected"
    elif status == 400 or "badrequest" in lowered:
        code, message = "OPENAI_BAD_REQUEST", "OpenAI rejected the request"
    else:
        code, message = "OPENAI_REQUEST_FAILED", "OpenAI request failed"
    diagnostics: dict[str, object] = {"provider_error_type": error_type, "request_stage": stage}
    if isinstance(status, int):
        diagnostics["http_status"] = status
    if isinstance(api_code, str) and api_code:
        diagnostics["api_error_code"] = api_code[:80]
    if raw_message:
        redacted = re.sub(r"(?i)bearer\s+\S+", "Bearer [redacted]", raw_message)
        diagnostics["safe_message"] = re.sub(r"(?i)(api[_-]?key\s*[=:]\s*)\S+", r"\1[redacted]", redacted)
    return ProviderRequestError(code, message, diagnostics=diagnostics)
