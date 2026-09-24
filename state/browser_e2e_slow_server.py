"""Disposable browser-E2E server: delayed work permits a real Stop click."""

from pathlib import Path
import runpy
import sys
import time
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import backend.app as application
import uvicorn


base = Path("state").resolve() / f"browser-e2e-slow-{uuid.uuid4().hex}"
base.mkdir(parents=True, exist_ok=False)
helpers = runpy.run_path("tests/test_local_llm_day_program.py")
root = helpers["_day1_repo"](base)
engine = helpers["_production_engine"](root, base)


def delayed_fixture_work(order):
    time.sleep(15)
    contract = engine.local_llm_day_program.snapshot.contract
    evidence_names = sorted(
        {
            evidence_name
            for criterion in contract.completion_criteria
            for evidence_name in criterion.required_evidence
        }
    )
    return {
        "final_result": "COMPLETE",
        "evidence": helpers["_valid_evidence"](evidence_names),
    }


engine.local_llm_day_program.work_order_executor = delayed_fixture_work
application.engine = engine
Path("state/browser-e2e-slow-fixture-root.txt").write_text(str(root), encoding="utf-8")
uvicorn.run(application.app, host="127.0.0.1", port=8767, log_level="info")
