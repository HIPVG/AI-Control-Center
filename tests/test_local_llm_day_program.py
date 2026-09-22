import subprocess
import sys
from pathlib import Path

import pytest

from backend.control.local_llm_day_program import LocalLLMDayProgram
from backend.models.local_llm_day import DayIssueClassification, LocalLLMDayState, LocalLLMDayWorkItem, LocalLLMWorkItemState


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "day-contract"


def _record(name, value=None, *, passed=True, verified=True):
    return {"evidence_type": name, "value": value if value is not None else {"proof": name}, "source": f"deterministic:{name}", "verified": verified, "validation": {"passed": passed, "validator": f"deterministic:{name}"}}


def _value(name):
    shapes = {
        "git_head": {"branch": "main", "head": "a" * 40, "is_commit": True},
        "commit_ref": {"branch": "main", "head": "a" * 40, "is_commit": True},
        "origin_ref": {"origin_url": "file:///origin.git", "upstream_ref": "origin/main", "upstream_sha": "b" * 40},
        "status_audit": {key: [] for key in ("staged_tracked_paths", "unstaged_tracked_paths", "untracked_paths", "relevant_dirty_paths", "generated_paths")},
        "staging_audit": {"staged_paths": [], "staged_generated_paths": [], "generated_artifacts_not_staged": True},
        "documentation_check": {"checked_files": ["docs/README.md"], "checks": [{"name": "fixture", "passed": True}], "failures": []},
        "test_result": {"commands": [["python", "-m", "pytest"]], "exit_code": 0, "deterministic_only": True},
    }
    return shapes.get(name, {"proof": name})


def _valid_evidence(required):
    return {name: _record(name, _value(name)) for name in required}


def _planner(contract, _inventory):
    return [LocalLLMDayWorkItem(item_id=f"task-{criterion.criterion_id}", title="bounded task", objective=criterion.statement, kind="ENGINE_WORK_ORDER", engine_task_id="SAFE-FIXTURE", criterion_ids=[criterion.criterion_id]) for criterion in contract.completion_criteria if criterion.criterion_id in contract.remaining_gaps][:3]


def _valid_executor(work_order):
    required = [name for criterion in work_order["contract"]["completion_criteria"] if criterion["criterion_id"] in work_order["criterion_ids"] for name in criterion["required_evidence"]]
    return {"final_result": "COMPLETE", "evidence": _valid_evidence(required)}


def test_pytest_temporary_directory_is_repository_owned(tmp_path):
    assert tmp_path.is_relative_to(Path(__file__).parents[1] / ".pytest-tmp")


@pytest.mark.parametrize("day", [2, 6])
def test_generic_contract_requires_explicit_validated_evidence(day):
    runner = LocalLLMDayProgram(FIXTURE_ROOT, planner=_planner, work_order_executor=_valid_executor)
    runner.start(day)
    runner.join(3)
    assert runner.view()["state"] == LocalLLMDayState.COMPLETE.value


def test_completed_task_with_engine_tokens_does_not_satisfy_criterion():
    runner = LocalLLMDayProgram(FIXTURE_ROOT)
    runner.smoke(6)
    criterion = runner.snapshot.contract.completion_criteria[0]
    criterion.evidence = {"engine_task_id": "PC-001-A", "run_id": "run-1", "postcheck_result": "PASS"}
    runner._evaluate_contract(runner.snapshot.contract, {})
    assert not criterion.satisfied


def test_partial_unrelated_empty_and_unverified_evidence_fail_closed():
    runner = LocalLLMDayProgram(FIXTURE_ROOT)
    runner.smoke(2)
    criterion = next(value for value in runner.snapshot.contract.completion_criteria if value.criterion_id == "d2-deterministic_validation")
    criterion.evidence = {"test_result": _record("test_result", _value("test_result"))}
    runner._evaluate_contract(runner.snapshot.contract, {})
    assert not criterion.satisfied
    criterion.evidence = {"git_head": _record("git_head", _value("git_head")), "origin_ref": _record("origin_ref", _value("origin_ref"))}
    runner._evaluate_contract(runner.snapshot.contract, {})
    assert not criterion.satisfied
    criterion.evidence = {"architecture_check": _record("architecture_check", {}), "test_result": _record("test_result", _value("test_result"), verified=False)}
    runner._evaluate_contract(runner.snapshot.contract, {})
    assert not criterion.satisfied


def test_complete_typed_evidence_satisfies_only_matching_criterion():
    runner = LocalLLMDayProgram(FIXTURE_ROOT)
    runner.smoke(6)
    criterion = runner.snapshot.contract.completion_criteria[0]
    criterion.evidence = _valid_evidence(criterion.required_evidence)
    runner._evaluate_contract(runner.snapshot.contract, {})
    assert criterion.satisfied
    assert set(criterion.required_evidence).issubset(criterion.evidence)


def test_missing_evidence_triggers_bounded_replan_not_false_completion():
    calls = []

    def planner(contract, _inventory):
        calls.append(contract.remaining_gaps[:])
        return _planner(contract, _inventory)

    runner = LocalLLMDayProgram(FIXTURE_ROOT, planner=planner, work_order_executor=lambda _order: {"final_result": "COMPLETE", "evidence": {}})
    runner.start(7)
    runner.join(3)
    assert runner.view()["report"]["result"] == "DAY_INSUFFICIENT_EVIDENCE"
    assert len(calls) == LocalLLMDayProgram.MAX_REPLANS


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


def test_static_process_tasks_cannot_supply_day_one_evidence():
    calls = []

    def unsafe_day_one_planner(*_args):
        calls.append("planner")
        return [LocalLLMDayWorkItem(item_id="pc", title="PC", objective="unsafe", kind="ENGINE_WORK_ORDER", engine_task_id="PC-001-A", criterion_ids=["d1-repository_relationship"])]

    runner = LocalLLMDayProgram(FIXTURE_ROOT, planner=unsafe_day_one_planner, work_order_executor=lambda _order: {"final_result": "COMPLETE", "evidence": {"git_head": _record("git_head", _value("git_head"))}})
    runner.start(1)
    runner.join(3)
    result = runner.view()
    assert not calls
    assert result["state"] != LocalLLMDayState.COMPLETE.value
    assert "d1-regression_baseline" in result["contract"]["remaining_gaps"]


def test_new_day_drops_stale_work_and_old_contract_state():
    runner = LocalLLMDayProgram(FIXTURE_ROOT)
    runner.smoke(2)
    runner.snapshot.work_items = [LocalLLMDayWorkItem(item_id="stale", title="stale", objective="stale", criterion_ids=["d3-fixed_comparison"], contract_day=3, contract_version=runner.snapshot.contract.version, state=LocalLLMWorkItemState.COMPLETE)]
    runner.snapshot.replan_count = 2
    runner.smoke(1)
    assert runner.view()["work_items"] == []
    assert runner.view()["replan_count"] == 0


def test_old_false_complete_persistence_is_invalidated():
    runner = LocalLLMDayProgram(FIXTURE_ROOT)
    runner.smoke(1)
    saved = runner.view()
    saved["state"] = "COMPLETE"
    saved["contract"]["version"] = "2026-09-22-v1"
    for criterion in saved["contract"]["completion_criteria"]:
        criterion["satisfied"] = True
        criterion["evidence"] = {"run_id": "old-run"}
    restored = LocalLLMDayProgram(FIXTURE_ROOT, saved=saved)
    assert restored.view()["state"] != LocalLLMDayState.COMPLETE.value
    assert len(restored.view()["contract"]["remaining_gaps"]) == 4


def test_same_day_valid_incomplete_evidence_survives_restart():
    runner = LocalLLMDayProgram(FIXTURE_ROOT)
    runner.smoke(6)
    saved = runner.view()
    criterion = saved["contract"]["completion_criteria"][0]
    criterion["evidence"] = _valid_evidence(criterion["required_evidence"])
    criterion["satisfied"] = True
    saved["state"] = "PAUSED"
    restored = LocalLLMDayProgram(FIXTURE_ROOT, saved=saved)
    assert restored.view()["contract"]["completion_criteria"][0]["satisfied"] is True
    assert restored.view()["state"] == LocalLLMDayState.PAUSED.value


def _git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True, text=True).stdout.strip()


def _day1_repo(tmp_path):
    root = tmp_path / "local-llm"
    root.mkdir()
    _git(root, "init", "-b", "main")
    _git(root, "config", "user.email", "day1@example.test")
    _git(root, "config", "user.name", "Day One")
    files = {
        "docs/runbooks/work-plan-day1-14.md": "# Day 1-14\n",
        "docs/README.md": "| Current decision architecture | architecture/decision-reasoning-architecture.md |\n| Current execution sequence | runbooks/work-plan-day1-14.md |\n| Resume context | handoff/handoff-2026-09-18.md |\n",
        "docs/architecture/decision-reasoning-architecture.md": "# Architecture\n",
        "docs/handoff/handoff-2026-09-18.md": "# Handoff\n",
        "tests/test_process_consistency_smoke.py": "def test_baseline():\n    assert True\n",
        "tests/test_process_consistency_review_set.py": "def test_review_set():\n    assert True\n",
    }
    for relative, text in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    _git(root, "add", ".")
    _git(root, "commit", "-m", "fixture baseline")
    _git(root, "remote", "add", "origin", str(root))
    head = _git(root, "rev-parse", "HEAD")
    _git(root, "config", "branch.main.remote", "origin")
    _git(root, "config", "branch.main.merge", "refs/heads/main")
    _git(root, "update-ref", "refs/remotes/origin/main", head)
    (root / "artifacts").mkdir()
    (root / "artifacts" / "retained.txt").write_text("preserve", encoding="utf-8")
    return root


def _run_day1(root):
    runner = LocalLLMDayProgram(root)
    runner.start(1)
    runner.join(240)
    return runner.view()


def test_day_one_disposable_git_integration_collects_real_evidence(tmp_path):
    root = _day1_repo(tmp_path)
    result = _run_day1(root)
    assert result["state"] == LocalLLMDayState.COMPLETE.value
    criteria = {item["criterion_id"]: item["evidence"] for item in result["contract"]["completion_criteria"]}
    head = _git(root, "rev-parse", "HEAD")
    assert criteria["d1-repository_relationship"]["git_head"]["value"]["head"] == head
    assert criteria["d1-repository_relationship"]["origin_ref"]["value"]["origin_url"] == str(root)
    assert "artifacts/retained.txt" in criteria["d1-preservation_audit"]["status_audit"]["value"]["untracked_paths"]
    assert criteria["d1-regression_baseline"]["test_result"]["value"]["exit_code"] == 0
    assert criteria["d1-regression_baseline"]["commit_ref"]["value"]["head"] == head


def test_day_one_integration_rejects_staged_generated_artifact(tmp_path):
    root = _day1_repo(tmp_path)
    path = root / "results" / "generated.json"
    path.parent.mkdir()
    path.write_text("{}", encoding="utf-8")
    _git(root, "add", "results/generated.json")
    result = _run_day1(root)
    assert result["state"] != LocalLLMDayState.COMPLETE.value
    assert "d1-preservation_audit" in result["contract"]["remaining_gaps"]


def test_day_one_integration_rejects_broken_authoritative_documentation(tmp_path):
    root = _day1_repo(tmp_path)
    (root / "docs" / "README.md").write_text("| Current execution sequence | Week1.md |\n", encoding="utf-8")
    result = _run_day1(root)
    assert result["state"] != LocalLLMDayState.COMPLETE.value
    assert "d1-documentation_consistency" in result["contract"]["remaining_gaps"]


def test_day_one_integration_rejects_failed_regression(tmp_path):
    root = _day1_repo(tmp_path)
    (root / "tests" / "test_process_consistency_smoke.py").write_text("def test_baseline():\n    assert False\n", encoding="utf-8")
    result = _run_day1(root)
    assert result["state"] != LocalLLMDayState.COMPLETE.value
    assert "d1-regression_baseline" in result["contract"]["remaining_gaps"]
