from pathlib import Path

from backend.control.projects import ConfiguredProject, ProjectRegistry
from backend.models.runtime import RuntimeConfig
from backend.orchestrator.engine import ControlCenterEngine, JsonStateStore


def scenario_engine(tmp_path: Path) -> ControlCenterEngine:
    local_lab = tmp_path / "local-llm-lab"
    local_lab.mkdir()
    return ControlCenterEngine(
        JsonStateStore(tmp_path / "state" / "control-center.json"),
        runtime_config=RuntimeConfig(),
        project_registry=ProjectRegistry(projects={
            "local_llm_lab": ConfiguredProject(name="LocalLLM-Lab", path=local_lab, default_branch="main"),
        }),
    )


def test_checkpoint_scenario_is_the_default_read_only_primary_path(tmp_path):
    engine = scenario_engine(tmp_path)
    assert engine.scenario_view()["active_scenario_id"] == "local-llm-research-checkpoint"
    action = engine.next_action()
    assert action["action_type"] == "NO_FURTHER_ACTION"
    assert action["policy_result"] == "SCENARIO_CHECKPOINT_READ_ONLY"


def test_repeat_scenario_runs_a_configured_capability_and_persists_completion(monkeypatch, tmp_path):
    state_path = tmp_path / "state" / "control-center.json"
    engine = scenario_engine(tmp_path)
    assert engine.activate_scenario("local-llm-smoke-iterations")["active_scenario_id"] == "local-llm-smoke-iterations"
    monkeypatch.setattr(engine, "_preflight_local_runtime", lambda: {"state": "READY"})
    monkeypatch.setattr(engine, "run_experiment", lambda experiment_id: {
        "experiment_id": experiment_id, "outcome": "RESULT_RECORDED", "artifact_path": "results/run",
        "response_count": 4, "success_count": 4, "failed_count": 0, "classification_reason": "completed",
    })
    for _ in range(3):
        assert engine.next_action()["target_id"] == "local_llm_process_consistency_smoke"
        assert engine.continue_autonomously()["result"]["outcome"] == "RESULT_RECORDED"
    assert engine.next_action()["policy_result"] == "SCENARIO_COMPLETE"

    resumed = ControlCenterEngine(
        JsonStateStore(state_path), runtime_config=RuntimeConfig(),
        project_registry=engine.projects,
    )
    assert resumed.scenario_view()["active_scenario_id"] == "local-llm-smoke-iterations"
    assert len(resumed.scenario_view()["runs"]["local-llm-smoke-iterations"]) == 3
