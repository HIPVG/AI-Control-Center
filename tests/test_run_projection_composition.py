from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

import backend.app as control_app
from backend.control.local_llm_day_program import LocalLLMDayProgram
from backend.control.run_projection_composition import build_run_read_model
from backend.control.run_read_model import ReviewProjection
from backend.control.run_store import JsonRunStore
from backend.control.run_telemetry_store import JsonRunTelemetryStore
from backend.models.local_llm_day import (
    DayCriterion,
    LocalLLMDayContract,
    LocalLLMDayState,
    RunControl,
    RunIntent,
    RunLimits,
    RunRecord,
    RunTelemetry,
    TelemetryMetric,
)


NOW = datetime(2026, 9, 29, 12, tzinfo=timezone.utc)


def contract() -> LocalLLMDayContract:
    return LocalLLMDayContract(
        day=6,
        title="Fixture Day 6",
        objective="Exercise exact-run projection.",
        completion_criteria=[
            DayCriterion(
                criterion_id="d6-c1",
                statement="Evidence is verified.",
                required_evidence=["typed fixture"],
                evidence_record_ids={"typed fixture": "evidence-001"},
            )
        ],
        constraints=["No actual Day execution."],
        authoritative_sources=["fixture"],
    )


def program(root, *, run_id: str | None, selected_day: int = 6) -> LocalLLMDayProgram:
    day_contract = contract()
    instance = LocalLLMDayProgram(
        root,
        saved={
            "run_id": run_id,
            "selected_day": selected_day,
            "state": "PREFLIGHT",
            "objective": day_contract.objective,
            "contract": day_contract.model_dump(mode="json"),
            "contract_fingerprint": LocalLLMDayProgram._contract_fingerprint(day_contract),
            "updated_at": NOW.isoformat(),
        },
    )
    return instance


def record(
    run_id: str,
    *,
    go_at: datetime,
    fingerprint: str,
    state: LocalLLMDayState = LocalLLMDayState.PREFLIGHT,
) -> RunRecord:
    return RunRecord(
        intent=RunIntent(
            run_id=run_id,
            selected_day=6,
            go_at=go_at,
            contract_fingerprint=fingerprint,
            policy_fingerprint="policy-v1",
            config_fingerprint="config-v1",
            git_fingerprint="git-base-v1",
            requested_limits=RunLimits(
                active_work_seconds=1800,
                max_attempts=2,
                max_cost=0,
                currency="JPY",
            ),
        ),
        control=RunControl(
            run_id=run_id,
            selected_day=6,
            contract_fingerprint=fingerprint,
            current_state=state,
            state_history=(LocalLLMDayState.IDLE,),
            next_action="Validate the same persisted run.",
            updated_at=go_at,
        ),
    )


def metric(value, unit: str, source: str | None = None, reason: str | None = None):
    return TelemetryMetric(
        value=value,
        unit=unit,
        source=source,
        observed_at=NOW,
        unknown_reason=reason,
    )


def telemetry(run_id: str) -> RunTelemetry:
    return RunTelemetry(
        run_id=run_id,
        manual_relay_count=metric(0, "count", "review registry"),
        attempt_count=metric(1, "attempts", "repair history"),
        attempt_limit=metric(2, "attempts", "RunIntent"),
        input_tokens=metric(None, "tokens", reason="not observed"),
        output_tokens=metric(None, "tokens", reason="not observed"),
        cost=metric(0.0, "JPY", "fixture authority"),
        captured_at=NOW,
    )


def test_read_time_composition_joins_only_current_run_and_preserves_unknowns(tmp_path):
    controller = program(tmp_path, run_id="run-current")
    fingerprint = controller._contract_fingerprint(controller.snapshot.contract)
    runs = JsonRunStore(tmp_path / "runs")
    runs.create(record("run-old", go_at=NOW - timedelta(minutes=1), fingerprint=fingerprint))
    runs.create(record("run-current", go_at=NOW, fingerprint=fingerprint))
    telemetry_store = JsonRunTelemetryStore(tmp_path / "telemetry")
    telemetry_store.create(telemetry("run-current"))

    body = build_run_read_model(
        run_store=runs,
        telemetry_store=telemetry_store,
        program=controller,
        at=NOW,
    ).read()

    assert body["current"]["run_id"] == "run-current"
    assert [item["run_id"] for item in body["history"]] == ["run-old"]
    assert body["admission"]["run_id"] == "run-current"
    assert body["unmet_criteria"][0]["evidence_record_ids"] == ["evidence-001"]
    assert body["telemetry"]["run_id"] == "run-current"
    assert body["telemetry"]["input_tokens"]["value"] is None
    assert body["telemetry"]["input_tokens"]["unknown_reason"] == "not observed"
    assert body["projection_errors"] == []


def test_restart_readback_retains_one_current_run_and_history(tmp_path):
    controller = program(tmp_path, run_id="run-current")
    fingerprint = controller._contract_fingerprint(controller.snapshot.contract)
    JsonRunStore(tmp_path / "runs").create(
        record("run-old", go_at=NOW - timedelta(minutes=1), fingerprint=fingerprint)
    )
    JsonRunStore(tmp_path / "runs").create(
        record("run-current", go_at=NOW, fingerprint=fingerprint)
    )
    JsonRunTelemetryStore(tmp_path / "telemetry").create(telemetry("run-current"))

    # New store/controller instances model a process restart and must rebuild,
    # rather than retain a startup-time singleton.
    restarted = program(tmp_path, run_id="run-current")
    body = build_run_read_model(
        run_store=JsonRunStore(tmp_path / "runs"),
        telemetry_store=JsonRunTelemetryStore(tmp_path / "telemetry"),
        program=restarted,
        at=NOW + timedelta(seconds=1),
    ).read()

    assert body["selected"] is True
    assert body["current"]["run_id"] == "run-current"
    assert [item["run_id"] for item in body["history"]] == ["run-old"]


def test_mismatched_snapshot_and_telemetry_fail_closed_without_completion(tmp_path):
    controller = program(tmp_path, run_id="run-other")
    fingerprint = controller._contract_fingerprint(controller.snapshot.contract)
    runs = JsonRunStore(tmp_path / "runs")
    runs.create(record("run-current", go_at=NOW, fingerprint=fingerprint))
    telemetry_store = JsonRunTelemetryStore(tmp_path / "telemetry")
    telemetry_store.directory.mkdir(parents=True)
    telemetry_store._path("run-current").write_text(
        telemetry("run-other").model_dump_json(indent=2), encoding="utf-8"
    )

    body = build_run_read_model(
        run_store=runs,
        telemetry_store=telemetry_store,
        program=controller,
        at=NOW,
    ).read()

    assert body["current"]["run_id"] == "run-current"
    assert body["current"]["state"] == "PREFLIGHT"
    assert body["unmet_criteria"] == []
    assert body["telemetry"] is None
    assert body["projection_errors"] == [
        "DAY_SNAPSHOT_RUN_ID_MISMATCH",
        "TELEMETRY_UNREADABLE_OR_MISMATCHED",
    ]


def test_corrupt_run_or_version_history_never_becomes_current(tmp_path):
    controller = program(tmp_path, run_id="run-current")
    fingerprint = controller._contract_fingerprint(controller.snapshot.contract)
    runs = JsonRunStore(tmp_path / "runs")
    current = record("run-current", go_at=NOW, fingerprint=fingerprint)
    runs.create(current)
    history = runs._history_directory("run-current")
    history.mkdir(parents=True)
    (history / "corrupt.json").write_text("{", encoding="utf-8")

    body = build_run_read_model(
        run_store=runs,
        telemetry_store=JsonRunTelemetryStore(tmp_path / "telemetry"),
        program=controller,
        at=NOW,
    ).read()

    assert body["selected"] is False
    assert body["current"] is None
    assert body["projection_errors"] == ["RUN_VERSION_HISTORY_UNREADABLE"]


def test_optional_projection_for_another_run_is_rejected_not_applied(tmp_path):
    controller = program(tmp_path, run_id="run-current")
    fingerprint = controller._contract_fingerprint(controller.snapshot.contract)
    runs = JsonRunStore(tmp_path / "runs")
    runs.create(record("run-current", go_at=NOW, fingerprint=fingerprint))

    body = build_run_read_model(
        run_store=runs,
        telemetry_store=JsonRunTelemetryStore(tmp_path / "telemetry"),
        program=controller,
        review=ReviewProjection(
            run_id="run-other",
            report_id="report-001",
            state="APPLIED",
            observed_at=NOW,
            source="fixture",
        ),
        at=NOW,
    ).read()

    assert body["current"]["run_id"] == "run-current"
    assert body["review"] is None
    assert body["projection_errors"] == ["OPTIONAL_PROJECTION_RUN_ID_MISMATCH"]


def test_api_requests_engine_projection_each_time(monkeypatch, tmp_path):
    controller = program(tmp_path, run_id="run-current")
    fingerprint = controller._contract_fingerprint(controller.snapshot.contract)
    runs = JsonRunStore(tmp_path / "runs")
    telemetry_store = JsonRunTelemetryStore(tmp_path / "telemetry")
    monkeypatch.setattr(control_app.engine, "local_llm_day_program", controller)
    monkeypatch.setattr(control_app.engine, "local_llm_run_store", runs)
    monkeypatch.setattr(control_app.engine, "local_llm_telemetry_store", telemetry_store)
    client = TestClient(control_app.app)
    first = client.get("/api/local-llm/runs").json()

    # The run appears after application construction. A startup singleton would
    # remain empty, while the RI-02 composition root observes it on the next GET.
    runs.create(record("run-current", go_at=NOW, fingerprint=fingerprint))
    telemetry_store.create(telemetry("run-current"))
    second = client.get("/api/local-llm/runs").json()

    assert first["selected"] is False
    assert second["selected"] is True
    assert second["current"]["run_id"] == "run-current"
    assert second["telemetry"]["run_id"] == "run-current"
