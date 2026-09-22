from pathlib import Path

from backend.control.local_llm_day_program import LocalLLMDayProgram
from backend.models.local_llm_day import (
    DayIssueClassification,
    LocalLLMDayState,
    LocalLLMDayWorkItem,
    LocalLLMWorkItemState,
)


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "day-contract"


def test_pytest_temporary_directory_is_repository_owned(tmp_path):
    assert tmp_path.is_relative_to(Path(__file__).parents[1] / ".pytest-tmp")
    assert not str(tmp_path).lower().startswith("c:\\temp\\")


def _planner(contract, _inventory):
    return [
        LocalLLMDayWorkItem(
            item_id=f"codex-{contract.day}-{criterion_id}",
            title="Codex Architect bounded task",
            objective="Collect and verify one criterion.",
            kind="ENGINE_WORK_ORDER",
            engine_task_id="SAFE-FIXTURE",
            criterion_ids=[criterion_id],
        )
        for criterion_id in contract.remaining_gaps
    ][:3]


def _executor(work_order):
    return {
        "final_result": "COMPLETE",
        "evidence": {criterion_id: {"test": "passed", "artifact": f"safe/{criterion_id}"} for criterion_id in work_order["criterion_ids"]},
    }


def test_all_contracts_are_explicit_machine_readable_definitions():
    runner = LocalLLMDayProgram(FIXTURE_ROOT)
    assert [item["day"] for item in runner.days()] == list(range(1, 15))
    runner.smoke(6)
    contract = runner.view()["contract"]
    assert contract["title"] == "Temporal-state design"
    assert any("planned, actual, forecast" in item["statement"].lower() for item in contract["completion_criteria"])
    assert contract["constraints"]
    assert "docs/runbooks/work-plan-day1-14.md" in contract["authoritative_sources"]

    runner.smoke(10)
    performance = runner.view()["contract"]
    requirements = " ".join(item["statement"] for item in performance["completion_criteria"])
    assert "VRAM CPU and RAM" in requirements
    assert "prompt/input and output tokens" in requirements


def test_two_materially_different_days_use_the_same_generic_planner_and_executor():
    root = FIXTURE_ROOT
    for day in (2, 6):
        runner = LocalLLMDayProgram(root, planner=_planner, work_order_executor=_executor)
        runner.start(day)
        runner.join(3)
        result = runner.view()
        assert result["state"] == LocalLLMDayState.COMPLETE.value
        assert result["report"]["result"] == "DAY_COMPLETE"
        assert result["work_items"][0]["kind"] == "ENGINE_WORK_ORDER"


def test_completion_requires_criterion_evidence_not_task_terminal_state():
    runner = LocalLLMDayProgram(FIXTURE_ROOT)
    runner.start(2)
    runner.join(3)
    result = runner.view()
    assert result["state"] == LocalLLMDayState.FAILED.value
    assert result["report"]["result"] == "DAY_INSUFFICIENT_EVIDENCE"
    assert all(item["state"] == LocalLLMWorkItemState.COMPLETE.value for item in result["work_items"])
    assert result["contract"]["remaining_gaps"]
    assert result["replan_count"] == LocalLLMDayProgram.MAX_REPLANS


def test_existing_retained_day_two_evidence_is_used_without_rerunning_it(tmp_path):
    retained = tmp_path / "results" / "decision-reasoning-v0.4" / "DRAP-retained"
    retained.mkdir(parents=True)
    for name in ("manifest.json", "validation.jsonl", "action-gate-summary.json"):
        (retained / name).write_text("{}", encoding="utf-8")
    planned = []

    def planner(contract, _inventory):
        planned.extend(contract.remaining_gaps)
        return _planner(contract, _inventory)

    runner = LocalLLMDayProgram(tmp_path, planner=planner, work_order_executor=_executor)
    runner.start(2)
    runner.join(3)
    assert "d2-feasibility_gate" not in planned
    assert "d2-relevance_gate" not in planned
    assert "d2-deterministic_validation" not in planned
    existing = runner.view()["contract"]["completion_criteria"]
    assert next(item for item in existing if item["criterion_id"] == "d2-feasibility_gate")["evidence"]["mode"] == "existing_evidence"


def test_missing_evidence_triggers_replan_then_new_evidence_completes_day():
    calls = []

    def planner(contract, _inventory):
        calls.append(list(contract.remaining_gaps))
        return _planner(contract, _inventory)

    def executor(work_order):
        if len(calls) == 1:
            return {"final_result": "COMPLETE", "evidence": {}}
        return _executor(work_order)

    runner = LocalLLMDayProgram(FIXTURE_ROOT, planner=planner, work_order_executor=executor)
    runner.start(7)
    runner.join(3)
    result = runner.view()
    assert len(calls) == 2
    assert calls[0] == calls[1]
    assert result["replan_count"] == 2
    assert result["state"] == LocalLLMDayState.COMPLETE.value


def test_restart_pauses_and_resume_preserves_completed_work():
    saved = {}
    runner = LocalLLMDayProgram(FIXTURE_ROOT, planner=_planner, work_order_executor=_executor, persist=lambda value: saved.update(value))
    runner.start(2)
    runner.join(3)
    saved["state"] = "RUNNING"
    restarted = LocalLLMDayProgram(FIXTURE_ROOT, saved=saved, planner=_planner, work_order_executor=_executor)
    assert restarted.view()["state"] == LocalLLMDayState.PAUSED.value
    assert restarted.view()["contract"]["satisfied_criteria"]
    restarted.resume()
    restarted.join(3)
    assert restarted.view()["state"] == LocalLLMDayState.COMPLETE.value


def test_planner_cannot_expand_authority():
    def unsafe_planner(_contract, _inventory):
        return [LocalLLMDayWorkItem(item_id="unsafe", title="unsafe", objective="unsafe", kind="SHELL", criterion_ids=["not-a-criterion"])]

    runner = LocalLLMDayProgram(FIXTURE_ROOT, planner=unsafe_planner)
    runner.start(2)
    runner.join(3)
    assert runner.view()["report"]["result"] == "DAY_HARNESS_FAILURE"


def test_model_quality_finding_is_preserved_and_never_offers_repair():
    def model_finding(_work_order):
        return {"final_result": "FAILED", "issue_classification": "MODEL_QUALITY_FINDING", "failure_excerpt": "bad research answer"}

    runner = LocalLLMDayProgram(FIXTURE_ROOT, planner=_planner, work_order_executor=model_finding)
    runner.start(2)
    runner.join(3)
    result = runner.view()
    assert result["issue_classification"] == DayIssueClassification.MODEL_QUALITY_FINDING.value
    assert result["recommended_action"]["action_id"] != "REPAIR_AND_GO"


def test_repair_is_proposal_only_until_guarded_executor_accepts_it():
    class Proposal:
        diagnosis = "isolated harness defect"
        edits = ()

    class Builder:
        def propose(self, **_kwargs):
            return Proposal()

    def defect_executor(work_order):
        if work_order["kind"] == "ENGINE_WORK_ORDER":
            return {"final_result": "FAILED", "issue_classification": "IMPLEMENTATION_DEFECT", "failure_excerpt": "safe fixture failed"}
        assert work_order["kind"] == "LOCAL_LLM_COUNTERMEASURE"
        return {"final_result": "COMPLETE", "evidence": {}}

    runner = LocalLLMDayProgram(FIXTURE_ROOT, planner=_planner, work_order_executor=defect_executor, repair_builder=Builder())
    runner._bounded_repair_files = lambda _item: {"tests/safe.py": "assert False"}
    runner.start(2)
    runner.join(3)
    assert runner.view()["recommended_action"]["action_id"] == "REPAIR_AND_GO"
    repaired = runner.repair_and_go()
    assert repaired["repair_knowledge"][-1]["status"] == "CODEX_ACCEPTED"
    assert repaired["work_items"][0]["state"] == LocalLLMWorkItemState.COMPLETE.value
