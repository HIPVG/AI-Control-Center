from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import shutil
import subprocess

from fastapi.testclient import TestClient
import pytest

import backend.app as control_app
from backend.control.day_git import fingerprint
from backend.control.preflight_authority import (
    AuthorityGrant,
    JsonAuthorityGrantStore,
    JsonPreflightFactStore,
    JsonPrerequisiteObservationStore,
    PrerequisiteObservation,
)
from backend.control.projects import ConfiguredProject, ProjectRegistry
from backend.control.run_store import JsonRunStore
from backend.control.run_telemetry_store import JsonRunTelemetryStore
from backend.models.local_llm_day import LocalLLMDaySnapshot, LocalLLMDayState, RunLimits
from backend.models.runtime import RuntimeConfig
from backend.orchestrator.engine import ControlCenterEngine, JsonStateStore


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "day-contract"
NOW = datetime(2026, 9, 30, 3, 0, tzinfo=timezone.utc)
TARGET_COMMIT = "d" * 40
REQUIRED_PATHS = (
    "docs/runbooks/work-plan-day1-14.md",
    "docs/architecture/decision-reasoning-architecture.md",
)


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def _repository(tmp_path: Path) -> tuple[Path, str]:
    root = tmp_path / "local-llm"
    shutil.copytree(FIXTURE_ROOT, root)
    _git(tmp_path, "init", "-b", "main", str(root))
    _git(root, "config", "user.name", "Fixture")
    _git(root, "config", "user.email", "fixture@example.invalid")
    _git(root, "add", ".")
    _git(root, "commit", "-m", "fixture baseline")
    return root, _git(root, "rev-parse", "HEAD")


def _engine(tmp_path: Path):
    root, head = _repository(tmp_path)
    authority_root = tmp_path / "control-center"
    authority_file = authority_root / "docs/authority.md"
    authority_file.parent.mkdir(parents=True)
    authority_file.write_text("Bounded Day 6 product validation authority.\n", encoding="utf-8")
    grant_store = JsonAuthorityGrantStore(tmp_path / "authority")
    observation_store = JsonPrerequisiteObservationStore(tmp_path / "observations")
    fact_store = JsonPreflightFactStore(tmp_path / "preflight-facts")
    run_store = JsonRunStore(tmp_path / "runs")
    telemetry_store = JsonRunTelemetryStore(tmp_path / "telemetry")
    state_store = JsonStateStore(tmp_path / "control-center.json")
    calls: list[tuple[str, int]] = []
    holder: dict[str, ControlCenterEngine] = {}

    def execute(run_id: str, day: int) -> dict[str, object]:
        engine = holder["engine"]
        contract = engine.local_llm_day_program._load_contracts()[day]
        engine.local_llm_day_program.snapshot = LocalLLMDaySnapshot(
            run_id=run_id,
            selected_day=day,
            state=LocalLLMDayState.PREFLIGHT,
            objective=contract.objective,
            contract=contract,
            contract_fingerprint=engine.local_llm_day_program._contract_fingerprint(contract),
            activity="AF-01 injected executor reached PREFLIGHT only.",
        )
        engine.local_llm_day_program._save()
        calls.append((run_id, day))
        return {"run_id": run_id, "result": "INJECTED_PREFLIGHT_ONLY"}

    registry = ProjectRegistry(projects={
        "local_llm_lab": ConfiguredProject(
            name="LocalLLM-Lab", path=root, default_branch="main"
        )
    })
    engine = ControlCenterEngine(
        state_store=state_store,
        runtime_config=RuntimeConfig(),
        project_registry=registry,
        local_llm_run_store=run_store,
        local_llm_telemetry_store=telemetry_store,
        local_llm_run_executor=execute,
        local_llm_authority_grant_store=grant_store,
        local_llm_prerequisite_observation_store=observation_store,
        local_llm_preflight_fact_store=fact_store,
        local_llm_authority_target_commit=TARGET_COMMIT,
        local_llm_authority_record_root=authority_root,
        local_llm_required_paths_by_day={6: REQUIRED_PATHS},
    )
    holder["engine"] = engine
    return {
        "engine": engine,
        "root": root,
        "head": head,
        "authority_root": authority_root,
        "authority_file": authority_file,
        "grant_store": grant_store,
        "observation_store": observation_store,
        "fact_store": fact_store,
        "run_store": run_store,
        "telemetry_store": telemetry_store,
        "state_store": state_store,
        "registry": registry,
        "calls": calls,
    }


def _seed_grant(context: dict[str, object], *, target_commit: str = TARGET_COMMIT) -> None:
    engine = context["engine"]
    program = engine.local_llm_day_program
    contract = program._load_contracts()[6]
    authority_file = context["authority_file"]
    context["grant_store"].create(AuthorityGrant(
        grant_id="grant-af01",
        decision_id="decision-af01",
        created_at=NOW,
        source_class="RECORDED_DIRECT_CONVERSATION",
        authority_record="docs/authority.md",
        authority_record_sha256=sha256(authority_file.read_bytes()).hexdigest(),
        project_id="local_llm_lab",
        selected_day=6,
        allowed_effect="RUN_DAY_PRODUCT_VALIDATION",
        target_commit=target_commit,
        contract_fingerprint=program._contract_fingerprint(contract),
        policy_fingerprint=program._file_fingerprint(
            Path(__file__).resolve().parents[1] / "docs/WORKING_RULES.md"
        ),
        config_fingerprint=program._file_fingerprint(program.PROGRAM_PATH),
        local_llm_commit=context["head"],
        git_fingerprint=fingerprint(context["root"]),
        requested_limits=RunLimits(
            active_work_seconds=1800,
            max_attempts=2,
            max_tokens=None,
            max_cost=0,
            currency="JPY",
        ),
    ))


def _seed_observation(context: dict[str, object]) -> None:
    context["observation_store"].create(PrerequisiteObservation(
        observation_id="observation-af01",
        project_id="local_llm_lab",
        selected_day=6,
        observed_at=NOW,
        local_llm_commit=context["head"],
        git_fingerprint=fingerprint(context["root"]),
        required_paths=REQUIRED_PATHS,
        ready=True,
        reason_codes=(),
    ))


def _client(engine: ControlCenterEngine):
    previous = control_app.engine
    control_app.engine = engine
    client = TestClient(control_app.app)

    def restore() -> None:
        client.close()
        control_app.engine = previous

    return client, restore


def test_browser_go_uses_one_intent_for_facts_admission_effect_and_readback(tmp_path: Path) -> None:
    context = _engine(tmp_path)
    _seed_grant(context)
    _seed_observation(context)
    client, restore = _client(context["engine"])
    try:
        response = client.post("/api/local-llm/day/go", json={"selected_day": 6}).json()
        run_id = response["run_id"]
        readback = client.get("/api/local-llm/runs").json()

        assert response["admission"]["status"] == "ADMISSIBLE"
        assert response["execution_started"] is True
        assert response["preflight_fact"]["run_id"] == run_id
        assert response["run_record"]["intent"]["run_id"] == run_id
        assert context["calls"] == [(run_id, 6)]
        assert readback["current"]["run_id"] == run_id
        assert readback["preflight_fact"]["run_id"] == run_id
        assert readback["preflight_fact"]["authority_grant_id"] == "grant-af01"
        assert readback["preflight_fact"]["prerequisite_observation_ids"] == [
            "observation-af01"
        ]
        assert readback["current"]["state"] == "PREFLIGHT"
        assert readback["unmet_criteria"]

        restarted_calls: list[tuple[str, int]] = []
        restarted = ControlCenterEngine(
            state_store=context["state_store"],
            runtime_config=RuntimeConfig(),
            project_registry=context["registry"],
            local_llm_run_store=context["run_store"],
            local_llm_telemetry_store=context["telemetry_store"],
            local_llm_run_executor=lambda new_run_id, day: (
                restarted_calls.append((new_run_id, day)) or {"run_id": new_run_id}
            ),
            local_llm_authority_grant_store=context["grant_store"],
            local_llm_prerequisite_observation_store=context["observation_store"],
            local_llm_preflight_fact_store=context["fact_store"],
            local_llm_authority_target_commit=TARGET_COMMIT,
            local_llm_authority_record_root=context["authority_root"],
            local_llm_required_paths_by_day={6: REQUIRED_PATHS},
        )
        duplicate = restarted.prepare_local_llm_day_go(6)
        legacy = restarted.legacy_start_local_llm_day(6)
        assert duplicate["error_code"] == legacy["error_code"] == "RUN_ALREADY_ACTIVE"
        assert duplicate["run_id"] == legacy["run_id"] == run_id
        assert restarted_calls == []
        assert context["fact_store"].get(run_id).run_id == run_id
    finally:
        restore()


@pytest.mark.parametrize("authority_case", ["missing", "stale"])
def test_missing_or_stale_authority_fails_closed_before_effect(
    tmp_path: Path, authority_case: str
) -> None:
    context = _engine(tmp_path)
    if authority_case == "stale":
        _seed_grant(context, target_commit="e" * 40)
    _seed_observation(context)
    client, restore = _client(context["engine"])
    try:
        response = client.post("/api/local-llm/day/go", json={"selected_day": 6}).json()
        assert response["execution_started"] is False
        assert response["admission"]["reason_code"] == "EFFECTIVE_PERMISSION_UNKNOWN"
        assert response["preflight_fact"]["effective_permission"] is None
        assert response["preflight_fact"]["authority_grant_id"] is None
        assert context["calls"] == []
    finally:
        restore()


def test_missing_prerequisite_fails_closed_without_erasing_permission(tmp_path: Path) -> None:
    context = _engine(tmp_path)
    _seed_grant(context)
    client, restore = _client(context["engine"])
    try:
        response = client.post("/api/local-llm/day/go", json={"selected_day": 6}).json()
        assert response["execution_started"] is False
        assert response["admission"]["reason_code"] == "EXTERNAL_PREREQUISITE_UNCONFIRMED"
        assert response["preflight_fact"]["effective_permission"] is True
        assert response["preflight_fact"]["external_prerequisite"] is None
        assert context["calls"] == []
    finally:
        restore()
