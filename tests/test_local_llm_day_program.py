import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from backend.control.local_llm_day_program import LocalLLMDayProgram
from backend.control.evidence_registry import REGISTRY
from backend.control.day_action_registry import STRATEGIES, assert_coverage
from backend.control.day_git import GitSafetyError
from backend.control.retained_evidence import RetainedEvidenceResolver
from backend.control.solution_catalog import JsonSolutionCatalogStore, RepairEpisodeStore, SolutionCatalog
from backend.models.local_llm_day import DayIssueClassification, DynamicDayWorkOrder, LocalLLMDayState, LocalLLMDayWorkItem, LocalLLMWorkItemState


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
        "test_result": {"commands": [["python", "-m", "pytest"]], "exit_code": 0, "passed": 1, "failed": 0, "deterministic_only": True},
        "source_check": {"checked_paths": ["src/example.py"], "assertions": ["required boundary"]},
        "deterministic_tests": {"commands": [["python", "-m", "pytest"]], "exit_code": 0, "passed": 1, "failed": 0},
        "architecture_check": {"checked_documents": ["docs/architecture.md"], "assertions": ["Python owns facts"]},
        "baseline_ref": {"baseline_sha": "a" * 40, "version": "v0.3.2"},
        "preservation_audit": {"protected_paths": ["results/"], "preserved": True},
        "schema_contract": {"schema_path": "schemas/temporal.json", "schema_version": "v1"},
        "provenance_test": {"commands": [["python", "-m", "pytest"]], "exit_code": 0, "passed": 1, "failed": 0},
    }
    return shapes.get(name, {"proof": name})


def _valid_evidence(required):
    return {name: _record(name, _value(name)) for name in required}


def _planner(contract, _inventory):
    return [LocalLLMDayWorkItem(item_id=f"task-{criterion.criterion_id}", title="bounded task", objective=criterion.statement, kind="ENGINE_WORK_ORDER", engine_task_id="SAFE-FIXTURE", criterion_ids=[criterion.criterion_id]) for criterion in contract.completion_criteria if criterion.criterion_id in contract.remaining_gaps][:3]


def _valid_executor(work_order):
    strategy = next(s for s in STRATEGIES.values() if s.strategy_id == work_order["strategy_id"])
    required = strategy.template.post_action_evidence_types
    return {"final_result": "COMPLETE", "evidence": _valid_evidence(required)}


def _write_retained_day_two_fixture(root):
    baseline_config = root / "config" / "decision-reasoning-prototype.json"
    baseline_config.parent.mkdir(parents=True)
    baseline_config.write_text('{"version":"0.3.2"}', encoding="utf-8")
    baseline_hash = hashlib.sha256(baseline_config.read_bytes()).hexdigest()
    (root / "config" / "decision-reasoning-v0.4.json").write_text(json.dumps({
        "version": "0.4", "baseline_config_sha256": baseline_hash,
        "action_gate": {"version": "FEASIBLE_RELEVANT_ACTION_GATE-v1", "require_feasible": True, "require_relevant_to_active_verified_issue": True},
    }), encoding="utf-8")
    baseline_manifest = root / "results" / "decision-reasoning-prototype" / "DRAP-baseline" / "manifest.json"
    baseline_manifest.parent.mkdir(parents=True)
    baseline_manifest.write_text(json.dumps({"run_id": "DRAP-baseline", "status": "COMPLETED", "dry_run": False, "config_version": "0.3.2", "config_sha256": baseline_hash}), encoding="utf-8")
    run = root / "results" / "decision-reasoning-v0.4" / "DRAP-retained"
    run.mkdir(parents=True)
    (run / "manifest.json").write_text(json.dumps({
        "run_id": "DRAP-retained", "status": "COMPLETED", "dry_run": False, "config_version": "0.4", "config_sha256": "c" * 64,
        "action_gate": {"version": "FEASIBLE_RELEVANT_ACTION_GATE-v1", "enforced": True},
    }), encoding="utf-8")
    (run / "summary.json").write_text(json.dumps({"action_gate": {"all_permitted_actions_feasible_and_relevant": True}}), encoding="utf-8")
    (run / "validation.jsonl").write_text(json.dumps({
        "effect_mapping_complete": True, "action_precondition_failure_count": 0,
        "hard_constraint_violation_count": 0, "fabricated_fact_count": 0,
        "provenance_error_count": 0,
    }) + "\n", encoding="utf-8")
    return run


def _write_retained_day_four_fixture(root):
    config = root / "config" / "decision-generalization-benchmark.json"
    config.parent.mkdir(parents=True)
    config.write_text(json.dumps({"version": "0.1", "architecture_version": "DRAP-v0.3.2"}), encoding="utf-8")
    config_hash = hashlib.sha256(config.read_bytes()).hexdigest()
    run = root / "results" / "decision-generalization" / "DAGB-retained"
    (run / "freeze").mkdir(parents=True)
    (run / "manifest.json").write_text(json.dumps({
        "run_id": "DAGB-retained", "status": "COMPLETED", "dry_run": False,
        "benchmark_version": "DAGB-v0.1", "architecture_version": "DRAP-v0.3.2",
        "config_sha256": config_hash, "architecture_frozen": True,
        "architecture_freeze_verified": True,
    }), encoding="utf-8")
    (run / "summary.json").write_text(json.dumps({
        "flags": {name: True for name in ("HOLDOUT_PIPELINE_STABLE", "METAMORPHIC_INVARIANCE_STABLE", "NO_CASE_HARDCODING", "NO_ORACLE_LEAKAGE")},
        "architecture_freeze_verified": True, "holdout_case_count": 6, "metamorphic_pair_count": 3,
    }), encoding="utf-8")
    (run / "freeze" / "freeze-verification.json").write_text(json.dumps({"unchanged": True, "changed_files": []}), encoding="utf-8")
    (run / "freeze" / "frozen-file-sha256-before.json").write_text(json.dumps({"scripts/eval.py": "a" * 64}), encoding="utf-8")
    cases = ("GH-001", "GH-001-M", "GH-002", "GH-002-M", "GH-003", "GH-003-M")
    (run / "validation.jsonl").write_text("".join(json.dumps({"run_id": "DAGB-retained", "case_id": case, "failure_stage": "PLAN_VALIDATION"}) + "\n" for case in cases), encoding="utf-8")
    pairs = ("GH-001", "GH-002", "GH-003")
    (run / "metamorphic-definition-validation.json").write_text(json.dumps([{ "pair_id": pair, "valid": True} for pair in pairs]), encoding="utf-8")
    (run / "metamorphic-metrics.json").write_text(json.dumps([{ "pair_id": pair, "invariance_status": "STABLE"} for pair in pairs]), encoding="utf-8")
    (run / "oracle-leakage-scan.json").write_text(json.dumps({"status": "PASS", "finding_count": 0}), encoding="utf-8")
    (run / "case-hardcode-scan.json").write_text(json.dumps({"status": "PASS", "case_id_findings": [], "known_literal_findings": []}), encoding="utf-8")
    return run


def test_retained_day_two_evidence_is_typed_complete_and_fails_closed(tmp_path):
    run = _write_retained_day_two_fixture(tmp_path)
    resolver = RetainedEvidenceResolver(tmp_path)
    evidence = resolver.resolve(2)
    assert set(evidence) == {"source_check", "deterministic_tests", "architecture_check", "test_result", "baseline_ref", "preservation_audit"}
    assert all(REGISTRY.validate(name, record) for name, record in evidence.items())
    assert resolver.resolve(4) == {}
    runner = LocalLLMDayProgram(tmp_path, retained_evidence_resolver=resolver)
    contract = runner._load_contracts()[2]
    runner._evaluate_contract(contract, runner._inventory(contract))
    assert not contract.remaining_gaps
    manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
    manifest["status"] = "FAILED"
    (run / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    assert RetainedEvidenceResolver(tmp_path).resolve(2) == {}


def test_retained_day_four_evidence_is_typed_complete_and_fails_closed(tmp_path):
    run = _write_retained_day_four_fixture(tmp_path)
    resolver = RetainedEvidenceResolver(tmp_path)
    evidence = resolver.resolve(4)
    assert set(evidence) == {"holdout_manifest", "architecture_ref", "dagb_artifact", "anti_leakage_check", "retained_failures"}
    assert all(REGISTRY.validate(name, record) for name, record in evidence.items())
    runner = LocalLLMDayProgram(tmp_path, retained_evidence_resolver=resolver)
    contract = runner._load_contracts()[4]
    runner._evaluate_contract(contract, runner._inventory(contract))
    assert not contract.remaining_gaps
    (run / "freeze" / "freeze-verification.json").write_text(json.dumps({"unchanged": False, "changed_files": ["scripts/eval.py"]}), encoding="utf-8")
    assert RetainedEvidenceResolver(tmp_path).resolve(4) == {}


def test_day_one_test_evidence_cache_reuses_only_a_successful_unchanged_key(tmp_path, monkeypatch):
    test_path = tmp_path / "tests" / "test_process_consistency_smoke.py"
    test_path.parent.mkdir()
    test_path.write_text("def test_fixture(): pass\n", encoding="utf-8")
    calls = []
    def successful_run(*_args, **_kwargs):
        calls.append("run")
        return subprocess.CompletedProcess([], 0, "1 passed in 0.01s", "")
    monkeypatch.setattr("backend.control.local_llm_day_program.subprocess.run", successful_run)
    runner = LocalLLMDayProgram(tmp_path)
    first = runner._day_one_test_result(cache_key="unchanged")
    second = runner._day_one_test_result(cache_key="unchanged")
    assert first["cache_hit"] is False and second["cache_hit"] is True
    assert calls == ["run"]
    assert runner._day_one_test_result(cache_key="changed")["cache_hit"] is False
    assert calls == ["run", "run"]


def test_pytest_temporary_directory_is_repository_owned(tmp_path):
    assert tmp_path.is_relative_to(Path(__file__).parents[1] / ".pytest-tmp")


@pytest.mark.parametrize("day", [6])
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
    runner._ingest_legacy_evidence(runner.snapshot.contract, _valid_evidence(criterion.required_evidence), provider_id="test-adapter", source_fingerprint="a" * 64)
    runner._evaluate_contract(runner.snapshot.contract, {})
    assert criterion.satisfied
    assert set(criterion.required_evidence).issubset(criterion.evidence)


@pytest.mark.parametrize("repair_produces_evidence", [True, False])
def test_missing_evidence_is_diagnosed_before_an_unchanged_action_fails_safe(repair_produces_evidence):
    calls = []
    executions = []

    def planner(contract, _inventory):
        calls.append(contract.remaining_gaps[:])
        return _planner(contract, _inventory)

    class NoProposal:
        def propose(self, **_kwargs):
            return None

    def executor(order):
        executions.append(order["kind"])
        if order["kind"] == "DAY_ACTION_TEMPLATE":
            return {"final_result": "COMPLETE", "evidence": {}}
        assert order["kind"] == "CODEX_EXPERT_SOLVER"
        names = [name for criterion in runner.snapshot.contract.completion_criteria for name in criterion.required_evidence]
        return {"final_result": "COMPLETE", "verification_passed": True,
                "evidence": _valid_evidence(names) if repair_produces_evidence else {}}

    runner = LocalLLMDayProgram(FIXTURE_ROOT, planner=planner, work_order_executor=executor, repair_builder=NoProposal())
    runner._bounded_repair_files = lambda _item: {"scripts/eval/temporal_state.py": "before"}
    runner.start(6)
    runner.join(3)
    result = runner.view()
    assert result["state"] == ("COMPLETE" if repair_produces_evidence else "HUMAN_ACTION_REQUIRED")
    assert result["report"]["result"] != "DAY_NO_SAFE_ACTION"
    assert executions == ["DAY_ACTION_TEMPLATE", "CODEX_EXPERT_SOLVER"]
    assert result["gap_diagnoses"]
    assert all(item["classification"] == "ENGINEERING_REPAIR" for item in result["gap_diagnoses"])
    if not repair_produces_evidence:
        assert result["authority_blocker"]["reason_code"] == "REPAIR_SCOPE_AUTHORITY_REQUIRED"
    assert calls == []
    assert len(result["action_attempts"]) == 1


def test_planner_cannot_expand_authority():
    def unsafe_planner(_contract, _inventory):
        return [LocalLLMDayWorkItem(item_id="unsafe", title="unsafe", objective="unsafe", kind="SHELL", criterion_ids=["not-a-criterion"])]

    runner = LocalLLMDayProgram(FIXTURE_ROOT, planner=unsafe_planner)
    runner.start(2)
    runner.join(3)
    assert runner.view()["report"]["result"] == "PREREQUISITE_DAY_REQUIRED"


def test_model_quality_finding_is_preserved_and_never_offers_repair(tmp_path):
    test_production_research_uses_admitted_condition_and_retains_outcome(tmp_path, "MODEL_QUALITY_FINDING")


def test_static_engine_failure_cannot_offer_repair_and_go_without_an_interrupted_episode():
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
    result = runner.view()
    assert result["recommended_action"]["action_id"] in {"SHOW_FAILURE", "SHOW_REQUIRED_ACTION"}
    assert runner.repair_and_go()["error_code"] == "AUTONOMOUS_REPAIR_NOT_AVAILABLE"


def test_local_rejection_runs_expert_and_teaches_next_episode(tmp_path, monkeypatch):
    engine, root, writer, builder = _repair_engine(tmp_path)
    runner = engine.local_llm_day_program
    catalog_path = tmp_path / "verified-catalog.json"
    runner.solution_catalog = SolutionCatalog(JsonSolutionCatalogStore(catalog_path))
    accepted = []
    accept = runner._accept_repair
    def observe_accept(item, value, episode, **kwargs):
        accept(item, value, episode, **kwargs)
        accepted.append({"item_id": item.item_id, "result_keys": list(value),
                         "adapter_evidence": sorted(value.get("evidence", {})),
                         "persisted_evidence": sorted(item.evidence.get("evidence", {})),
                         "repair_diagnoses": [d.model_dump(mode="json") for d in runner.snapshot.gap_diagnoses
                                              if d.classification == DayIssueClassification.ENGINEERING_REPAIR]})
    monkeypatch.setattr(runner, "_accept_repair", observe_accept)
    engine.start_local_llm_day(6)
    engine.local_llm_day_program.join(120)
    result = engine.local_llm_day_status()
    (tmp_path / "repair-e2e.json").write_text(json.dumps({"snapshot": result, "roles": writer.roles,
                                                        "accepted": accepted}, indent=2), encoding="utf-8")
    assert result["state"] == "COMPLETE", (result["report"], result["work_items"], writer.roles)
    episode = engine.local_llm_day_program.repair_episode_store.get(result["repair_episode_ids"][0])
    assert len(episode.proposal_attempts) == 3
    assert episode.final_outcome == "CODEX_VERIFIED"
    assert all(p.outcome == "REJECTED" for p in episode.proposal_attempts)
    assert episode.verification_result == "PASS"
    assert writer.roles == ["normal", "local", "local", "local", "expert"]
    expected_evidence = {"schema_contract", "source_check", "provenance_test", "deterministic_tests", "architecture_check"}
    assert len(accepted) == 1
    assert set(accepted[0]["adapter_evidence"]) == expected_evidence
    assert set(accepted[0]["persisted_evidence"]) == expected_evidence
    assert accepted[0]["result_keys"].index("evidence") >= 20
    assert accepted[0]["repair_diagnoses"]
    assert set(r.evidence_type for r in runner.snapshot.evidence_store.values()) == expected_evidence
    assert all(runner._evidence_record_valid(r.evidence_type, r) for r in runner.snapshot.evidence_store.values())
    assert all(c.satisfied and c.evidence_record_ids for c in runner.snapshot.contract.completion_criteria)
    assert result["authority_blocker"] is None
    assert result["state_history"].count("REPAIR_SUPERVISOR") == 1
    catalog = engine.local_llm_day_program.solution_catalog
    assert catalog.entries()[0].source == "CODEX_VERIFIED"
    assert (root / "scripts/eval/temporal_state.py").read_text() == "def valid_time(): return False\n"
    second, _, writer2, builder2 = _repair_engine(tmp_path / "second", root=root)
    second.local_llm_day_program.solution_catalog = SolutionCatalog(JsonSolutionCatalogStore(catalog_path))
    second.start_local_llm_day(6)
    second.local_llm_day_program.join(120)
    assert second.local_llm_day_status()["state"] == "COMPLETE", second.local_llm_day_status()
    assert builder2.requests[0]["repair_knowledge"]
    assert writer2.roles == ["normal", "local", "local", "local", "expert"]
    assert len(builder2.requests) == 3
    assert second.local_llm_day_program.solution_catalog.entries()[0].uses > 0
    (tmp_path / "repair-e2e.json").write_text(json.dumps({"snapshot": result, "roles": writer.roles,
        "accepted": accepted, "second_snapshot": second.local_llm_day_status(), "second_roles": writer2.roles,
        "second_repair_knowledge": builder2.requests[0]["repair_knowledge"]}, indent=2), encoding="utf-8")


def test_repair_deadline_escalates_without_waiting(tmp_path):
    from backend.models.local_llm_day import RepairEpisode
    engine, root, writer, builder = _repair_engine(tmp_path)
    runner = engine.local_llm_day_program
    runner.smoke(6)
    template = STRATEGIES[(6, "source_check")].template
    order = DynamicDayWorkOrder(task_id="day-6-d6-temporal-state-design",
        allowed_files=list(template.allowed_output_scope), context_files=list(template.context_scope),
        acceptance_test_files=["tests/test_temporal_state.py"])
    item = LocalLLMDayWorkItem(item_id="repair-D6_SOURCE_CHECK", title="interrupted repair",
        objective="repair deterministic failure", kind="DYNAMIC_ENGINEERING_WORK", dynamic_work_order=order,
        criterion_ids=[runner.snapshot.contract.completion_criteria[0].criterion_id],
        contract_day=6, contract_version=runner.snapshot.contract.version, state=LocalLLMWorkItemState.FAILED,
        evidence={"failure_excerpt": "fixed temporal assertion"})
    runner.snapshot.work_items = [item]
    episode = RepairEpisode(episode_id="persisted-deadline", project_id="local_llm_lab", day=6,
        work_item_id=item.item_id, failure_class=DayIssueClassification.ENGINEERING_REPAIR,
        failure_fingerprint=runner._failure_fingerprint(item, "fixed temporal assertion"),
        failure_excerpt="fixed temporal assertion", started_at_epoch=0, repair_deadline_epoch=300,
        contract_version=runner.snapshot.contract.version,
        scope_fingerprint=runner._text_fingerprint(order.model_dump_json()))
    path = tmp_path / "episodes.json"
    runner.repair_episode_store = RepairEpisodeStore(path)
    runner.repair_episode_store.save(episode)
    runner.snapshot.repair_episode_ids = [episode.episode_id]
    runner.snapshot.state = LocalLLMDayState.REPAIR_SUPERVISOR
    runner.snapshot.contract_fingerprint = runner._contract_fingerprint(runner.snapshot.contract)
    restored = LocalLLMDayProgram(root, saved=runner.view(),
        repair_episode_store=RepairEpisodeStore(path), repair_builder=builder,
        work_order_executor=engine._execute_local_llm_day_work_order, clock=lambda: 301.0)
    engine.local_llm_day_program = restored
    assert restored.view()["enabled_controls"]["repair_and_go"]
    restored.repair_and_go()
    restored.join(120)
    assert restored.view()["state"] == "COMPLETE", restored.view()
    assert not builder.requests and writer.roles == ["expert"]
    retained = restored.repair_episode_store.get(episode.episode_id)
    assert retained.repair_deadline_epoch == 300
    assert retained.final_outcome == "CODEX_VERIFIED"


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
    criterion = runner.snapshot.contract.completion_criteria[0]
    runner._ingest_legacy_evidence(runner.snapshot.contract, _valid_evidence(criterion.required_evidence),
                                   provider_id="fixture-adapter", source_fingerprint="a" * 64)
    runner._evaluate_contract(runner.snapshot.contract, {})
    saved = runner.view()
    saved["state"] = "PAUSED"
    restored = LocalLLMDayProgram(FIXTURE_ROOT, saved=saved)
    assert restored.view()["contract"]["completion_criteria"][0]["satisfied"] is True
    assert restored.view()["state"] == LocalLLMDayState.PAUSED.value
    assert restored.view()["evidence_store"] == saved["evidence_store"]


@pytest.mark.parametrize("operation", ["restart", "resume"])
def test_identical_contract_identity_survives_restart_and_resume(operation):
    runner = LocalLLMDayProgram(FIXTURE_ROOT)
    runner.smoke(6)
    contract = runner.snapshot.contract
    all_required = sorted({evidence for criterion in contract.completion_criteria for evidence in criterion.required_evidence})
    runner._ingest_legacy_evidence(contract, _valid_evidence(all_required),
                                   provider_id="fixture-adapter", source_fingerprint="a" * 64)
    runner._evaluate_contract(contract, {})
    assert not contract.remaining_gaps
    runner.snapshot.contract_fingerprint = runner._contract_fingerprint(contract)
    runner.snapshot.state = LocalLLMDayState.PAUSED
    saved = runner.view()
    reordered = contract.model_copy(deep=True)
    reordered.completion_criteria.reverse()
    for criterion in reordered.completion_criteria:
        criterion.required_evidence.reverse()
    reordered.constraints.reverse()
    reordered.authoritative_sources.reverse()
    assert runner._contract_fingerprint(reordered) == saved["contract_fingerprint"]
    if operation == "restart":
        runner = LocalLLMDayProgram(FIXTURE_ROOT, saved=saved)
    else:
        runner.resume()
        runner.join(5)
    result = runner.view()
    assert result["contract_fingerprint"] == saved["contract_fingerprint"]
    assert result["evidence_store"] == saved["evidence_store"]
    assert result["contract"]["remaining_gaps"] == []
    if operation == "resume":
        assert result["state"] == "COMPLETE", result
    else:
        assert result["state"] == "PAUSED", result


@pytest.mark.parametrize("operation", ["restart", "resume"])
@pytest.mark.parametrize("changed_field", ["statement", "required_evidence", "objective", "constraints", "authoritative_sources"])
def test_same_version_contract_content_change_fails_closed(tmp_path, monkeypatch, operation, changed_field):
    import yaml
    runner = LocalLLMDayProgram(FIXTURE_ROOT)
    runner.smoke(6)
    criterion = runner.snapshot.contract.completion_criteria[0]
    runner._ingest_legacy_evidence(runner.snapshot.contract, _valid_evidence(criterion.required_evidence),
                                   provider_id="fixture-adapter", source_fingerprint="a" * 64)
    runner.snapshot.contract_fingerprint = runner._contract_fingerprint(runner.snapshot.contract)
    runner.snapshot.state = LocalLLMDayState.PAUSED
    saved = runner.view()
    document = yaml.safe_load(runner.PROGRAM_PATH.read_text(encoding="utf-8"))
    definition = next(d for d in document["days"] if d["day"] == 6)
    if changed_field == "statement":
        definition["completion_criteria"][0]["statement"] += " changed semantics"
    elif changed_field == "required_evidence":
        # Move two existing registered evidence types between criteria.  Registry
        # coverage remains valid while the criterion semantics change.
        first = definition["completion_criteria"][0]["evidence"]
        second = definition["completion_criteria"][1]["evidence"]
        first[1], second[1] = second[1], first[1]
    elif changed_field == "objective":
        definition["objective"] += " changed semantics"
    else:
        # Sources/constraints are program-level in the server-owned YAML.
        key = "shared_constraints" if changed_field == "constraints" else changed_field
        document[key] = [*document[key], "changed semantics"]
    path = tmp_path / "contract.yaml"
    path.write_text(yaml.safe_dump(document), encoding="utf-8")
    monkeypatch.setattr(LocalLLMDayProgram, "PROGRAM_PATH", path)
    if operation == "restart":
        runner = LocalLLMDayProgram(FIXTURE_ROOT, saved=saved)
    else:
        runner.resume()
        runner.join(5)
    result = runner.view()
    assert result["state"] == "FAILED_UNRECOVERABLE", result
    assert result["report"]["result"] == "CONTRACT_VERSION_CONTENT_MISMATCH"
    assert set(result["evidence_store"]) == set(saved["evidence_store"])
    assert all(not record["compatibility_result"] for record in result["evidence_store"].values())
    assert not result["action_attempts"]


@pytest.mark.parametrize("operation", ["restart", "resume"])
def test_changed_contract_version_does_not_reuse_saved_evidence(tmp_path, monkeypatch, operation):
    import yaml
    runner = LocalLLMDayProgram(FIXTURE_ROOT)
    runner.smoke(6)
    criterion = runner.snapshot.contract.completion_criteria[0]
    runner._ingest_legacy_evidence(runner.snapshot.contract, _valid_evidence(criterion.required_evidence),
                                   provider_id="fixture-adapter", source_fingerprint="a" * 64)
    runner.snapshot.contract_fingerprint = runner._contract_fingerprint(runner.snapshot.contract)
    runner.snapshot.state = LocalLLMDayState.PAUSED
    saved = runner.view()
    document = yaml.safe_load(runner.PROGRAM_PATH.read_text(encoding="utf-8"))
    document["version"] += "-next"
    path = tmp_path / "contract-version.yaml"
    path.write_text(yaml.safe_dump(document), encoding="utf-8")
    monkeypatch.setattr(LocalLLMDayProgram, "PROGRAM_PATH", path)
    if operation == "restart":
        runner = LocalLLMDayProgram(FIXTURE_ROOT, saved=saved)
    else:
        runner.resume()
        runner.join(5)
    result = runner.view()
    assert result["state"] == "FAILED_UNRECOVERABLE", result
    assert result["report"]["result"] == "CONTRACT_VERSION_CHANGED"
    assert set(result["evidence_store"]) == set(saved["evidence_store"])
    assert all(not record["compatibility_result"] for record in result["evidence_store"].values())
    assert not result["action_attempts"]


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
    criteria = {item["criterion_id"]: {name: result["evidence_store"][record_id] for name, record_id in item["evidence_record_ids"].items()} for item in result["contract"]["completion_criteria"]}
    head = _git(root, "rev-parse", "HEAD")
    assert criteria["d1-repository_relationship"]["git_head"]["value"]["head"] == head
    assert criteria["d1-repository_relationship"]["origin_ref"]["value"]["origin_url"] == str(root)
    assert "artifacts/retained.txt" in criteria["d1-preservation_audit"]["status_audit"]["value"]["untracked_paths"]
    assert criteria["d1-regression_baseline"]["test_result"]["value"]["exit_code"] == 0
    checkpoint = criteria["d1-regression_baseline"]["commit_ref"]["value"]
    assert checkpoint["head"] != head
    assert checkpoint["parent_head"] == head
    assert checkpoint["checkpoint_ref"].startswith("refs/heads/ai-control-center/day1-baseline-")
    assert _git(root, "rev-parse", "HEAD") == head
    assert _git(root, "diff", "--cached", "--name-only") == ""


def test_frozen_registry_covers_each_configured_day_evidence_pair():
    document = __import__("yaml").safe_load(LocalLLMDayProgram.PROGRAM_PATH.read_text(encoding="utf-8"))
    pairs = {(day["day"], evidence) for day in document["days"] for criterion in day["completion_criteria"] for evidence in criterion["evidence"]}
    assert len(REGISTRY.names) == 46
    assert len(pairs) == 62
    assert_coverage(pairs, REGISTRY.names)
    assert set(STRATEGIES) == pairs


def test_day_one_commit_ref_is_not_satisfied_by_read_only_head_observation(tmp_path):
    root = _day1_repo(tmp_path)
    runner = LocalLLMDayProgram(root)
    contract = runner._load_contracts()[1]
    runner._ingest_action_result(contract, runner._diagnose_gaps(contract, runner._inventory(contract))[0], runner._collect_day_one_evidence(contract))
    runner._evaluate_contract(contract, runner._inventory(contract))
    assert "d1-regression_baseline" in contract.remaining_gaps
    assert not contract.completion_criteria[-1].evidence_record_ids.get("commit_ref")


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


def _production_engine(root, tmp_path):
    from backend.control.projects import ConfiguredProject, ProjectRegistry
    from backend.orchestrator.engine import ControlCenterEngine
    from backend.models.runtime import RuntimeConfig
    projects = ProjectRegistry(projects={"local_llm_lab": ConfiguredProject(
        name="Disposable Day project", path=root, default_branch="main")})
    engine = ControlCenterEngine(project_registry=projects, runtime_config=RuntimeConfig(),
                                 worktree_root=tmp_path / "worktrees", smoke_root=tmp_path / "smoke")
    engine.local_llm_day_program.solution_catalog = SolutionCatalog()
    engine.local_llm_day_program.repair_episode_store = RepairEpisodeStore()
    return engine


def _repair_engine(tmp_path, root=None):
    from backend.control.local_ollama_repair import RepairEdit, RepairProposal
    from backend.models.result import ExecutionResult, ProcessDiagnostics, TokenUsage
    from backend.models.runtime import CodexMode
    tmp_path.mkdir(parents=True, exist_ok=True)
    if root is None:
        root = _day1_repo(tmp_path)
        contents = {
            "scripts/eval/temporal_state.py": "def valid_time(): return False\n",
            "schemas/temporal-state.json": '{"type":"object","properties":{"time":{"type":"string"}}}',
            "docs/architecture/temporal-state.md": "# Fixed temporal contract\n",
            "tests/test_temporal_state.py": "import importlib.util\nfrom pathlib import Path\ndef test_time():\n    path = Path(__file__).parents[1] / 'scripts/eval/temporal_state.py'\n    spec = importlib.util.spec_from_file_location('temporal', path)\n    module = importlib.util.module_from_spec(spec)\n    spec.loader.exec_module(module)\n    assert module.valid_time() is True\n",
            ".gitignore": "__pycache__/\n.pytest_cache/\n",
        }
        for relative, value in contents.items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(value, encoding="utf-8")
        _git(root, "add", "--", *contents)
        _git(root, "commit", "-m", "fixture temporal defect")
    engine = _production_engine(root, tmp_path)
    engine.runtime.codex.mode = CodexMode.REAL
    class Writer:
        def __init__(self):
            self.roles = []
        def run_worktree_task(self, working_directory, prompt):
            role = "expert" if "Codex Expert Solver repair" in prompt else "local" if "LOCAL LLM COUNTERMEASURE" in prompt else "normal"
            self.roles.append(role)
            if role == "expert":
                (working_directory / "scripts/eval/temporal_state.py").write_text("def valid_time(): return True\n", encoding="utf-8")
            return ExecutionResult(status="completed", test_result="pending", summary="fixture provider", exit_code=0,
                token_usage=TokenUsage(input_tokens=1, output_tokens=1, available=True),
                diagnostics=ProcessDiagnostics(thread_started=True, turn_started=True, turn_completed=True))
    class Proposals:
        def __init__(self):
            self.requests = []
        def propose(self, **kwargs):
            self.requests.append(kwargs)
            return RepairProposal(f"fixture proposal {len(self.requests)}", (RepairEdit("scripts/eval/temporal_state.py", "False", "False"),))
    writer, builder = Writer(), Proposals()
    engine.real_runner = writer
    engine.local_llm_day_program.repair_builder = builder
    return engine, root, writer, builder


def test_unapproved_research_condition_is_configuration_boundary(tmp_path):
    engine = _production_engine(_day1_repo(tmp_path), tmp_path)
    engine.day_action_executor.research_runner.run_command = lambda *_args, **_kwargs: pytest.fail("Unapproved research must not run")
    engine.start_local_llm_day(10)
    engine.local_llm_day_program.join(10)
    result = engine.local_llm_day_status()
    assert result["state"] == "HUMAN_ACTION_REQUIRED", result
    assert result["blocker"]["reason_code"] == "RESEARCH_CONDITION_NOT_APPROVED"
    assert result["blocker"]["resolution_strategy"] == "RESEARCH_CONDITION"
    assert not result["repair_episode_ids"]


@pytest.mark.parametrize("outcome", ["OBSERVED", "MODEL_QUALITY_FINDING"])
def test_production_research_uses_admitted_condition_and_retains_outcome(tmp_path, outcome):
    root = _day1_repo(tmp_path)
    inputs = {"scripts/research.py": "# Deterministic fixture model boundary\n",
              "config/research.json": json.dumps({"version": "v1", "research_kind": "performance", "entrypoint": "scripts/research.py",
                                                 "inputs": ["config/input.json"], "model": "fixture-model", "execution": {"retry": False}}),
              "config/model-matrix.json": json.dumps({"models": [{"runtime_model_name": "fixture-model", "enabled": True}]}),
              "config/input.json": '{"case":"fixed"}'}
    for relative, value in inputs.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding="utf-8")
    engine = _production_engine(root, tmp_path)
    calls = []
    def model_boundary(argv, **kwargs):
        calls.append(argv)
        assert Path(kwargs["cwd"]) != root
        output = Path(argv[argv.index("--output-root") + 1])
        values = {
            "performance_artifact": {"artifact_path": str(output), "prompt_tokens": 7, "output_tokens": 3,
                                     "elapsed_seconds": 1, "vram_mb": 1, "cpu_percent": 1, "ram_mb": 1},
            "condition_record": {"condition_fingerprint": "fixture-fixed-v1", "model": "fixture-model", "configuration_version": "v1"},
            "limitation_record": {"limitations": [outcome], "scope": "fixture only"},
        }
        (output / "evidence.json").write_text(json.dumps({"values": values, "outcome": outcome}), encoding="utf-8")
        return subprocess.CompletedProcess(argv, 0)
    engine.day_action_executor.research_runner.run_command = model_boundary
    runner = engine.local_llm_day_program
    runner._supervise_repair = lambda *_args: pytest.fail("Research quality must not enter repair")
    engine.start_local_llm_day(10)
    runner.join(10)
    result = engine.local_llm_day_status()
    assert result["state"] == "COMPLETE", result
    assert len(calls) == 1
    assert all(c["satisfied"] for c in result["contract"]["completion_criteria"])
    assert all(g["classification"] == "PRODUCE_DAY_EVIDENCE" for g in result["gap_diagnoses"])
    assert result["action_attempts"][0]["action_template_id"] == "D10_PERFORMANCE_RUN"
    if outcome == "MODEL_QUALITY_FINDING":
        assert result["issue_classification"] == outcome
    for record in result["evidence_store"].values():
        assert runner._evidence_record_valid(record["evidence_type"], runner.snapshot.evidence_store[record["record_id"]])
    assert all((root / relative).read_text(encoding="utf-8") == value for relative, value in inputs.items())
    plan = result["research_execution_plans"]["D10_PERFORMANCE_RUN"]
    assert plan["script_path"] == "scripts/research.py"
    assert plan["config_paths"] == ["config/research.json"]
    condition = engine.day_action_executor.research_plan(STRATEGIES[(10, "condition_record")].template)
    retained = engine.day_action_executor.research_runner.execute(condition)
    assert retained["issue_classification"] == outcome and len(calls) == 1


def _runtime_research_fixture(root, *, script_path="scripts/runtime-discovered.py",
                              config_path="config/runtime-discovered.json",
                              input_path="datasets/runtime-input.json", script_text="# fixture research script\n"):
    values = {
        "performance_artifact": {"artifact_path": "fixture", "prompt_tokens": 7, "output_tokens": 3,
                                 "elapsed_seconds": 1, "vram_mb": 1, "cpu_percent": 1, "ram_mb": 1},
        "condition_record": {"condition_fingerprint": "fixture-fixed-v1", "model": "fixture-model", "configuration_version": "v1"},
        "limitation_record": {"limitations": ["fixture"], "scope": "fixture only"},
    }
    contents = {
        script_path: script_text,
        config_path: json.dumps({"version": "v1", "research_kind": "performance", "entrypoint": script_path,
                                 "inputs": [input_path], "model": "fixture-model", "execution": {"retry": False}}),
        "config/model-matrix.json": json.dumps({"models": [{"runtime_model_name": "fixture-model", "enabled": True}]}),
        input_path: '{"case":"fixed"}',
    }
    for relative, value in contents.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding="utf-8")
    return values


def _write_research_artifact(argv, values, outcome="OBSERVED"):
    output = Path(argv[argv.index("--output-root") + 1])
    (output / "evidence.json").write_text(json.dumps({"values": values, "outcome": outcome}), encoding="utf-8")
    return subprocess.CompletedProcess(argv, 0)


def test_runtime_research_plan_is_discovered_without_static_day_path_mapping(tmp_path):
    root = _day1_repo(tmp_path)
    values = _runtime_research_fixture(
        root, script_path="scripts/discovered_performance_boundary.py",
        config_path="config/discovered-performance-condition.json", input_path="datasets/discovered-input.json")
    engine = _production_engine(root, tmp_path)
    runner = engine.local_llm_day_program
    calls = []
    def boundary(argv, **_kwargs):
        calls.append(argv)
        return _write_research_artifact(argv, values)
    engine.day_action_executor.research_runner.run_command = boundary
    engine.start_local_llm_day(10)
    engine.local_llm_day_program.join(10)
    result = engine.local_llm_day_status()
    assert result["state"] == "COMPLETE", result
    assert len(calls) == 1
    plan = result["research_execution_plans"]["D10_PERFORMANCE_RUN"]
    assert plan["day"] == 10
    assert plan["script_path"] == "scripts/discovered_performance_boundary.py"
    assert plan["config_paths"] == ["config/discovered-performance-condition.json"]
    assert plan["input_paths"] == ["datasets/discovered-input.json"]
    assert plan["condition_fingerprint"]
    required = {"performance_artifact", "condition_record", "limitation_record"}
    stored = [record for record in runner.snapshot.evidence_store.values() if record.evidence_type in required]
    assert {record.evidence_type for record in stored} == required
    assert all(runner._evidence_record_valid(record.evidence_type, record) for record in stored)


@pytest.mark.parametrize(("unsafe", "expected_code"), [
    ("out_of_scope", "RESEARCH_PATH_OUTSIDE_TRUSTED_SCOPE"),
    ("wrong_day", "RESEARCH_DAY_AUTHORITY_MISMATCH"),
])
def test_unsafe_runtime_research_plan_fails_closed_before_execution(tmp_path, unsafe, expected_code):
    root = _day1_repo(tmp_path)
    _runtime_research_fixture(root)
    engine = _production_engine(root, tmp_path)
    calls = []
    engine.day_action_executor.research_runner.run_command = lambda *args, **kwargs: calls.append((args, kwargs))
    def unsafe_planner(request):
        proposal = dict(request["candidates"][0])
        if unsafe == "out_of_scope":
            proposal["script_path"] = "../outside.py"
        else:
            proposal["day"] = 9
        return proposal
    engine.local_llm_contract_planner.plan_research = unsafe_planner
    engine.start_local_llm_day(10)
    engine.local_llm_day_program.join(10)
    result = engine.local_llm_day_status()
    assert result["state"] == "HUMAN_ACTION_REQUIRED", result
    assert result["blocker"]["reason_code"] == expected_code
    assert calls == []
    assert not result["research_execution_plans"]


def test_ambiguous_runtime_research_condition_requires_human_decision(tmp_path):
    root = _day1_repo(tmp_path)
    _runtime_research_fixture(root, script_path="scripts/condition_a.py", config_path="config/condition_a.json", input_path="datasets/a.json")
    _runtime_research_fixture(root, script_path="scripts/condition_b.py", config_path="config/condition_b.json", input_path="datasets/b.json")
    engine = _production_engine(root, tmp_path)
    engine.day_action_executor.research_runner.run_command = lambda *_args, **_kwargs: pytest.fail("Ambiguous research must not execute")
    engine.start_local_llm_day(10)
    engine.local_llm_day_program.join(10)
    result = engine.local_llm_day_status()
    assert result["state"] == "HUMAN_ACTION_REQUIRED", result
    assert result["blocker"]["reason_code"] == "RESEARCH_CONDITION_CHOICE_REQUIRED"
    assert result["issue_classification"] == "HUMAN_PRODUCT_DECISION_REQUIRED"
    assert not result["research_execution_plans"]


@pytest.mark.parametrize("mutation", ["source", "outside_output"])
def test_research_run_rejects_source_or_output_escape(tmp_path, mutation):
    root = _day1_repo(tmp_path)
    protected = root / "scripts/protected_source.py"
    protected.parent.mkdir(parents=True, exist_ok=True)
    protected.write_text("VALUE = 'original'\n", encoding="utf-8")
    values = {
        "performance_artifact": {"artifact_path": "fixture", "prompt_tokens": 1, "output_tokens": 1,
                                 "elapsed_seconds": 1, "vram_mb": 1, "cpu_percent": 1, "ram_mb": 1},
        "condition_record": {"condition_fingerprint": "fixture", "model": "fixture-model", "configuration_version": "v1"},
        "limitation_record": {"limitations": ["fixture"], "scope": "fixture"},
    }
    mutation_statement = (
        f"Path({str(protected)!r}).write_text(\"VALUE = 'mutated'\\n\", encoding='utf-8')"
        if mutation == "source" else "(Path.cwd().parent / 'outside-approved-output.json').write_text('escape', encoding='utf-8')"
    )
    payload = json.dumps({"values": values, "outcome": "OBSERVED"})
    script = (
        "import argparse\nimport json\nfrom pathlib import Path\n"
        "parser = argparse.ArgumentParser()\nparser.add_argument('--config')\nparser.add_argument('--output-root')\nargs = parser.parse_args()\n"
        f"{mutation_statement}\n"
        "output = Path(args.output_root)\noutput.mkdir(parents=True, exist_ok=True)\n"
        f"(output / 'evidence.json').write_text({payload!r}, encoding='utf-8')\n"
    )
    _runtime_research_fixture(root, script_text=script)
    engine = _production_engine(root, tmp_path)
    runner = engine.local_llm_day_program
    runner.smoke(10)
    condition = engine.day_action_executor.research_plan(STRATEGIES[(10, "condition_record")].template)
    with pytest.raises(GitSafetyError, match="RESEARCH_SOURCE_MUTATION"):
        engine.day_action_executor.research_runner.execute(condition)
    terminal = next(engine.day_action_executor.research_runner.storage.rglob("terminal.json"))
    assert json.loads(terminal.read_text(encoding="utf-8"))["safety"] == "SOURCE_MUTATION"
    if mutation == "source":
        assert protected.read_text(encoding="utf-8") == "VALUE = 'mutated'\n"


@pytest.mark.parametrize("authority", ["human", "external"])
def test_production_api_resumes_same_day_after_authority_resolution(tmp_path, monkeypatch, authority):
    from fastapi.testclient import TestClient
    import backend.app as app
    root = _day1_repo(tmp_path)
    missing = root / "docs/runbooks/work-plan-day1-14.md"
    if authority == "external":
        preserved = missing.read_text(encoding="utf-8")
        missing.rename(root / "docs/runbooks/preserved-runbook.md")
    engine = _production_engine(root, tmp_path)
    monkeypatch.setattr(app, "engine", engine)
    client = TestClient(app.app)
    day = 14 if authority == "human" else 1
    expected = "HUMAN_ACTION_REQUIRED" if authority == "human" else "EXTERNAL_ACTION_REQUIRED"
    client.post(f"/api/local-llm/day/{day}/start")
    engine.local_llm_day_program.join(30)
    before = client.get("/api/local-llm/day/status").json()
    assert before["state"] == expected, before
    assert before["blocker"]["resolution_strategy"] == ("RETAINED_EVIDENCE" if authority == "human" else "AUTHORITATIVE_SOURCES")
    assert not before["enabled_controls"]["resume"]
    selected_day, contract_fingerprint = before["selected_day"], before["contract_fingerprint"]
    blocker = before["blocker"]
    compatible_evidence = {record_id for record_id, record in before["evidence_store"].items()
                           if record["compatibility_result"]}
    client.post("/api/local-llm/day/resume")
    engine.local_llm_day_program.join(30)
    unresolved = client.get("/api/local-llm/day/status").json()
    assert unresolved["state"] == expected and unresolved["selected_day"] == day
    assert len(unresolved["action_attempts"]) == len(before["action_attempts"])
    assert unresolved["contract_fingerprint"] == contract_fingerprint
    assert unresolved["blocker"] == blocker
    assert compatible_evidence.issubset(unresolved["evidence_store"])
    if authority == "human":
        marker = root / "docs/reviews/day14-human-review.json"
        marker.parent.mkdir(parents=True)
        marker.write_text(json.dumps({"day": 14, "project_id": "local_llm_lab", "authority": "human",
                                     "approved": True, "marker_id": "fixture-human-review"}), encoding="utf-8")
    else:
        missing.write_text(preserved, encoding="utf-8")
    assert client.get("/api/local-llm/day/status").json()["enabled_controls"]["resume"]
    client.post("/api/local-llm/day/resume")
    engine.local_llm_day_program.join(60)
    result = client.get("/api/local-llm/day/status").json()
    assert result["state"] == "COMPLETE", result
    assert result["selected_day"] == day and result["blocker"] is None
    assert result["contract_fingerprint"] == contract_fingerprint
    assert compatible_evidence.issubset(result["evidence_store"])
    assert result["state_history"].count("PREFLIGHT") == 3
