from __future__ import annotations

from datetime import datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path
import subprocess

import pytest

from backend.control.preflight_authority import (
    AuthorityFactResolver,
    AuthorityGrant,
    JsonAuthorityGrantStore,
    JsonPreflightFactStore,
    JsonPrerequisiteObservationStore,
    PrerequisiteObservation,
)
from backend.models.local_llm_day import RunIntent, RunLimits


NOW = datetime(2026, 9, 30, 9, 0, tzinfo=timezone.utc)
TARGET_COMMIT = "a" * 40
REQUIRED = (
    "docs/runbooks/work-plan-day1-14.md",
    "docs/architecture/decision-reasoning-architecture.md",
    "schemas/decision-reasoning",
)


def command(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def project(tmp_path: Path) -> tuple[Path, str]:
    root = tmp_path / "local-llm"
    for relative in REQUIRED:
        path = root / relative
        if path.suffix:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(relative, encoding="utf-8")
        else:
            path.mkdir(parents=True, exist_ok=True)
            (path / "schema.json").write_text("{}", encoding="utf-8")
    command(root, "init")
    command(root, "config", "user.email", "fixture@example.invalid")
    command(root, "config", "user.name", "Fixture")
    command(root, "add", ".")
    command(root, "commit", "-m", "fixture")
    return root, command(root, "rev-parse", "HEAD")


def intent(**changes: object) -> RunIntent:
    values: dict[str, object] = {
        "run_id": "run-af00",
        "selected_day": 6,
        "go_at": NOW,
        "contract_fingerprint": "contract-0001",
        "policy_fingerprint": "policy-000001",
        "config_fingerprint": "config-000001",
        "git_fingerprint": "git-fingerprint-0001",
        "requested_limits": RunLimits(
            active_work_seconds=1800,
            max_attempts=2,
            max_tokens=None,
            max_cost=0,
            currency="JPY",
        ),
    }
    values.update(changes)
    return RunIntent(**values)


def authority_record(root: Path) -> tuple[str, str]:
    relative = "docs/review-records/authority.md"
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("Human authority: Day 6, bounded validation.\n", encoding="utf-8")
    return relative, sha256(path.read_bytes()).hexdigest()


def grant(record_root: Path, head: str, run: RunIntent, **changes: object) -> AuthorityGrant:
    relative, digest = authority_record(record_root)
    values: dict[str, object] = {
        "grant_id": "grant-af00",
        "decision_id": "decision-af00",
        "created_at": NOW,
        "source_class": "RECORDED_DIRECT_CONVERSATION",
        "authority_record": relative,
        "authority_record_sha256": digest,
        "project_id": "local_llm_lab",
        "selected_day": run.selected_day,
        "allowed_effect": "RUN_DAY_PRODUCT_VALIDATION",
        "target_commit": TARGET_COMMIT,
        "contract_fingerprint": run.contract_fingerprint,
        "policy_fingerprint": run.policy_fingerprint,
        "config_fingerprint": run.config_fingerprint,
        "local_llm_commit": head,
        "git_fingerprint": run.git_fingerprint,
        "requested_limits": run.requested_limits,
        "expires_at": NOW + timedelta(days=1),
    }
    values.update(changes)
    return AuthorityGrant(**values)


def observation(head: str, run: RunIntent, **changes: object) -> PrerequisiteObservation:
    values: dict[str, object] = {
        "observation_id": "observation-af00",
        "project_id": "local_llm_lab",
        "selected_day": run.selected_day,
        "observed_at": NOW,
        "local_llm_commit": head,
        "git_fingerprint": run.git_fingerprint,
        "required_paths": REQUIRED,
        "ready": True,
        "reason_codes": (),
    }
    values.update(changes)
    return PrerequisiteObservation(**values)


def resolver(
    tmp_path: Path,
    project_root: Path,
    record_root: Path,
) -> AuthorityFactResolver:
    return AuthorityFactResolver(
        project_root=project_root,
        authority_record_root=record_root,
        target_commit=TARGET_COMMIT,
        allowed_effect="RUN_DAY_PRODUCT_VALIDATION",
        required_paths_by_day={6: REQUIRED},
        grant_store=JsonAuthorityGrantStore(tmp_path / "authority"),
        observation_store=JsonPrerequisiteObservationStore(tmp_path / "observations"),
        fact_store=JsonPreflightFactStore(tmp_path / "facts"),
        clock=lambda: NOW,
    )


def seed_exact(
    tmp_path: Path,
    project_root: Path,
    record_root: Path,
    head: str,
    run: RunIntent,
) -> AuthorityFactResolver:
    result = resolver(tmp_path, project_root, record_root)
    result.grant_store.create(grant(record_root, head, run))
    result.observation_store.create(observation(head, run))
    return result


def test_exact_grant_and_day6_observation_resolve_with_restart_readback(tmp_path: Path) -> None:
    project_root, head = project(tmp_path)
    record_root = tmp_path / "control-center"
    run = intent()
    service = seed_exact(tmp_path, project_root, record_root, head, run)

    resolved = service.resolve(run)

    assert resolved.effective_permission is True
    assert resolved.external_prerequisite is True
    assert resolved.record.authority_grant_id == "grant-af00"
    assert resolved.record.authority_decision_id == "decision-af00"
    assert resolved.record.prerequisite_observation_ids == ("observation-af00",)
    assert resolved.record.prerequisite_observation_hashes == {
        "observation-af00": sha256(
            observation(head, run).model_dump_json().encode("utf-8")
        ).hexdigest()
    }
    restarted_store = JsonPreflightFactStore(tmp_path / "facts")
    assert restarted_store.get(run.run_id) == resolved.record


@pytest.mark.parametrize(
    ("grant_change", "run_change", "resolver_change"),
    [
        ({"selected_day": 5}, {}, {}),
        ({"contract_fingerprint": "other-contract"}, {}, {}),
        ({"policy_fingerprint": "other-policy"}, {}, {}),
        ({"config_fingerprint": "other-config"}, {}, {}),
        ({"local_llm_commit": "b" * 40}, {}, {}),
        ({"git_fingerprint": "other-git"}, {}, {}),
        ({"target_commit": "b" * 40}, {}, {}),
        ({"allowed_effect": "OTHER_EFFECT"}, {}, {}),
        (
            {"requested_limits": RunLimits(active_work_seconds=1200, max_attempts=2,
                                            max_tokens=None, max_cost=0, currency="JPY")},
            {},
            {},
        ),
    ],
)
def test_any_authority_binding_mismatch_fails_closed(
    tmp_path: Path,
    grant_change: dict[str, object],
    run_change: dict[str, object],
    resolver_change: dict[str, object],
) -> None:
    project_root, head = project(tmp_path)
    record_root = tmp_path / "control-center"
    run = intent(**run_change)
    service = resolver(tmp_path, project_root, record_root)
    service.grant_store.create(grant(record_root, head, run, **grant_change))
    service.observation_store.create(observation(head, run))

    resolved = service.resolve(run)

    assert resolved.effective_permission is None
    assert resolved.record.authority_grant_id is None


@pytest.mark.parametrize("case", ["missing", "duplicate", "revoked", "corrupt"])
def test_missing_duplicate_revoked_and_corrupt_grants_fail_closed(
    tmp_path: Path, case: str
) -> None:
    project_root, head = project(tmp_path)
    record_root = tmp_path / "control-center"
    run = intent()
    service = resolver(tmp_path, project_root, record_root)
    service.observation_store.create(observation(head, run))
    if case == "duplicate":
        service.grant_store.create(grant(record_root, head, run))
        service.grant_store.create(grant(record_root, head, run, grant_id="grant-af00-2"))
    elif case == "revoked":
        service.grant_store.create(grant(record_root, head, run, revoked_by="decision-revoke"))
    elif case == "corrupt":
        corrupt = tmp_path / "authority" / "corrupt.authority.json"
        corrupt.parent.mkdir(parents=True, exist_ok=True)
        corrupt.write_text("{not-json", encoding="utf-8")

    resolved = service.resolve(run)

    assert resolved.effective_permission is None
    assert resolved.external_prerequisite is True
    expected = {
        "missing": "AUTHORITY_GRANT_NOT_MATCHED",
        "duplicate": "AUTHORITY_GRANT_AMBIGUOUS",
        "revoked": "AUTHORITY_GRANT_NOT_MATCHED",
        "corrupt": "AUTHORITY_GRANT_UNREADABLE",
    }
    assert resolved.record.permission_reason == expected[case]


def test_permission_does_not_substitute_for_missing_prerequisite(tmp_path: Path) -> None:
    project_root, head = project(tmp_path)
    record_root = tmp_path / "control-center"
    run = intent()
    service = resolver(tmp_path, project_root, record_root)
    service.grant_store.create(grant(record_root, head, run))

    resolved = service.resolve(run)

    assert resolved.effective_permission is True
    assert resolved.external_prerequisite is None
    assert resolved.record.prerequisite_observation_ids == ()


def test_grant_at_exact_expiration_time_fails_closed_without_provenance(tmp_path: Path) -> None:
    project_root, head = project(tmp_path)
    record_root = tmp_path / "control-center"
    run = intent()
    service = resolver(tmp_path, project_root, record_root)
    service.grant_store.create(grant(record_root, head, run, expires_at=NOW))
    service.observation_store.create(observation(head, run))

    resolved = service.resolve(run)

    assert resolved.effective_permission is None
    assert resolved.record.permission_reason == "AUTHORITY_GRANT_NOT_MATCHED"
    assert resolved.record.authority_grant_id is None
    assert resolved.record.authority_decision_id is None
    assert resolved.record.authority_record_sha256 is None
    assert resolved.external_prerequisite is True


def test_observation_for_another_day_cannot_promote_prerequisite(tmp_path: Path) -> None:
    project_root, head = project(tmp_path)
    record_root = tmp_path / "control-center"
    run = intent()
    service = resolver(tmp_path, project_root, record_root)
    service.grant_store.create(grant(record_root, head, run))
    service.observation_store.create(observation(head, run, selected_day=5))

    resolved = service.resolve(run)

    assert resolved.effective_permission is True
    assert resolved.external_prerequisite is None


def test_fact_record_is_create_only_for_one_run_identity(tmp_path: Path) -> None:
    project_root, head = project(tmp_path)
    record_root = tmp_path / "control-center"
    run = intent()
    service = seed_exact(tmp_path, project_root, record_root, head, run)
    service.resolve(run)

    with pytest.raises(FileExistsError):
        service.resolve(run)


def test_versioned_human_authority_companion_is_strict_and_traceable() -> None:
    repository = Path(__file__).resolve().parents[1]
    companion = repository / "config/preflight-authorities/auth-g7-clean-baseline-validation-20260930-001.authority.json"
    parsed = AuthorityGrant.model_validate_json(companion.read_text(encoding="utf-8"))
    authority_path = repository / parsed.authority_record

    assert parsed.source_class == "RECORDED_DIRECT_CONVERSATION"
    assert parsed.selected_day == 6
    assert parsed.requested_limits.max_cost == 0
    assert sha256(authority_path.read_bytes()).hexdigest() == parsed.authority_record_sha256
