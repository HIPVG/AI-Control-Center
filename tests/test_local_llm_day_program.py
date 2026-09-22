from pathlib import Path

from backend.control.local_llm_day_program import LocalLLMDayProgram
from backend.models.local_llm_day import LocalLLMDayState


def _runner() -> LocalLLMDayProgram:
    runner = LocalLLMDayProgram(Path("C:/trusted-local-llm"))
    runner._objectives = lambda: {day: f"Objective {day}" for day in range(1, 15)}
    runner._inspect_repository = lambda: {
        "status": "", "branch": "main", "head": "trusted-head", "origin": "https://example.invalid/local-llm.git", "staged_count": 0,
    }
    runner._run = lambda _arguments: 0
    runner._missing_docs = lambda: []
    return runner


def test_day_one_completes_a_clean_trusted_baseline():
    runner = _runner()
    assert [item["day"] for item in runner.days()] == list(range(1, 15))
    assert runner.start(1)["state"] == "RUNNING"
    runner.join(5)
    result = runner.view()
    assert result["state"] == LocalLLMDayState.COMPLETE.value
    assert result["report"]["result"] == "DAY_COMPLETE"
    assert result["report"]["evidence"]["tests_exit_code"] == 0
    assert result["report"]["evidence"]["working_tree_clean"] is True


def test_another_day_is_selectable_from_the_runbook_without_python_changes():
    runner = _runner()
    assert runner.start(14)["objective"] == "Objective 14"
    runner.join(5)
    result = runner.view()
    assert result["state"] == LocalLLMDayState.FAILED.value
    assert result["report"]["result"] == "NO_TRUSTED_DAY_ACTION"


def test_repair_and_go_restarts_only_a_failed_test_day():
    runner = _runner()
    runner._run = lambda _arguments: 1
    runner.start(1)
    runner.join(5)
    assert runner.view()["report"]["result"] == "TEST_FAILURE"
    runner._run = lambda _arguments: 0
    assert runner.repair_and_go()["state"] == "RUNNING"
    runner.join(5)
    assert runner.view()["report"]["result"] == "DAY_COMPLETE"
