from datetime import datetime, timedelta, timezone
from pathlib import Path
import shutil
import subprocess

from fastapi.testclient import TestClient

import backend.app as control_app
from backend.control.human_decision import DecisionRequest, HumanResponse, SubjectType
from backend.control.projects import ConfiguredProject, ProjectRegistry
from backend.control.run_composition import RunPreflightFacts
from backend.control.run_store import JsonRunStore
from backend.control.run_telemetry_store import JsonRunTelemetryStore
from backend.models.local_llm_day import (
    LocalLLMDaySnapshot,
    LocalLLMDayState,
    RunTelemetry,
    TelemetryMetric,
)
from backend.models.runtime import RuntimeConfig
from backend.orchestrator.engine import ControlCenterEngine, JsonStateStore


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "day-contract"
NOW = datetime(2026, 9, 29, 12, 0, tzinfo=timezone.utc)


def _engine(tmp_path, *, admitted=True, default_executor=False):
    holder = {}
    calls = []

    def execute(run_id, day):
        engine = holder["engine"]
        contract = engine.local_llm_day_program._load_contracts()[day]
        engine.local_llm_day_program.snapshot = LocalLLMDaySnapshot(
            run_id=run_id,
            selected_day=day,
            state=LocalLLMDayState.PREFLIGHT,
            objective=contract.objective,
            contract=contract,
            contract_fingerprint=engine.local_llm_day_program._contract_fingerprint(contract),
            activity="Injected executor reached the production composition root.",
        )
        engine.local_llm_day_program._save()
        calls.append((run_id, day))
        return {"run_id": run_id, "result": "INJECTED_ONLY"}

    fixture_repository = tmp_path / "repository"
    if not fixture_repository.exists():
        shutil.copytree(FIXTURE_ROOT, fixture_repository)
        subprocess.run(
            ["git", "init", "-b", "main", str(fixture_repository)],
            check=True, capture_output=True, text=True,
        )
        subprocess.run(
            ["git", "-C", str(fixture_repository), "config", "user.name", "Fixture"],
            check=True, capture_output=True, text=True,
        )
        subprocess.run(
            ["git", "-C", str(fixture_repository), "config", "user.email", "fixture@example.invalid"],
            check=True, capture_output=True, text=True,
        )
        subprocess.run(
            ["git", "-C", str(fixture_repository), "add", "."],
            check=True, capture_output=True, text=True,
        )
        subprocess.run(
            ["git", "-C", str(fixture_repository), "commit", "-m", "fixture baseline"],
            check=True, capture_output=True, text=True,
        )
    registry = ProjectRegistry(projects={
        "local_llm_lab": ConfiguredProject(
            name="LocalLLM-Lab", path=fixture_repository.resolve(), default_branch="main"
        )
    })
    engine_kwargs = dict(
        state_store=JsonStateStore(tmp_path / "control-center.json"),
        runtime_config=RuntimeConfig(),
        project_registry=registry,
        local_llm_run_store=JsonRunStore(tmp_path / "runs"),
        local_llm_telemetry_store=JsonRunTelemetryStore(tmp_path / "telemetry"),
        local_llm_preflight_resolver=lambda _day: RunPreflightFacts(admitted, admitted),
    )
    if not default_executor:
        engine_kwargs["local_llm_run_executor"] = execute
    engine = ControlCenterEngine(**engine_kwargs)
    holder["engine"] = engine
    return engine, calls


def test_default_async_worker_projects_settled_real_mode_blocker_once(tmp_path):
    engine, injected_calls = _engine(tmp_path, default_executor=True)
    client, restore = _api(engine)
    try:
        go = client.post("/api/local-llm/day/go", json={"selected_day": 6}).json()
        run_id = go["run_id"]

        assert go["execution_started"] is True
        assert go["run_record"]["control"]["current_state"] == "PREFLIGHT"
        assert injected_calls == []

        engine.local_llm_day_program._thread.join(5)
        assert not engine.local_llm_day_program._thread.is_alive()
        readback = client.get("/api/local-llm/runs").json()

        assert readback["current"]["run_id"] == run_id
        assert readback["current"]["state"] == "EXTERNAL_ACTION_REQUIRED"
        assert readback["current"]["blocker"] == "REAL_MODE_REQUIRED"
        projection_events = [
            event for event in engine.timeline
            if event.event_type.value == "DETERMINISTIC_CHECK"
            and event.details.get("check") == "DAY_STATE_SETTLEMENT_PROJECTION"
            and event.details.get("run_id") == run_id
        ]
        assert len(projection_events) == 1
        assert projection_events[0].details["outcome"] == "ACCEPTED"

        restarted, restarted_calls = _engine(tmp_path, default_executor=True)
        restarted_readback = restarted.local_llm_run_read_model()
        assert restarted_calls == []
        assert restarted_readback["current"]["run_id"] == run_id
        assert restarted_readback["current"]["state"] == "EXTERNAL_ACTION_REQUIRED"
        assert restarted_readback["current"]["blocker"] == "REAL_MODE_REQUIRED"
    finally:
        restore()


def _api(engine):
    previous = control_app.engine
    control_app.engine = engine
    client = TestClient(control_app.app)

    def restore():
        client.close()
        control_app.engine = previous

    return client, restore


def _evidence(run_id, criterion_id, evidence_type, config_fingerprint, value):
    return {
        "run_id": run_id,
        "criterion_id": criterion_id,
        "evidence_type": evidence_type,
        "provider_id": "ri03-injected-executor",
        "provider_version": "v1",
        "source_fingerprint": "s" * 64,
        "configuration_fingerprint": config_fingerprint,
        "value": value,
    }


def _evidence_value(evidence_type):
    return {
        "schema_contract": {"schema_path": "schema.json", "schema_version": "v1"},
        "source_check": {"checked_paths": ["src/state.py"], "assertions": ["states differ"]},
        "provenance_test": {"exit_code": 0, "commands": ["pytest provenance"], "passed": 1, "failed": 0},
        "deterministic_tests": {"exit_code": 0, "commands": ["pytest temporal"], "passed": 1, "failed": 0},
        "architecture_check": {"checked_documents": ["docs/architecture.md"], "assertions": ["server owns state"]},
    }[evidence_type]


def _metric(value, unit, source):
    return TelemetryMetric(value=value, unit=unit, source=source, observed_at=NOW)


def _terminal_task_record(product_run_id, **updates):
    record = {
        "product_run_id": product_run_id,
        "run_id": "task-run-day6",
        "end_time": NOW.isoformat(),
        "final_result": "COMPLETE",
        "codex_attempts": [{
            "attempt": 1,
            "gross_input_tokens": 528695,
            "cached_input_tokens": 474112,
            "uncached_input_tokens": 54583,
            "output_tokens": 8131,
        }],
        "gross_input_tokens": 528695,
        "cached_input_tokens": 474112,
        "uncached_input_tokens": 54583,
        "output_tokens": 8131,
        "budget_warning": "TASK_BUDGET_EXCEEDED",
    }
    record.update(updates)
    return record


def _install_integrated_terminal_executor(engine, calls, *, evidence_mode="valid"):
    """Inject one deterministic Day effect through the production coordinator."""
    def execute(run_id, day):
        contract = engine.local_llm_day_program._load_contracts()[day]
        engine.local_llm_day_program.snapshot = LocalLLMDaySnapshot(
            run_id=run_id,
            selected_day=day,
            state=LocalLLMDayState.PREFLIGHT,
            objective=contract.objective,
            contract=contract,
            contract_fingerprint=engine.local_llm_day_program._contract_fingerprint(contract),
            activity="Integrated deterministic executor entered the product boundary.",
        )
        all_required = sorted({
            evidence_type
            for criterion in contract.completion_criteria
            for evidence_type in criterion.required_evidence
        })
        legacy = {
            evidence_type: {
                "evidence_type": evidence_type,
                "value": _evidence_value(evidence_type),
                "source": "PR-03 integrated fixture",
                "verified": True,
                "validation": {"passed": True, "validator": "deterministic fixture"},
            }
            for evidence_type in all_required
        }
        if evidence_mode == "incomplete":
            legacy.pop(all_required[-1])
        engine.local_llm_day_program._ingest_legacy_evidence(
            contract,
            legacy,
            provider_id="pr03-integrated-executor",
            source_fingerprint="p" * 64,
        )
        engine.local_llm_day_program._evaluate_contract(contract, {})
        if evidence_mode == "cross-run":
            criterion = contract.completion_criteria[0]
            evidence_id = next(iter(criterion.evidence_record_ids.values()))
            source = engine.local_llm_day_program.snapshot.evidence_store[evidence_id]
            engine.local_llm_day_program.snapshot.evidence_store[evidence_id] = source.model_copy(
                update={"run_id": "run-other", "criterion_id": criterion.criterion_id}
            )
        engine.local_llm_day_program.snapshot.state = LocalLLMDayState.COMPLETE
        engine.local_llm_day_program.snapshot.activity = "Integrated fixture reached terminal save."
        engine.local_llm_day_program._save()
        engine.data["task_runs"] = [_terminal_task_record(run_id)]
        engine._save()
        calls.append((run_id, day))
        settlement = engine._settle_local_llm_product_run(run_id)
        return {"run_id": run_id, "result": "DETERMINISTIC_TERMINAL", "settlement": settlement}

    engine.local_llm_run_coordinator.executor = execute


def _satisfy_product_criteria(engine, run_id):
    record = engine.local_llm_run_store.get(run_id)
    contract = engine.local_llm_day_program.snapshot.contract
    for criterion in contract.completion_criteria:
        results = [
            _evidence(
                run_id,
                criterion.criterion_id,
                evidence_type,
                record.intent.config_fingerprint,
                _evidence_value(evidence_type),
            )
            for evidence_type in criterion.required_evidence
        ]
        outcome = engine.local_llm_run_product.execution.evaluate_criterion(
            run_id, criterion_id=criterion.criterion_id, results=results
        )
        assert outcome["criterion_satisfied"] is True


def test_integrated_fastapi_product_boundary_settles_once_and_survives_reconstruction(tmp_path):
    engine, calls = _engine(tmp_path)
    _install_integrated_terminal_executor(engine, calls)
    client, restore = _api(engine)
    try:
        before = client.get("/api/local-llm/runs").json()
        go = client.post("/api/local-llm/day/go", json={"selected_day": 6}).json()
        run_id = go["run_id"]
        readback = client.get("/api/local-llm/runs").json()
        versions_before_replay = engine.local_llm_run_store.versions(run_id)
        day_before_replay = engine.local_llm_day_program.snapshot.model_dump_json()
        replay = engine._settle_local_llm_product_run(run_id)

        assert before["selected"] is False
        assert go["execution_started"] is True
        assert calls == [(run_id, 6)]
        assert go["execution"]["settlement"]["stage"] == "PROJECTED"
        assert readback["current"]["run_id"] == run_id
        assert readback["current"]["state"] == "COMPLETE"
        assert readback["telemetry"]["run_id"] == run_id
        assert readback["telemetry"]["attempt_count"]["value"] == 1
        assert readback["telemetry"]["input_tokens"]["value"] == 528695
        assert readback["telemetry"]["budget_decision"]["value"] == "TASK_BUDGET_EXCEEDED"
        assert readback["telemetry"]["cost"]["value"] is None
        assert readback["telemetry"]["cost"]["unknown_reason"]
        assert readback["unmet_criteria"] == []
        assert all(
            evidence.run_id == run_id and evidence.criterion_id == criterion.criterion_id
            for criterion in engine.local_llm_day_program.snapshot.contract.completion_criteria
            for evidence_id in criterion.evidence_record_ids.values()
            for evidence in [engine.local_llm_day_program.snapshot.evidence_store[evidence_id]]
        )
        assert replay["stage"] == "ALREADY_PROJECTED"
        assert engine.local_llm_run_store.versions(run_id) == versions_before_replay
        assert engine.local_llm_day_program.snapshot.model_dump_json() == day_before_replay

        restarted, restarted_calls = _engine(tmp_path)
        reconstructed = restarted.local_llm_run_read_model()
        assert restarted_calls == []
        assert reconstructed["projected_at"] != readback["projected_at"]
        assert {key: value for key, value in reconstructed.items() if key != "projected_at"} == {
            key: value for key, value in readback.items() if key != "projected_at"
        }
    finally:
        restore()


def test_integrated_settlement_failures_never_create_terminal_product_state(tmp_path):
    for mode, reason in (
        ("incomplete", "DAY_EVIDENCE_SOURCE_INVALID"),
        ("cross-run", "DAY_EVIDENCE_SOURCE_BINDING_MISMATCH"),
    ):
        engine, calls = _engine(tmp_path / mode)
        _install_integrated_terminal_executor(engine, calls, evidence_mode=mode)
        client, restore = _api(engine)
        try:
            go = client.post("/api/local-llm/day/go", json={"selected_day": 6}).json()
            run_id = go["run_id"]
            settlement = go["execution"]["settlement"]
            assert calls == [(run_id, 6)]
            assert settlement["outcome"] == "REJECTED"
            assert settlement["reason_code"] == reason
            assert engine.local_llm_run_store.get(run_id).control.current_state == LocalLLMDayState.PREFLIGHT
            assert engine.local_llm_telemetry_store.get(run_id) is None
        finally:
            restore()

    engine, _calls = _engine(tmp_path / "ordering")
    client, restore = _api(engine)
    try:
        run_id = client.post("/api/local-llm/day/go", json={"selected_day": 6}).json()["run_id"]
        before = engine.local_llm_run_store.get(run_id)
        early = engine.local_llm_run_product.settle_terminal_run(
            run_id, [_terminal_task_record(run_id)]
        )
        assert early["control"]["current_state"] == "PREFLIGHT"
        assert engine.local_llm_run_store.get(run_id).control.current_state == LocalLLMDayState.PREFLIGHT
        assert engine.local_llm_telemetry_store.get(run_id) is None

        _satisfy_product_criteria(engine, run_id)
        engine.local_llm_day_program.snapshot.state = LocalLLMDayState.COMPLETE
        engine.local_llm_day_program._save()
        engine.data["task_runs"] = [_terminal_task_record(run_id)]
        settled = engine._settle_local_llm_product_run(run_id)
        complete = engine.local_llm_run_store.get(run_id)
        conflicting = _terminal_task_record(
            run_id,
            codex_attempts=[{
                "attempt": 1,
                "gross_input_tokens": 528696,
                "cached_input_tokens": 474112,
                "uncached_input_tokens": 54584,
                "output_tokens": 8131,
            }],
            gross_input_tokens=528696,
            uncached_input_tokens=54584,
        )
        engine.data["task_runs"] = [conflicting]
        conflict = engine._settle_local_llm_product_run(run_id)
        assert settled["stage"] == "PROJECTED"
        assert conflict["reason_code"] == "TELEMETRY_CONFLICT"
        assert engine.local_llm_run_store.get(run_id) == complete
        assert before.intent.run_id == complete.intent.run_id
    finally:
        restore()


def test_terminal_settlement_orders_evidence_telemetry_projection_and_replays_once(tmp_path):
    engine, _calls = _engine(tmp_path)
    client, restore = _api(engine)
    try:
        run_id = client.post("/api/local-llm/day/go", json={"selected_day": 6}).json()["run_id"]
        _satisfy_product_criteria(engine, run_id)
        engine.local_llm_day_program.snapshot.state = LocalLLMDayState.COMPLETE
        engine.local_llm_day_program.snapshot.activity = "Terminal Day snapshot saved."
        engine.local_llm_day_program._save()
        engine.data["task_runs"] = [_terminal_task_record(run_id)]

        original_project = engine.local_llm_run_product.execution.project_day_state
        observed_order = []

        def project_after_reconciliation(value):
            observed_order.append("projection")
            assert engine.local_llm_telemetry_store.get(value) is not None
            assert engine.local_llm_run_product.execution._completion_ready(
                engine.local_llm_run_store.get(value)
            )
            return original_project(value)

        engine.local_llm_run_product.execution.project_day_state = project_after_reconciliation
        settled = engine._settle_local_llm_product_run(run_id)
        fixed = engine.local_llm_run_store.get(run_id)
        snapshot_before_replay = engine.local_llm_day_program.snapshot.model_dump_json()
        replay = engine._settle_local_llm_product_run(run_id)

        assert settled["outcome"] == "ACCEPTED"
        assert settled["stage"] == "PROJECTED"
        assert observed_order == ["projection"]
        assert fixed.control.current_state == LocalLLMDayState.COMPLETE
        assert replay["stage"] == "ALREADY_PROJECTED"
        assert replay["telemetry_replay"] is True
        assert engine.local_llm_run_store.get(run_id) == fixed
        assert engine.local_llm_day_program.snapshot.model_dump_json() == snapshot_before_replay
        assert all(
            evidence.run_id == run_id and evidence.criterion_id == criterion.criterion_id
            for criterion in engine.local_llm_day_program.snapshot.contract.completion_criteria
            for evidence_id in criterion.evidence_record_ids.values()
            for evidence in [engine.local_llm_day_program.snapshot.evidence_store[evidence_id]]
        )

        conflicting = _terminal_task_record(
            run_id,
            codex_attempts=[{
                "attempt": 1,
                "gross_input_tokens": 528696,
                "cached_input_tokens": 474112,
                "uncached_input_tokens": 54584,
                "output_tokens": 8131,
            }],
            gross_input_tokens=528696,
            uncached_input_tokens=54584,
        )
        engine.data["task_runs"] = [conflicting]
        conflict = engine._settle_local_llm_product_run(run_id)
        assert conflict["reason_code"] == "TELEMETRY_CONFLICT"
        assert engine.local_llm_day_program.snapshot.model_dump_json() == snapshot_before_replay
        assert engine.local_llm_run_store.get(run_id) == fixed

        engine.data["task_runs"] = [_terminal_task_record(run_id)]
        criterion = engine.local_llm_day_program.snapshot.contract.completion_criteria[0]
        evidence_id = next(iter(criterion.evidence_record_ids.values()))
        source = engine.local_llm_day_program.snapshot.evidence_store[evidence_id]
        engine.local_llm_day_program.snapshot.evidence_store[evidence_id] = source.model_copy(
            update={"source_fingerprint": "x" * 64, "observation_fingerprint": "x" * 64}
        )
        conflicting_snapshot = engine.local_llm_day_program.snapshot.model_dump_json()
        evidence_conflict = engine._settle_local_llm_product_run(run_id)
        assert evidence_conflict["reason_code"] == "BOUND_EVIDENCE_CONFLICT"
        assert engine.local_llm_day_program.snapshot.model_dump_json() == conflicting_snapshot
        assert engine.local_llm_run_store.get(run_id) == fixed
    finally:
        restore()


def test_terminal_settlement_rejects_missing_same_run_task_before_projection(tmp_path):
    engine, _calls = _engine(tmp_path)
    client, restore = _api(engine)
    try:
        run_id = client.post("/api/local-llm/day/go", json={"selected_day": 6}).json()["run_id"]
        _satisfy_product_criteria(engine, run_id)
        engine.local_llm_day_program.snapshot.state = LocalLLMDayState.COMPLETE
        engine.local_llm_day_program._save()
        engine.data["task_runs"] = [_terminal_task_record("run-other")]
        before = engine.local_llm_run_store.get(run_id)

        rejected = engine._settle_local_llm_product_run(run_id)

        assert rejected == {
            "outcome": "REJECTED",
            "reason_code": "TERMINAL_TASK_RECORDS_MISSING",
            "run_id": run_id,
            "stage": "TELEMETRY",
        }
        assert engine.local_llm_run_store.get(run_id) == before
        assert engine.local_llm_telemetry_store.get(run_id) is None
    finally:
        restore()


def test_terminal_task_telemetry_reconciles_same_run_and_survives_restart(tmp_path):
    engine, _calls = _engine(tmp_path)
    client, restore = _api(engine)
    try:
        run_id = client.post("/api/local-llm/day/go", json={"selected_day": 6}).json()["run_id"]
        engine.local_llm_day_program.snapshot.state = LocalLLMDayState.COMPLETE
        engine.local_llm_day_program._save()
        record = _terminal_task_record(run_id)
        known_cost = engine.local_llm_run_product._terminal_telemetry(
            engine.local_llm_run_store.get(run_id).intent,
            [_terminal_task_record(run_id, measured_cost=0.25, cost_currency="JPY")],
        )

        result = engine.local_llm_run_product.reconcile_terminal_telemetry(run_id, [record])
        readback = client.get("/api/local-llm/runs").json()["telemetry"]
        replay = engine.local_llm_run_product.reconcile_terminal_telemetry(run_id, [record])

        assert result == {"outcome": "ACCEPTED", "run_id": run_id, "replay": False}
        assert known_cost.cost.value == 0.25
        assert known_cost.cost.unit == "JPY"
        assert known_cost.cost.source.startswith("terminal task records:")
        assert replay == {"outcome": "ACCEPTED", "run_id": run_id, "replay": True}
        assert readback["schema_version"] == 2
        assert readback["run_id"] == run_id
        assert readback["attempt_count"]["value"] == 1
        assert readback["attempt_limit"]["value"] == 2
        assert readback["input_tokens"]["value"] == 528695
        assert readback["cached_input_tokens"]["value"] == 474112
        assert readback["uncached_input_tokens"]["value"] == 54583
        assert readback["output_tokens"]["value"] == 8131
        assert readback["budget_decision"]["value"] == "TASK_BUDGET_EXCEEDED"
        assert readback["cost"]["value"] is None
        assert readback["cost"]["unknown_reason"] == (
            "terminal task records did not expose measured cost"
        )
        assert readback["attempt_count"]["source"].startswith("terminal task records:")

        restarted, restarted_calls = _engine(tmp_path)
        restarted_readback = restarted.local_llm_run_read_model()["telemetry"]
        assert restarted_calls == []
        assert restarted_readback == readback

        conflicting = _terminal_task_record(
            run_id,
            codex_attempts=[{
                "attempt": 1,
                "gross_input_tokens": 528696,
                "cached_input_tokens": 474112,
                "uncached_input_tokens": 54584,
                "output_tokens": 8131,
            }],
            gross_input_tokens=528696,
            uncached_input_tokens=54584,
        )
        conflict = engine.local_llm_run_product.reconcile_terminal_telemetry(
            run_id, [conflicting]
        )
        assert conflict["reason_code"] == "TELEMETRY_CONFLICT"
        assert client.get("/api/local-llm/runs").json()["telemetry"] == readback
    finally:
        restore()


def test_terminal_task_telemetry_rejects_cross_run_and_inconsistent_facts(tmp_path):
    engine, _calls = _engine(tmp_path)
    client, restore = _api(engine)
    try:
        run_id = client.post("/api/local-llm/day/go", json={"selected_day": 6}).json()["run_id"]
        engine.local_llm_day_program.snapshot.state = LocalLLMDayState.COMPLETE
        engine.local_llm_day_program._save()

        wrong_run = engine.local_llm_run_product.reconcile_terminal_telemetry(
            run_id, [_terminal_task_record("run-other")]
        )
        inconsistent = engine.local_llm_run_product.reconcile_terminal_telemetry(
            run_id, [_terminal_task_record(run_id, gross_input_tokens=1)]
        )
        duplicate = engine.local_llm_run_product.reconcile_terminal_telemetry(
            run_id, [_terminal_task_record(run_id), _terminal_task_record(run_id)]
        )
        nonterminal = engine.local_llm_run_product.reconcile_terminal_telemetry(
            run_id, [_terminal_task_record(run_id, final_result="RUNNING")]
        )
        incomplete_cost = engine.local_llm_run_product.reconcile_terminal_telemetry(
            run_id,
            [
                _terminal_task_record(run_id, run_id="task-one", measured_cost=0, cost_currency="JPY"),
                _terminal_task_record(run_id, run_id="task-two"),
            ],
        )

        assert wrong_run["reason_code"] == "TERMINAL_TASK_RUN_ID_MISMATCH"
        assert inconsistent["reason_code"] == "TERMINAL_TASK_TOKEN_TOTAL_INVALID"
        assert duplicate["reason_code"] == "TERMINAL_TASK_ID_INVALID_OR_DUPLICATE"
        assert nonterminal["reason_code"] == "TERMINAL_TASK_NOT_TERMINAL"
        assert incomplete_cost["reason_code"] == "TERMINAL_TASK_COST_INCOMPLETE"
        assert engine.local_llm_telemetry_store.get(run_id) is None
    finally:
        restore()


def test_actual_api_to_evidence_telemetry_terminal_readback_uses_one_run(tmp_path):
    engine, calls = _engine(tmp_path)
    client, restore = _api(engine)
    try:
        before = client.get("/api/local-llm/runs").json()
        go = client.post("/api/local-llm/day/go", json={"selected_day": 6}).json()
        run_id = go["run_id"]

        assert before["selected"] is False
        assert go["execution_started"] is True
        assert calls == [(run_id, 6)]
        assert go["execution"]["run_id"] == run_id

        record = engine.local_llm_run_store.get(run_id)
        contract = engine.local_llm_day_program.snapshot.contract
        for criterion in contract.completion_criteria:
            results = [
                _evidence(
                    run_id, criterion.criterion_id, evidence_type,
                    record.intent.config_fingerprint, _evidence_value(evidence_type),
                )
                for evidence_type in criterion.required_evidence
            ]
            result = engine.local_llm_run_product.execution.evaluate_criterion(
                run_id, criterion_id=criterion.criterion_id, results=results
            )
            assert result["criterion_satisfied"] is True

        engine.local_llm_day_program.snapshot.state = LocalLLMDayState.COMPLETE
        engine.local_llm_day_program.snapshot.activity = "All declared evidence validated."
        engine.local_llm_day_program._save()
        projected = engine.local_llm_run_product.execution.project_day_state(run_id)
        telemetry = RunTelemetry(
            run_id=run_id,
            manual_relay_count=_metric(0, "count", "RI-03 fixture"),
            attempt_count=_metric(1, "attempts", "RI-03 fixture"),
            attempt_limit=_metric(2, "attempts", "RunIntent"),
            input_tokens=TelemetryMetric(value=None, unit="tokens", observed_at=NOW, unknown_reason="not measured"),
            output_tokens=TelemetryMetric(value=None, unit="tokens", observed_at=NOW, unknown_reason="not measured"),
            cost=_metric(0, "JPY", "authorized fixture limit"),
            captured_at=NOW,
        )
        assert engine.local_llm_run_product.record_telemetry(run_id, telemetry)["outcome"] == "ACCEPTED"
        readback = client.get("/api/local-llm/runs").json()

        assert projected["control"]["current_state"] == "COMPLETE"
        assert readback["current"]["run_id"] == run_id
        assert readback["current"]["state"] == "COMPLETE"
        assert readback["telemetry"]["run_id"] == run_id
        assert readback["unmet_criteria"] == []

        restarted, restarted_calls = _engine(tmp_path)
        restarted_readback = restarted.local_llm_run_read_model()
        assert restarted_calls == []
        assert restarted_readback["current"]["run_id"] == run_id
        assert restarted_readback["current"]["state"] == "COMPLETE"
        assert restarted_readback["telemetry"]["run_id"] == run_id
    finally:
        restore()


def test_failure_controls_preserve_one_run_and_reject_unauthorized_effects(tmp_path):
    engine, calls = _engine(tmp_path)
    client, restore = _api(engine)
    try:
        go = client.post("/api/local-llm/day/go", json={"selected_day": 6}).json()
        run_id = go["run_id"]
        record = engine.local_llm_run_store.get(run_id)
        criterion = engine.local_llm_day_program.snapshot.contract.completion_criteria[0]
        invalid = [_evidence(
            "other-run", criterion.criterion_id, criterion.required_evidence[0],
            record.intent.config_fingerprint, _evidence_value(criterion.required_evidence[0]),
        )]
        rejected = engine.local_llm_run_product.execution.evaluate_criterion(
            run_id, criterion_id=criterion.criterion_id, results=invalid
        )
        assert rejected["criterion_satisfied"] is False
        assert engine.local_llm_run_store.get(run_id).control.current_state == LocalLLMDayState.PREFLIGHT

        execution = engine.local_llm_run_product.execution
        execution.begin_repair(run_id, allowed_paths={"src/temporal.py"})
        attempt = {
            "run_id": run_id, "selected_day": 6,
            "failure_fingerprint": "failure-0001", "action_fingerprint": "action-00001",
            "changed_paths": ["src/temporal.py"], "git_fingerprint": record.intent.git_fingerprint,
            "active_work_seconds": 60, "verification_passed": False,
        }
        execution.record_repair_attempt(run_id, attempt)
        second = execution.record_repair_attempt(run_id, {**attempt, "action_fingerprint": "action-00002"})
        third = execution.record_repair_attempt(run_id, {**attempt, "action_fingerprint": "action-00003"})
        assert second["status"] == "HUMAN_ACTION_REQUIRED"
        assert third["reason_code"] == "ATTEMPT_LIMIT_EXHAUSTED"

        execution.request_review(run_id, "REPORT-RI03", at=NOW)
        stale = execution.apply_review_response(
            run_id, {"response_id": "RESP-OLD", "in_reply_to": "REPORT-OLD", "result": "CONTINUE"},
            comment_id="COMMENT-OLD", at=NOW + timedelta(seconds=1), exit_code=0,
            envelope_valid=True, envelope_validation_reason="valid",
            downstream_effect_id="EFFECT-OLD", observed_effect_id="EFFECT-OLD",
        )
        assert stale["reason_code"] == "IN_REPLY_TO_MISMATCH"
        waiting = engine.local_llm_run_store.get(run_id)
        assert waiting.control.current_state == LocalLLMDayState.HUMAN_ACTION_REQUIRED

        matched = execution.apply_review_response(
            run_id, {"response_id": "RESP-RI03", "in_reply_to": "REPORT-RI03", "result": "CONTINUE"},
            comment_id="COMMENT-RI03", at=NOW + timedelta(seconds=2), exit_code=0,
            envelope_valid=True, envelope_validation_reason="identity valid",
            downstream_effect_id="EFFECT-RI03", observed_effect_id="EFFECT-RI03",
        )
        assert matched["review"]["state"] == "VERIFIED"
        assert engine.local_llm_run_store.get(run_id).control.current_state == LocalLLMDayState.PREFLIGHT

        decision = DecisionRequest(
            decision_id="DECISION-RI03", revision=1,
            subject_type=SubjectType.EXECUTION_AUTHORITY,
            decision_subject="Resume the same fixture run", target_commit="a" * 40,
            requested_effect="RETURN_TO_PREFLIGHT",
        )
        execution.bind_human_decision(run_id, decision)
        received = execution.receive_human_decision(
            run_id,
            HumanResponse(
                exact_text="承認します", decider="広瀬剛", channel="Codex Work chat",
                message_id="MSG-RI03", source_class="RECORDED_DIRECT_CONVERSATION",
                received_at=NOW + timedelta(seconds=3), decision_id="DECISION-RI03",
                revision=1, subject_type=SubjectType.EXECUTION_AUTHORITY,
                target_commit="a" * 40, decision_effect="RETURN_TO_PREFLIGHT",
                subject_basis="The bound RI-03 decision request",
            ),
        )
        execution.build_human_confirmation(
            run_id, received["record_id"], confirmation_report_id="CONFIRM-RI03",
            confirms_report_id="REPORT-HUMAN-RI03", confirms_response_id="RESP-HUMAN-RI03",
            authority_record="AUTH-RI03",
        )
        confirmed = execution.apply_human_confirmation(
            run_id, received["record_id"],
            {
                "RESPONSE_ID": "CONFIRM-RESP-RI03", "IN_REPLY_TO": "CONFIRM-RI03",
                "CONFIRMS_REPORT_ID": "REPORT-HUMAN-RI03",
                "CONFIRMS_RESPONSE_ID": "RESP-HUMAN-RI03",
                "DECISION_ID": "DECISION-RI03", "DECISION_REVISION": 1,
                "REVIEWED_COMMIT": "a" * 40, "SUBJECT_TYPE": "EXECUTION_AUTHORITY",
                "DECISION_EFFECT": "RETURN_TO_PREFLIGHT", "RESULT": "CONTINUE",
            },
            continuation_succeeded=True, effect_evidence_id="HUMAN-EFFECT-RI03",
        )
        assert confirmed["effect_applied"] is True
        assert confirmed["run_id"] == run_id
        assert engine.local_llm_run_store.get(run_id).control.current_state == LocalLLMDayState.PREFLIGHT
        assert calls == [(run_id, 6)]
    finally:
        restore()


def test_blocked_admission_persists_reason_and_never_calls_executor(tmp_path):
    engine, calls = _engine(tmp_path, admitted=None)
    client, restore = _api(engine)
    try:
        result = client.post("/api/local-llm/day/go", json={"selected_day": 6}).json()
        assert result["execution_started"] is False
        assert result["run_record"]["control"]["current_state"] == "HUMAN_ACTION_REQUIRED"
        assert result["run_record"]["control"]["blocker"] == "EFFECTIVE_PERMISSION_UNKNOWN"
        assert calls == []
    finally:
        restore()
