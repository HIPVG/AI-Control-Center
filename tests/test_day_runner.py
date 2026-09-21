from pathlib import Path

import pytest

from backend.agents.day_providers import MockDayArchitect, MockSemanticEvaluator, OpenAIDayArchitect, OpenAISemanticEvaluator, ProviderConfigurationError, ProviderTimeoutError
from backend.control.plans import load_plan_registry
from backend.control.orchestration import load_orchestration_config
from backend.control.tasks import ConfiguredTask, TaskCommand, TaskRegistry
from backend.models.day import DayExecutionMode, DayPlan, DayPlanRegistry, DayRunSnapshot, DayRunState, QueuedTask, SemanticEvaluation
from backend.models.orchestration import ProviderBudget, ProviderSettings
from backend.models.model_routing import ProviderExecutionConfig
from backend.models.runtime import CodexAttemptResult
from backend.models.task import TaskType
from backend.orchestrator.day_runner import DayRunner


def configured_task(task_id: str, *, semantic: bool = False, requires_codex: bool = False) -> ConfiguredTask:
    return ConfiguredTask(task_id=task_id, project_id="test", title=task_id, task_type=TaskType.CODE_FIX, precheck=TaskCommand(argv=["python", "-c", "pass"]), postcheck=TaskCommand(argv=["python", "-c", "pass"]), allowed_files=["src/example.py"], context_files=["src/example.py"], requires_codex=requires_codex, evaluator_type="semantic" if semantic else "deterministic", evaluation_metrics=["groundedness"] if semantic else [])


def make_runner(tasks, execute, *, plan_kwargs=None, evaluators=None, provider_budgets=None, persisted=None, saved=None):
    plan_values = {"plan_id": "mock-day", "title": "Mock day", "task_ids": [task.task_id for task in tasks], "max_tasks_per_run": 10, "max_codex_calls": 5, "max_architect_calls": 10, "max_evaluator_calls": 10}
    plan_values.update(plan_kwargs or {})
    plan = DayPlan(**plan_values)
    return DayRunner(DayPlanRegistry(plans={plan.plan_id: plan}), TaskRegistry(tasks={task.task_id: task for task in tasks}), execute, evaluators=evaluators, provider_budgets=provider_budgets, saved=saved, persist=(lambda state: persisted.append(state)) if persisted is not None else None)


def complete_no_change(task_id, **kwargs):
    return {"run_id": f"run-{task_id}", "task_id": task_id, "final_result": "COMPLETE_NO_CHANGE", "codex_attempts": [], "codex_invoked": False, "precheck_result": "PASS"}


def test_multi_task_plan_loads_without_reinterpreting_historical_plan():
    plans = load_plan_registry(Path("config/plans.yaml"))
    assert plans.get("week1-day3-local-llm").task_ids == ["PC-001-A"]
    assert plans.get("week1-day3-local-llm-v2").task_ids == ["PC-001-A", "PC-001-C", "PC-002-A"]
    config = load_orchestration_config(Path("config/orchestration.yaml"))
    assert config.orchestration.architect.provider == "mock"
    assert config.orchestration.evaluator.provider == "mock"


def test_provider_environment_overrides_are_explicit_and_do_not_require_credentials(monkeypatch):
    monkeypatch.setenv("AI_CONTROL_CENTER_ARCHITECT_PROVIDER", "openai")
    monkeypatch.setenv("AI_CONTROL_CENTER_ARCHITECT_MODEL", "configured-test-model")
    config = load_orchestration_config(Path("config/orchestration.yaml"))
    assert config.orchestration.architect.provider == "openai"
    assert config.orchestration.architect.model == "configured-test-model"


def test_mock_provider_diagnostics_report_mock_without_a_model():
    execution = ProviderExecutionConfig(provider="mock")
    architect = MockDayArchitect().choose({"eligible_tasks": [{"task_id": "A"}]}, execution)
    evaluator = MockSemanticEvaluator().evaluate({"task_id": "A", "rubric": {"metrics": []}}, execution)
    assert architect.diagnostics["provider"] == evaluator.diagnostics["provider"] == "mock"
    assert architect.diagnostics["execution"]["model"] is None
    assert evaluator.diagnostics["execution"]["model"] is None


def test_single_step_pauses_after_first_task_then_completes_final_task_with_progress():
    calls = []

    def execute(task_id, **kwargs):
        calls.append(task_id)
        return complete_no_change(task_id, **kwargs)

    day = make_runner([configured_task("A"), configured_task("B")], execute)
    first = day.start("mock-day")
    assert first["state"] == "PAUSED"
    assert first["day_progress"] == 50
    assert first["overall_progress"] == 50
    second = day.resume()
    assert second["state"] == "COMPLETE"
    assert second["day_progress"] == 100
    assert calls == ["A", "B"]


def test_continuous_mode_processes_all_tasks_and_preserves_mode_for_resume():
    day = make_runner([configured_task("A"), configured_task("B"), configured_task("C")], complete_no_change)
    result = day.start("mock-day", mode=DayExecutionMode.CONTINUOUS)
    assert result["state"] == "COMPLETE"
    assert result["mode"] == "continuous"
    assert result["day_progress"] == 100


def test_continuous_human_review_and_hard_limits_stop_without_extra_task_execution():
    review = make_runner([configured_task("A")], lambda task_id, **kwargs: {"task_id": task_id, "final_result": "HUMAN_REVIEW", "codex_attempts": []})
    assert review.start("mock-day", mode=DayExecutionMode.CONTINUOUS)["state"] == "HUMAN_REVIEW"
    max_tasks = make_runner([configured_task("A"), configured_task("B")], complete_no_change, plan_kwargs={"max_tasks_per_run": 1})
    assert max_tasks.start("mock-day", mode=DayExecutionMode.CONTINUOUS)["stop_reason"] == "MAX_TASKS_PER_RUN_REACHED"
    max_architect = make_runner([configured_task("A")], complete_no_change, plan_kwargs={"max_architect_calls": 0})
    assert max_architect.start("mock-day", mode=DayExecutionMode.CONTINUOUS)["stop_reason"] == "MAX_ARCHITECT_CALLS_REACHED"
    max_codex = make_runner([configured_task("A", requires_codex=True)], complete_no_change, plan_kwargs={"max_codex_calls": 0})
    assert max_codex.start("mock-day", mode=DayExecutionMode.CONTINUOUS)["stop_reason"] == "MAX_CODEX_CALLS_REACHED"


def test_semantic_evaluator_is_called_only_after_deterministic_success_and_repair_is_bounded():
    requests = []

    class Evaluator:
        def evaluate(self, request, execution):
            requests.append(request)
            assert execution.provider == "mock"
            return SemanticEvaluation(decision="REPAIR" if len(requests) == 1 else "PASS", reason="repair", repair_instruction="Fix the bounded semantic issue.", metrics={"groundedness": 5.0})

    executions = []

    def execute(task_id, **kwargs):
        executions.append(kwargs)
        return {"task_id": task_id, "final_result": "COMPLETE", "precheck_result": "FAIL", "postcheck_result": "PASS", "scope_guard_result": "PASS", "codex_attempts": []}

    result = make_runner([configured_task("S", semantic=True)], execute, evaluators={"mock": Evaluator()}).start("mock-day")
    assert result["state"] == "COMPLETE"
    assert len(requests) == 2
    assert executions[1]["repair_instruction"] == "Fix the bounded semantic issue."
    assert "architect_history" not in requests[0]


def test_evaluator_cannot_override_deterministic_postcheck_failure():
    called = []

    class Evaluator:
        def evaluate(self, request, execution):
            called.append(request)
            return SemanticEvaluation(decision="PASS")

    result = make_runner([configured_task("S", semantic=True)], lambda task_id, **kwargs: {"task_id": task_id, "final_result": "COMPLETE", "postcheck_result": "FAIL", "scope_guard_result": "PASS", "codex_attempts": []}, evaluators={"mock": Evaluator()}).start("mock-day")
    assert result["state"] == "HUMAN_REVIEW"
    assert called == []


def test_provider_budget_precheck_stops_and_post_run_overage_warns_without_rewriting_success():
    stopped = make_runner([configured_task("A")], complete_no_change, provider_budgets={"architect": ProviderBudget(max_calls=0), "evaluator": ProviderBudget()})
    assert stopped.start("mock-day")["stop_reason"] == "ARCHITECT_BUDGET_GUARD"

    class Architect:
        def choose(self, request, execution):
            from backend.models.day import ArchitectDecision
            from backend.models.result import TokenUsage
            return ArchitectDecision(task_id="A", reason="test", token_usage=TokenUsage(input_tokens=10, output_tokens=1, available=True))

    overage = DayRunner(DayPlanRegistry(plans={"mock-day": DayPlan(plan_id="mock-day", title="x", task_ids=["A"])}), TaskRegistry(tasks={"A": configured_task("A")}), complete_no_change, architects={"mock": Architect()}, provider_budgets={"architect": ProviderBudget(daily_input_tokens=1, daily_output_tokens=1), "evaluator": ProviderBudget()})
    result = overage.start("mock-day")
    assert result["state"] == "COMPLETE"
    assert "ARCHITECT_POST_RUN_BUDGET_OVERAGE" in result["budget_warnings"]
    assert result["token_totals"]["day_total"] == 11


class FakeResponses:
    def __init__(self, outputs):
        self.outputs, self.calls = list(outputs), []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        item = self.outputs.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


class FakeClient:
    def __init__(self, responses):
        self.responses = responses


def test_openai_architect_and_evaluator_build_structured_sdk_requests_parse_usage_and_retry(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    architect_responses = FakeResponses([type("APITimeout", (Exception,), {})(), {"output_text": '{"decision":"RUN_TASK","task_id":"A","reason":"ok","priority":1}', "usage": {"input_tokens": 12, "input_tokens_details": {"cached_tokens": 3}, "output_tokens": 4}}])
    settings = ProviderSettings(provider="openai", model="ignored-test-model", max_transient_retries=1)
    execution = ProviderExecutionConfig(profile_id="standard", provider="openai", model="gpt-5.6-terra", reasoning_effort="medium", timeout_seconds=123, max_output_tokens=456)
    client_options = []
    architect = OpenAIDayArchitect(settings, client_factory=lambda **kwargs: client_options.append(kwargs) or FakeClient(architect_responses))
    decision = architect.choose({"plan_id": "p", "eligible_tasks": [{"task_id": "A"}]}, execution)
    assert decision.task_id == "A"
    assert decision.token_usage.cached_input_tokens == 3
    assert len(architect_responses.calls) == 2
    assert architect_responses.calls[0]["store"] is False
    assert "json_schema" == architect_responses.calls[0]["text"]["format"]["type"]
    assert architect_responses.calls[0]["model"] == "gpt-5.6-terra"
    assert architect_responses.calls[0]["reasoning"] == {"effort": "medium"}
    assert architect_responses.calls[0]["max_output_tokens"] == 456
    assert client_options == [{"api_key": "test-key", "timeout": 123, "max_retries": 0}]
    assert decision.diagnostics["model"] == "gpt-5.6-terra"
    assert decision.diagnostics["timeout_seconds"] == 123

    evaluator_responses = FakeResponses([{"output_text": '{"decision":"PASS","reason":"ok","metrics":{"groundedness":4.8},"blocking_issues":[],"repair_instruction":null}', "usage": {"input_tokens": 8, "output_tokens": 2}}])
    evaluation = OpenAISemanticEvaluator(settings, client_factory=lambda **kwargs: FakeClient(evaluator_responses)).evaluate({"task_id": "S", "rubric": {"metrics": ["groundedness"]}}, execution)
    assert evaluation.decision == "PASS"
    assert evaluation.metrics["groundedness"] == 4.8
    assert evaluation.diagnostics["reasoning_effort"] == "medium"


def test_openai_provider_fails_closed_without_credentials_and_exposes_typed_timeout(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    execution = ProviderExecutionConfig(provider="openai", model="gpt-5.6-terra", reasoning_effort="medium", timeout_seconds=30, max_output_tokens=100)
    with pytest.raises(ProviderConfigurationError):
        OpenAIDayArchitect(ProviderSettings(provider="openai", model="test")).choose({"eligible_tasks": []}, execution)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    responses = FakeResponses([type("APITimeout", (Exception,), {})()])
    with pytest.raises(ProviderTimeoutError):
        OpenAIDayArchitect(ProviderSettings(provider="openai", model="test", max_transient_retries=0), client_factory=lambda **kwargs: FakeClient(responses)).choose({"eligible_tasks": []}, execution)


def test_interrupted_state_pauses_and_persists_meaningful_transitions():
    persisted = []
    saved = DayRunSnapshot(plan_id="mock-day", state=DayRunState.RUNNING, queue=[QueuedTask(task_id="A")]).model_dump(mode="json")
    day = make_runner([configured_task("A")], complete_no_change, saved=saved, persisted=persisted)
    assert day.view()["state"] == "PAUSED"
    assert day.resume()["state"] == "COMPLETE"
    assert persisted[-1]["state"] == "COMPLETE"


def test_launchers_use_expected_port_and_reload_boundaries():
    development = Path("scripts/start_dev.ps1").read_text(encoding="utf-8")
    production = Path("scripts/start.ps1").read_text(encoding="utf-8")
    assert "--port $Port --reload" in development and "127.0.0.1" in development
    assert "--port $Port" in production and "--reload" not in production and "127.0.0.1" in production
