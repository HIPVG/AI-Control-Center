from collections import deque
from pathlib import Path

import pytest

from backend.agents.day_providers import MockSemanticEvaluator, OpenAIDayArchitect, OpenAIProviderNotConfigured
from backend.control.tasks import ConfiguredTask, TaskCommand, TaskRegistry
from backend.control.plans import load_plan_registry
from backend.models.day import DayPlan, DayPlanRegistry, DayRunSnapshot, DayRunState, QueueTaskState, SemanticEvaluation
from backend.models.runtime import CodexAttemptResult
from backend.models.task import TaskType
from backend.orchestrator.day_runner import DayRunner


def task(task_id: str, *, semantic: bool = False, requires_codex: bool = False) -> ConfiguredTask:
    return ConfiguredTask(
        task_id=task_id, project_id="test", title=task_id, task_type=TaskType.CODE_FIX,
        precheck=TaskCommand(argv=["python", "-c", "pass"]), postcheck=TaskCommand(argv=["python", "-c", "pass"]),
        allowed_files=["src/example.py"], context_files=["src/example.py"], requires_codex=requires_codex,
        evaluator_type="semantic" if semantic else "deterministic", evaluation_metrics=["groundedness"] if semantic else [],
    )


def runner_for(tasks: list[ConfiguredTask], execute, *, evaluator=None, max_repair=1, saved=None, persisted=None) -> DayRunner:
    plan = DayPlan(
        plan_id="mock-day", title="Mock Day", task_ids=[item.task_id for item in tasks],
        max_codex_calls=3, max_architect_calls=5, max_evaluator_calls=5, max_repair_loops_per_task=max_repair,
    )
    return DayRunner(
        DayPlanRegistry(plans={plan.plan_id: plan}), TaskRegistry(tasks={item.task_id: item for item in tasks}), execute,
        evaluators={"mock": evaluator or MockSemanticEvaluator()}, saved=saved,
        persist=(lambda state: persisted.append(state)) if persisted is not None else None,
    )


def test_mock_day_a_deterministic_no_change_skips_evaluator_and_persists_queue():
    calls = []
    persisted = []

    def execute(task_id, **kwargs):
        calls.append((task_id, kwargs))
        return {"task_id": task_id, "final_result": "COMPLETE_NO_CHANGE", "codex_attempts": [], "codex_invoked": False}

    day = runner_for([task("A")], execute, persisted=persisted)
    result = day.start("mock-day")
    assert result["state"] == "COMPLETE"
    assert result["queue"][0]["state"] == "COMPLETE_NO_CHANGE"
    assert result["evaluator_calls"] == 0
    assert result["codex_calls"] == 0
    assert calls[0][1]["max_codex_attempts"] == 3
    assert persisted[-1]["queue"][0]["state"] == "COMPLETE_NO_CHANGE"


def test_mock_day_b_records_mocked_codex_repair_and_postcheck_pass_without_evaluator():
    def execute(task_id, **kwargs):
        return {
            "task_id": task_id, "final_result": "COMPLETE", "precheck_result": "FAIL", "postcheck_result": "PASS",
            "codex_invoked": True, "codex_attempts": [CodexAttemptResult(attempt=1).model_dump()],
            "gross_input_tokens": 11, "cached_input_tokens": 3, "output_tokens": 4,
        }

    result = runner_for([task("B", requires_codex=True)], execute).start("mock-day")
    assert result["state"] == "COMPLETE"
    assert result["queue"][0]["state"] == "PASS"
    assert result["codex_calls"] == 1
    assert result["evaluator_calls"] == 0
    assert result["token_usage"]["codex"]["input_tokens"] == 11


def test_mock_day_c_semantic_repair_is_bounded_and_instruction_is_structured():
    decisions = deque([
        SemanticEvaluation(decision="REPAIR", repair_instruction="Repair only the bounded semantic issue."),
        SemanticEvaluation(decision="PASS", score={"groundedness": 4.9}),
    ])

    class Evaluator:
        def evaluate(self, **kwargs):
            return decisions.popleft()

    calls = []

    def execute(task_id, **kwargs):
        calls.append(kwargs)
        return {"task_id": task_id, "final_result": "COMPLETE", "codex_attempts": [], "codex_invoked": False}

    result = runner_for([task("C", semantic=True)], execute, evaluator=Evaluator()).start("mock-day")
    assert result["state"] == "COMPLETE"
    assert result["queue"][0]["state"] == "PASS"
    assert result["queue"][0]["repair_loops"] == 1
    assert result["evaluator_calls"] == 2
    assert calls[1]["repair_instruction"] == "Repair only the bounded semantic issue."


def test_semantic_repair_limit_routes_to_human_review():
    def execute(task_id, **kwargs):
        return {"task_id": task_id, "final_result": "COMPLETE", "codex_attempts": []}

    evaluator = MockSemanticEvaluator({"C": SemanticEvaluation(decision="REPAIR", repair_instruction="bounded")})
    result = runner_for([task("C", semantic=True)], execute, evaluator=evaluator, max_repair=0).start("mock-day")
    assert result["state"] == "HUMAN_REVIEW"
    assert result["human_review_queue"][0]["task_id"] == "C"


def test_continuous_mode_is_rejected_and_interrupted_run_requires_resume():
    def execute(task_id, **kwargs):
        return {"task_id": task_id, "final_result": "COMPLETE_NO_CHANGE", "codex_attempts": []}

    day = runner_for([task("A")], execute, saved=DayRunSnapshot(plan_id="mock-day", state=DayRunState.RUNNING).model_dump(mode="json"))
    assert day.view()["state"] == "PAUSED"
    assert day.step(single_step=False)["error_code"] == "CONTINUOUS_MODE_NOT_SUPPORTED"
    assert day.resume()["state"] == "COMPLETE"


def test_resume_advances_exactly_one_next_queue_item_for_a_multi_task_plan():
    calls = []

    def execute(task_id, **kwargs):
        calls.append(task_id)
        return {"task_id": task_id, "final_result": "COMPLETE_NO_CHANGE", "codex_attempts": []}

    day = runner_for([task("A"), task("B")], execute)
    first = day.start("mock-day")
    assert first["state"] == "RUNNING"
    assert [item["state"] for item in first["queue"]] == ["COMPLETE_NO_CHANGE", "PENDING"]
    assert day.resume()["state"] == "COMPLETE"
    assert calls == ["A", "B"]


def test_openai_provider_fails_closed_without_opt_in_credentials(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_DAY_MODEL", raising=False)
    with pytest.raises(OpenAIProviderNotConfigured):
        OpenAIDayArchitect().choose([])


def test_mock_plan_fixture_is_single_step_and_disables_continuous_mode():
    plan = load_plan_registry(Path(__file__).parent / "fixtures" / "mock_day_plan.yaml").get("mock-day")
    assert plan is not None
    assert plan.single_step_default is True
    assert plan.continuous_mode_supported is False
