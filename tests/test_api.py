import pytest
from fastapi.testclient import TestClient

import backend.app as control_app
from backend.orchestrator.engine import ControlCenterEngine


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(control_app, "engine", ControlCenterEngine())
    return TestClient(control_app.app)


def test_required_endpoints_are_available(client):
    for path in ("/api/status", "/api/plan", "/api/tasks", "/api/timeline", "/api/token-usage"):
        assert client.get(path).status_code == 200
    assert client.post("/api/run/mock").status_code == 200
    assert client.get("/").status_code == 200


def test_status_includes_timeline_for_dashboard_rendering(client):
    response = client.get("/api/status")
    assert "timeline" in response.json()
    assert isinstance(response.json()["timeline"], list)
