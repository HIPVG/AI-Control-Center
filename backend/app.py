from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.orchestrator.engine import ControlCenterEngine, JsonStateStore

ROOT = Path(__file__).resolve().parent.parent
engine = ControlCenterEngine(JsonStateStore(ROOT / "state" / "control-center.json"), ROOT / "config" / "budget.yaml")

app = FastAPI(title="AI Control Center", version="0.1.0")
app.mount("/static", StaticFiles(directory=ROOT / "frontend"), name="static")


@app.get("/", include_in_schema=False)
def dashboard() -> FileResponse:
    return FileResponse(ROOT / "frontend" / "index.html")


@app.get("/api/status")
def status() -> dict:
    return engine.status()


@app.get("/api/plan")
def plan() -> dict:
    state = engine.status()
    return {"week": state["week"], "validation_day": state["validation_day"], "calendar_day": state["calendar_day"], "days": state["days"]}


@app.get("/api/tasks")
def tasks() -> list[dict]:
    return engine.status()["tasks"]


@app.get("/api/timeline")
def timeline() -> list[dict]:
    return [event.model_dump(mode="json") for event in engine.timeline]


@app.get("/api/token-usage")
def token_usage() -> dict:
    return engine.budgets.usage_view()


@app.get("/api/runtime")
def runtime() -> dict:
    return engine.runtime_view()


@app.post("/api/run/mock")
def run_mock() -> dict:
    return engine.run_mock()


@app.post("/api/run/codex-smoke")
def run_codex_smoke() -> dict:
    return engine.run_codex_smoke()


@app.post("/api/run/project-smoke/{project_id}")
def run_project_smoke(project_id: str) -> dict:
    return engine.run_project_smoke(project_id)


@app.get("/api/tasks/configured")
def configured_tasks() -> list[dict]:
    return engine.configured_tasks()


@app.post("/api/run/task/{task_id}")
def run_task(task_id: str) -> dict:
    return engine.run_task(task_id)


@app.post("/api/tasks/discover-failing/{discovery_id}")
def discover_failing_task(discovery_id: str) -> dict:
    return engine.discover_failing_task(discovery_id)


@app.post("/api/run/fault-repair/{fault_id}")
def run_fault_repair(fault_id: str) -> dict:
    return engine.run_fault_repair(fault_id)
