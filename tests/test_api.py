import pytest
from fastapi.testclient import TestClient

import backend.app as control_app
from backend.orchestrator.engine import ControlCenterEngine
from backend.models.runtime import RuntimeConfig


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(control_app, "engine", ControlCenterEngine(runtime_config=RuntimeConfig()))
    return TestClient(control_app.app)


def test_required_endpoints_are_available(client):
    for path in ("/api/status", "/api/plan", "/api/tasks", "/api/timeline", "/api/token-usage", "/api/runtime"):
        assert client.get(path).status_code == 200
    assert client.post("/api/run/mock").status_code == 200
    assert client.post("/api/run/codex-smoke").json()["error_code"] == "REAL_MODE_REQUIRED"
    assert client.get("/").status_code == 200


def test_status_includes_timeline_for_dashboard_rendering(client):
    response = client.get("/api/status")
    assert "timeline" in response.json()
    assert isinstance(response.json()["timeline"], list)


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
