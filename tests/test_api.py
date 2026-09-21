import pytest
from fastapi.testclient import TestClient

import backend.app as control_app
from backend.orchestrator.engine import ControlCenterEngine
from backend.models.runtime import RuntimeConfig


class StubDailyOperation:
    def autostart_status(self):
        return {"supported": True, "enabled": False, "task_name": "AI Control Center", "state": "NOT_ENABLED", "startup_diagnostics": [{"code": "LAUNCH_EXCEPTION", "reason": "PYTHON_INVOCATION_FAILED", "exception_type": "RuntimeException"}]}

    def enable_autostart(self):
        return {"supported": True, "enabled": True, "task_name": "AI Control Center", "state": "ENABLED", "action": "ENABLED", "startup_diagnostics": [{"code": "UVICORN_LAUNCHED", "value": 8000}]}


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(control_app, "engine", ControlCenterEngine(runtime_config=RuntimeConfig()))
    monkeypatch.setattr(control_app, "daily_operation", StubDailyOperation())
    return TestClient(control_app.app)


def test_required_endpoints_are_available(client):
    for path in ("/api/status", "/api/plan", "/api/tasks", "/api/timeline", "/api/token-usage", "/api/runtime", "/api/operation/health", "/api/day/plans", "/api/day/status", "/api/experiments", "/api/goals", "/api/next-action", "/api/git/candidates", "/api/git/completions", "/api/zero-touch"):
        assert client.get(path).status_code == 200
    assert client.post("/api/run/mock").status_code == 200
    assert client.post("/api/run/codex-smoke").json()["error_code"] == "REAL_MODE_REQUIRED"
    assert client.get("/").status_code == 200


def test_day_endpoints_accept_only_configured_plan_ids(client):
    assert client.post("/api/day/start/not-configured", json={"command": "unsafe"}).json()["error_code"] == "PLAN_NOT_CONFIGURED"
    assert client.post("/api/day/resume", json={"single_step": False}).json()["error_code"] == "NO_DAY_PLAN"
    assert client.post("/api/day/stop").status_code == 200


def test_day_mode_is_a_typed_query_not_a_browser_supplied_configuration_object(client):
    assert client.post("/api/day/start/not-configured?mode=continuous").json()["error_code"] == "PLAN_NOT_CONFIGURED"
    assert client.post("/api/day/start/not-configured?mode=unsafe").status_code == 422


def test_dashboard_v2_uses_only_configured_day_plan_api_contracts(client):
    plans = client.get("/api/day/plans").json()
    codex_core = next(plan for plan in plans if plan["plan_id"] == "week1-day3-local-llm-v3-codex-core")
    assert codex_core["architect_provider"] == "codex"
    html = (control_app.ROOT / "frontend" / "index.html").read_text(encoding="utf-8")
    script = (control_app.ROOT / "frontend" / "app.js").read_text(encoding="utf-8")
    assert 'id="run-day"' in html
    assert 'id="goal-input"' in html
    assert 'id="propose-goal"' in html
    assert 'id="execute-goal"' in html
    assert 'id="run-continuous"' in html
    assert 'id="stop-day"' in html
    assert 'id="server-health"' in html
    assert 'id="enable-autostart"' in html
    assert 'id="run-experiment"' in html
    assert 'id="validate-transient"' in html
    assert 'id="validate-replan"' in html
    assert 'id="validate-runtime"' in html
    assert 'id="continue-autonomously"' in html
    assert 'id="complete-verified-work"' in html
    assert 'id="validate-git-completion"' in html
    assert 'id="git-completion-evidence"' in html
    assert 'id="start-zero-touch"' in html
    assert 'id="continue-zero-touch"' in html
    assert 'id="zero-touch-evidence"' in html
    assert 'id="validation-evidence"' in html
    assert 'id="experiment-evidence"' in html
    assert "/api/day/start/" in script
    assert 'fetch("/api/goals"' in script
    assert 'fetch("/api/next-action")' in script
    assert 'fetch("/api/next-action/continue"' in script
    assert "/api/git/candidates" in script
    assert "/api/git/complete/" in script
    assert "/api/validation/git-completion" in script
    assert 'fetch("/api/zero-touch")' in script
    assert 'fetch("/api/zero-touch/start"' in script
    assert 'fetch("/api/zero-touch/continue"' in script
    assert "/execute" in script
    assert "/api/day/resume?mode=continuous" in script
    assert 'fetch("/api/day/stop"' in script
    assert "/api/operation/health" in script
    assert "/api/operation/autostart/enable" in script
    assert "DAILY_OPERATION_AUTOSTART" in script
    assert "startup_diagnostics" in script
    assert "continuous_mode_supported" in script
    assert "/api/experiments" in script
    assert "/api/validation/escalation/" in script
    assert "normal_day_unchanged" in script
    assert "auto_replans" in script
    assert "builder_invoked" in script
    assert "GIT_" in script
    assert "ZERO_TOUCH_" in script
    assert "/api/run/mock" not in script
    assert "innerHTML" not in script


def test_goal_endpoint_accepts_only_the_bounded_goal_field(client):
    rejected = client.post("/api/goals", json={"goal": "Run the trusted LocalLLM experiment", "command": "unsafe"})
    assert rejected.status_code == 422
    result = client.post("/api/goals", json={"goal": "Run the trusted LocalLLM process consistency experiment"})
    assert result.json()["status"] == "PROPOSED"
    assert "command" not in result.json()


def test_zero_touch_start_accepts_only_the_bounded_goal_field(client):
    response = client.post("/api/zero-touch/start", json={"goal": "Run the trusted LocalLLM experiment", "command": "unsafe"})
    assert response.status_code == 422


def test_continue_endpoint_uses_only_current_trusted_policy(client, monkeypatch):
    action = client.get("/api/next-action").json()
    assert action["action_type"] == "RUN_TRUSTED_EXPERIMENT"
    monkeypatch.setattr(control_app.engine, "run_experiment", lambda experiment_id: {"experiment_id": experiment_id, "outcome": "RESULT_RECORDED"})
    result = client.post("/api/next-action/continue", json={"command": "unsafe", "target_id": "unsafe"}).json()
    assert result["result"]["experiment_id"] == "local_llm_process_consistency_smoke"


def test_git_completion_endpoint_rejects_unknown_run_id_without_browser_supplied_git_data(client):
    response = client.post("/api/git/complete/not-a-verified-run", json={"branch": "main", "command": "unsafe", "path": "unsafe"})
    assert response.json()["error_code"] == "GIT_COMPLETION_NOT_READY"


def test_model_router_single_step_day_is_auditable_without_external_execution(monkeypatch):
    engine = ControlCenterEngine(runtime_config=RuntimeConfig())
    engine.day_runner.execute_task = lambda task_id, **kwargs: {
        "run_id": "mock-day-run", "task_id": task_id, "final_result": "COMPLETE_NO_CHANGE",
        "codex_attempts": [], "codex_invoked": False, "precheck_result": "PASS",
    }
    monkeypatch.setattr(control_app, "engine", engine)
    response = TestClient(control_app.app).post("/api/day/start/week1-day3-local-llm-v2?mode=single-step")
    assert response.status_code == 200
    body = response.json()
    assert body["state"] == "PAUSED"
    assert body["queue"][0]["task_id"] == "PC-001-A"
    assert body["queue"][0]["final_result"] == "COMPLETE_NO_CHANGE"
    assert body["architect_calls"] == 1
    assert body["codex_calls"] == 0
    assert body["evaluator_calls"] == 0
    assert [decision["role"] for decision in body["model_routing_decisions"]] == ["architect"]
    assert body["current_task"]["task_id"] == "PC-001-C"
    assert body["current_routing"]["provider"] == "codex"
    assert "human_review_queue" in TestClient(control_app.app).get("/api/day/status").json()
    assert any(event.event_type.value == "DAY_MODEL_ROUTING" for event in engine.timeline)
    assert any(event.event_type.value == "DAY_DETERMINISTIC_NO_AI" for event in engine.timeline)


def test_status_includes_timeline_for_dashboard_rendering(client):
    response = client.get("/api/status")
    assert "timeline" in response.json()
    assert isinstance(response.json()["timeline"], list)


def test_health_and_autostart_endpoints_expose_only_fixed_operation_state(client):
    health = client.get("/api/operation/health").json()
    assert health["server_state"] == "HEALTHY"
    assert health["autostart"]["task_name"] == "AI Control Center"
    enabled = client.post("/api/operation/autostart/enable").json()
    assert enabled["action"] == "ENABLED"
    assert any(event.event_type.value == "DAILY_OPERATION_AUTOSTART" for event in control_app.engine.timeline)


def test_codex_smoke_endpoint_does_not_accept_browser_supplied_commands(client):
    response = client.post("/api/run/codex-smoke", json={"command": "unsafe", "prompt": "unsafe"})
    assert response.status_code == 200
    assert response.json()["error_code"] == "REAL_MODE_REQUIRED"


def test_project_smoke_endpoint_accepts_only_configured_path_parameter(client):
    unknown = client.post("/api/run/project-smoke/not-configured", json={"path": "C:/unsafe", "command": "unsafe", "prompt": "unsafe"})
    assert unknown.status_code == 200
    assert unknown.json()["error_code"] == "PROJECT_NOT_CONFIGURED"
    configured = client.post("/api/run/project-smoke/local_llm_lab", json={"path": "C:/unsafe"})
    assert configured.status_code == 200
    assert configured.json()["error_code"] == "REAL_MODE_REQUIRED"


def test_configured_tasks_endpoint_hides_commands_and_task_endpoint_rejects_request_injection(client):
    configured = client.get("/api/tasks/configured")
    assert configured.status_code == 200
    assert configured.json()[0]["task_id"] == "PC-001-A"
    assert "argv" not in configured.json()[0]
    unknown = client.post("/api/run/task/not-configured", json={"command": "unsafe", "path": "C:/unsafe"})
    assert unknown.status_code == 200
    assert unknown.json()["error_code"] == "TASK_NOT_CONFIGURED"
    selected = client.post("/api/run/task/PC-001-A", json={"command": "unsafe", "path": "C:/unsafe"})
    assert selected.status_code == 200
    assert selected.json()["error_code"] == "REAL_MODE_REQUIRED"


def test_discovery_endpoint_accepts_only_a_configured_discovery_id(client):
    response = client.post("/api/tasks/discover-failing/not-configured", json={"command": "unsafe", "cases": ["unsafe"]})
    assert response.status_code == 200
    assert response.json()["error_code"] == "DISCOVERY_NOT_CONFIGURED"


def test_fault_repair_endpoint_accepts_only_a_configured_fault_id(client):
    response = client.post("/api/run/fault-repair/not-configured", json={"target_file": "unsafe", "mutation": "unsafe"})
    assert response.status_code == 200
    assert response.json()["error_code"] == "FAULT_NOT_CONFIGURED"
