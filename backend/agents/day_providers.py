"""Small, structured role providers for autonomous-day orchestration.

The OpenAI implementations are deliberately opt-in: construction and tests do
not access the network, and a missing API key fails closed before a request.
"""

import json
import os
from typing import Any, Protocol
from urllib.error import URLError
from urllib.request import Request, urlopen

from backend.models.day import ArchitectDecision, QueuedTask, SemanticEvaluation
from backend.models.result import TokenUsage


class DayArchitect(Protocol):
    def choose(self, queue: list[QueuedTask]) -> ArchitectDecision: ...


class DayEvaluator(Protocol):
    def evaluate(self, *, task_id: str, metrics: list[str], result: dict[str, Any]) -> SemanticEvaluation: ...


class MockDayArchitect:
    def choose(self, queue: list[QueuedTask]) -> ArchitectDecision:
        candidate = next((item for item in queue if item.state.value in {"PENDING", "READY", "REPAIR_PENDING"}), None)
        return ArchitectDecision(task_id=candidate.task_id if candidate else None, reason="first trusted ready queue item")


class MockSemanticEvaluator:
    """Deterministic fake used only by tests and explicit mock plans."""

    def __init__(self, decisions: dict[str, SemanticEvaluation] | None = None) -> None:
        self.decisions = decisions or {}

    def evaluate(self, *, task_id: str, metrics: list[str], result: dict[str, Any]) -> SemanticEvaluation:
        return self.decisions.get(task_id, SemanticEvaluation(decision="PASS", score={metric: 5.0 for metric in metrics}))


class OpenAIProviderNotConfigured(RuntimeError):
    pass


class _OpenAIStructuredProvider:
    def __init__(self, *, model: str | None = None, api_key: str | None = None) -> None:
        self.model = model or os.environ.get("OPENAI_DAY_MODEL")
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")

    def _request(self, instructions: str, payload: dict[str, Any], schema_name: str, schema: dict[str, Any]) -> tuple[dict[str, Any], TokenUsage]:
        if not self.api_key or not self.model:
            raise OpenAIProviderNotConfigured("OPENAI_API_KEY and OPENAI_DAY_MODEL are required for the opt-in provider")
        request_body = {
            "model": self.model,
            "store": False,
            "instructions": instructions,
            "input": json.dumps(payload, ensure_ascii=False),
            "text": {"format": {"type": "json_schema", "name": schema_name, "strict": True, "schema": schema}},
        }
        request = Request(
            "https://api.openai.com/v1/responses",
            data=json.dumps(request_body).encode("utf-8"),
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=30) as response:  # nosec B310 - fixed HTTPS endpoint
                decoded = json.loads(response.read().decode("utf-8"))
        except (OSError, URLError, ValueError) as exc:
            raise RuntimeError("OpenAI structured provider request failed") from exc
        if decoded.get("status") != "completed":
            raise RuntimeError("OpenAI structured provider returned a non-completed response")
        output_text = decoded.get("output_text")
        if not isinstance(output_text, str):
            raise RuntimeError("OpenAI structured provider returned no structured text")
        usage = decoded.get("usage") or {}
        cached = (usage.get("input_tokens_details") or {}).get("cached_tokens", 0)
        return json.loads(output_text), TokenUsage(
            input_tokens=int(usage.get("input_tokens", 0)), cached_input_tokens=int(cached),
            output_tokens=int(usage.get("output_tokens", 0)), available=bool(usage),
        )


class OpenAIDayArchitect(_OpenAIStructuredProvider):
    def choose(self, queue: list[QueuedTask]) -> ArchitectDecision:
        payload, usage = self._request(
            "Select exactly one trusted queue task_id, or null when no task is eligible. Do not plan or execute work.",
            {"queue": [{"task_id": item.task_id, "state": item.state.value} for item in queue]},
            "architect_decision",
            {"type": "object", "additionalProperties": False, "properties": {"task_id": {"type": ["string", "null"]}, "reason": {"type": "string"}}, "required": ["task_id", "reason"]},
        )
        return ArchitectDecision.model_validate({**payload, "token_usage": usage})


class OpenAISemanticEvaluator(_OpenAIStructuredProvider):
    def evaluate(self, *, task_id: str, metrics: list[str], result: dict[str, Any]) -> SemanticEvaluation:
        payload, usage = self._request(
            "Evaluate only the supplied bounded result against the named metrics. Return PASS, REPAIR, or HUMAN_REVIEW.",
            {"task_id": task_id, "metrics": metrics, "result": result},
            "semantic_evaluation",
            {"type": "object", "additionalProperties": False, "properties": {"decision": {"type": "string", "enum": ["PASS", "REPAIR", "HUMAN_REVIEW"]}, "score": {"type": "object", "additionalProperties": {"type": "number"}}, "blocking_issues": {"type": "array", "items": {"type": "string"}}, "repair_instruction": {"type": ["string", "null"]}}, "required": ["decision", "score", "blocking_issues", "repair_instruction"]},
        )
        return SemanticEvaluation.model_validate({**payload, "token_usage": usage})
