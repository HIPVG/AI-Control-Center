"""Disposable browser-E2E server with a persisted interrupted repair episode."""

from pathlib import Path
import runpy
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import backend.app as application
import uvicorn
from backend.control.day_action_registry import STRATEGIES
from backend.control.local_llm_day_program import LocalLLMDayProgram
from backend.control.solution_catalog import RepairEpisodeStore
from backend.models.local_llm_day import (
    DayIssueClassification,
    DynamicDayWorkOrder,
    LocalLLMDayState,
    LocalLLMDayWorkItem,
    LocalLLMWorkItemState,
    RepairEpisode,
)


base = Path("state").resolve() / f"browser-e2e-repair-{uuid.uuid4().hex}"
base.mkdir(parents=True, exist_ok=False)
helpers = runpy.run_path("tests/test_local_llm_day_program.py")
engine, root, _writer, builder = helpers["_repair_engine"](base)
runner = engine.local_llm_day_program
runner.smoke(6)
template = STRATEGIES[(6, "source_check")].template
order = DynamicDayWorkOrder(
    task_id="day-6-d6-temporal-state-design",
    allowed_files=list(template.allowed_output_scope),
    context_files=list(template.context_scope),
    acceptance_test_files=["tests/test_temporal_state.py"],
)
item = LocalLLMDayWorkItem(
    item_id="repair-D6_SOURCE_CHECK",
    title="interrupted repair",
    objective="repair deterministic failure",
    kind="DYNAMIC_ENGINEERING_WORK",
    dynamic_work_order=order,
    criterion_ids=[runner.snapshot.contract.completion_criteria[0].criterion_id],
    contract_day=6,
    contract_version=runner.snapshot.contract.version,
    state=LocalLLMWorkItemState.FAILED,
    evidence={"failure_excerpt": "fixed temporal assertion"},
)
runner.snapshot.work_items = [item]
episode = RepairEpisode(
    episode_id="browser-interrupted-repair",
    project_id="local_llm_lab",
    day=6,
    work_item_id=item.item_id,
    failure_class=DayIssueClassification.ENGINEERING_REPAIR,
    failure_fingerprint=runner._failure_fingerprint(item, "fixed temporal assertion"),
    failure_excerpt="fixed temporal assertion",
    started_at_epoch=0,
    repair_deadline_epoch=300,
    contract_version=runner.snapshot.contract.version,
    scope_fingerprint=runner._text_fingerprint(order.model_dump_json()),
)
episodes_path = base / "episodes.json"
runner.repair_episode_store = RepairEpisodeStore(episodes_path)
runner.repair_episode_store.save(episode)
runner.snapshot.repair_episode_ids = [episode.episode_id]
runner.snapshot.state = LocalLLMDayState.REPAIR_SUPERVISOR
runner.snapshot.contract_fingerprint = runner._contract_fingerprint(runner.snapshot.contract)
restored = LocalLLMDayProgram(
    root,
    saved=runner.view(),
    repair_episode_store=RepairEpisodeStore(episodes_path),
    repair_builder=builder,
    work_order_executor=engine._execute_local_llm_day_work_order,
    clock=lambda: 301.0,
)
engine.local_llm_day_program = restored
application.engine = engine
Path("state/browser-e2e-repair-fixture-root.txt").write_text(str(root), encoding="utf-8")
uvicorn.run(application.app, host="127.0.0.1", port=8769, log_level="info")
