"""AF-00 authority and prerequisite facts bound to one immutable RunIntent.

The records in this module are inputs to admission, never authority inferred from
UI input, environment switches, or a previously persisted boolean.
"""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Callable, Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from backend.control.day_git import GitSafetyError, git
from backend.models.local_llm_day import RunIntent, RunLimits


def _timezone(value: datetime) -> datetime:
    if value.utcoffset() is None:
        raise ValueError("Timestamp must include timezone")
    return value


def _relative_path(value: str) -> str:
    normalized = value.replace("\\", "/").strip()
    if (not normalized or normalized.startswith("/") or ":" in normalized
            or ".." in normalized.split("/")):
        raise ValueError("Path must be a safe repository-relative path")
    return normalized


class AuthorityGrant(BaseModel):
    """A recorded human grant with exact target and RunIntent bindings."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    schema_version: Literal[1] = 1
    grant_id: str = Field(min_length=1, max_length=160)
    decision_id: str = Field(min_length=1, max_length=160)
    created_at: datetime
    source_class: Literal["RECORDED_DIRECT_CONVERSATION"]
    authority_record: str
    authority_record_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    project_id: Literal["local_llm_lab"]
    selected_day: int = Field(ge=1, le=14)
    allowed_effect: str = Field(min_length=1, max_length=160)
    target_commit: str = Field(pattern=r"^[0-9a-f]{40}$")
    contract_fingerprint: str = Field(min_length=8, max_length=128)
    policy_fingerprint: str = Field(min_length=8, max_length=128)
    config_fingerprint: str = Field(min_length=8, max_length=128)
    local_llm_commit: str = Field(pattern=r"^[0-9a-f]{40}$")
    git_fingerprint: str = Field(min_length=8, max_length=128)
    requested_limits: RunLimits
    expires_at: datetime | None = None
    revoked_by: str | None = Field(default=None, min_length=1, max_length=160)

    @field_validator("created_at", "expires_at")
    @classmethod
    def require_timezone(cls, value: datetime | None) -> datetime | None:
        return None if value is None else _timezone(value)

    @field_validator("authority_record")
    @classmethod
    def safe_authority_record(cls, value: str) -> str:
        return _relative_path(value)


class PrerequisiteObservation(BaseModel):
    """A bounded server-side observation of one Day's declared prerequisites."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    schema_version: Literal[1] = 1
    observation_id: str = Field(min_length=1, max_length=160)
    project_id: Literal["local_llm_lab"]
    selected_day: int = Field(ge=1, le=14)
    observed_at: datetime
    local_llm_commit: str = Field(pattern=r"^[0-9a-f]{40}$")
    git_fingerprint: str = Field(min_length=8, max_length=128)
    required_paths: tuple[str, ...] = Field(min_length=1, max_length=30)
    ready: bool
    reason_codes: tuple[str, ...] = Field(default=(), max_length=30)

    @field_validator("observed_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        return _timezone(value)

    @field_validator("required_paths")
    @classmethod
    def safe_unique_paths(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        normalized = tuple(_relative_path(value) for value in values)
        if len(normalized) != len(set(normalized)):
            raise ValueError("Prerequisite paths must be unique")
        return normalized

    @model_validator(mode="after")
    def consistent_result(self) -> "PrerequisiteObservation":
        if self.ready and self.reason_codes:
            raise ValueError("A ready observation cannot contain failure reasons")
        if not self.ready and not self.reason_codes:
            raise ValueError("A failed observation requires a reason")
        return self


class PreflightFactRecord(BaseModel):
    """Immutable provenance for facts derived for exactly one RunIntent."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    schema_version: Literal[1] = 1
    run_id: str = Field(min_length=1, max_length=120)
    selected_day: int = Field(ge=1, le=14)
    contract_fingerprint: str = Field(min_length=8, max_length=128)
    policy_fingerprint: str = Field(min_length=8, max_length=128)
    config_fingerprint: str = Field(min_length=8, max_length=128)
    git_fingerprint: str = Field(min_length=8, max_length=128)
    observed_at: datetime
    effective_permission: bool | None
    external_prerequisite: bool | None
    authority_grant_id: str | None = Field(default=None, min_length=1, max_length=160)
    authority_decision_id: str | None = Field(default=None, min_length=1, max_length=160)
    authority_record_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    prerequisite_observation_ids: tuple[str, ...] = ()
    prerequisite_observation_hashes: dict[str, str] = Field(default_factory=dict)
    permission_reason: str = Field(min_length=1, max_length=160)
    prerequisite_reason: str = Field(min_length=1, max_length=160)

    @field_validator("observed_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        return _timezone(value)

    @model_validator(mode="after")
    def require_provenance(self) -> "PreflightFactRecord":
        if self.effective_permission is True and not all((
            self.authority_grant_id,
            self.authority_decision_id,
            self.authority_record_sha256,
        )):
            raise ValueError("True permission requires grant provenance")
        if self.external_prerequisite is True and not self.prerequisite_observation_ids:
            raise ValueError("True prerequisite requires observation provenance")
        if self.external_prerequisite is True and (
            set(self.prerequisite_observation_hashes) != set(self.prerequisite_observation_ids)
            or any(
                len(value) != 64 or any(character not in "0123456789abcdef" for character in value)
                for value in self.prerequisite_observation_hashes.values()
            )
        ):
            raise ValueError("True prerequisite requires observation source hashes")
        return self


class AuthorityGrantStore(Protocol):
    def create(self, record: AuthorityGrant) -> None: ...
    def records(self) -> tuple[AuthorityGrant, ...]: ...


class PrerequisiteObservationStore(Protocol):
    def create(self, record: PrerequisiteObservation) -> None: ...
    def records(self) -> tuple[PrerequisiteObservation, ...]: ...


class PreflightFactStore(Protocol):
    def create(self, record: PreflightFactRecord) -> None: ...
    def get(self, run_id: str) -> PreflightFactRecord | None: ...


class _CreateOnlyJsonStore:
    model: type[BaseModel]
    suffix: str
    identity_field: str

    def __init__(self, directory: Path) -> None:
        self.directory = directory

    def _path(self, identity: str) -> Path:
        return self.directory / (sha256(identity.encode("utf-8")).hexdigest() + self.suffix)

    def create(self, record: BaseModel) -> None:
        checked = self.model.model_validate_json(record.model_dump_json())
        identity = str(getattr(checked, self.identity_field))
        self.directory.mkdir(parents=True, exist_ok=True)
        with self._path(identity).open("x", encoding="utf-8") as stream:
            stream.write(checked.model_dump_json(indent=2))

    def _records(self) -> tuple[BaseModel, ...]:
        if not self.directory.exists():
            return ()
        return tuple(
            self.model.model_validate_json(path.read_text(encoding="utf-8"))
            for path in sorted(self.directory.glob(f"*{self.suffix}"))
        )


class JsonAuthorityGrantStore(_CreateOnlyJsonStore):
    model = AuthorityGrant
    suffix = ".authority.json"
    identity_field = "grant_id"

    def records(self) -> tuple[AuthorityGrant, ...]:
        return self._records()  # type: ignore[return-value]


class JsonPrerequisiteObservationStore(_CreateOnlyJsonStore):
    model = PrerequisiteObservation
    suffix = ".prerequisite.json"
    identity_field = "observation_id"

    def records(self) -> tuple[PrerequisiteObservation, ...]:
        return self._records()  # type: ignore[return-value]


class JsonPreflightFactStore(_CreateOnlyJsonStore):
    model = PreflightFactRecord
    suffix = ".preflight.json"
    identity_field = "run_id"

    def get(self, run_id: str) -> PreflightFactRecord | None:
        try:
            payload = self._path(run_id).read_text(encoding="utf-8")
        except FileNotFoundError:
            return None
        record = PreflightFactRecord.model_validate_json(payload)
        if record.run_id != run_id:
            raise ValueError("Stored preflight fact run ID does not match lookup")
        return record


class AuthorityFactResolution(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    effective_permission: bool | None
    external_prerequisite: bool | None
    record: PreflightFactRecord


class AuthorityFactResolver:
    """Derive two independent preflight facts from exact, current evidence."""

    def __init__(
        self,
        *,
        project_root: Path,
        authority_record_root: Path,
        target_commit: str,
        allowed_effect: str,
        required_paths_by_day: dict[int, tuple[str, ...]],
        grant_store: AuthorityGrantStore,
        observation_store: PrerequisiteObservationStore,
        fact_store: PreflightFactStore,
        clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    ) -> None:
        self.project_root = project_root.resolve()
        self.authority_record_root = authority_record_root.resolve()
        self.target_commit = target_commit
        self.allowed_effect = allowed_effect
        self.required_paths_by_day = required_paths_by_day
        self.grant_store = grant_store
        self.observation_store = observation_store
        self.fact_store = fact_store
        self.clock = clock

    def _head(self) -> str:
        return git(self.project_root, "rev-parse", "HEAD").decode().strip()

    def _authority_record_matches(self, grant: AuthorityGrant) -> bool:
        path = (self.authority_record_root / grant.authority_record).resolve()
        if not path.is_relative_to(self.authority_record_root) or not path.is_file():
            return False
        return sha256(path.read_bytes()).hexdigest() == grant.authority_record_sha256

    def _path_ready(self, relative: str) -> bool:
        path = (self.project_root / relative).resolve()
        return path.is_relative_to(self.project_root) and path.exists()

    def resolve(self, intent: RunIntent) -> AuthorityFactResolution:
        now = self.clock()
        head: str | None
        try:
            head = self._head()
        except GitSafetyError:
            head = None

        permission_reason = "AUTHORITY_GRANT_NOT_MATCHED"
        matching_grants: list[AuthorityGrant] = []
        try:
            grants = self.grant_store.records()
            for grant in grants:
                if grant.revoked_by is not None:
                    continue
                if grant.expires_at is not None and now > grant.expires_at:
                    continue
                if (
                    grant.project_id == "local_llm_lab"
                    and grant.selected_day == intent.selected_day
                    and grant.allowed_effect == self.allowed_effect
                    and grant.target_commit == self.target_commit
                    and grant.contract_fingerprint == intent.contract_fingerprint
                    and grant.policy_fingerprint == intent.policy_fingerprint
                    and grant.config_fingerprint == intent.config_fingerprint
                    and grant.git_fingerprint == intent.git_fingerprint
                    and grant.requested_limits == intent.requested_limits
                    and grant.local_llm_commit == head
                    and self._authority_record_matches(grant)
                ):
                    matching_grants.append(grant)
        except (OSError, ValueError):
            permission_reason = "AUTHORITY_GRANT_UNREADABLE"

        grant = matching_grants[0] if len(matching_grants) == 1 else None
        if len(matching_grants) > 1:
            permission_reason = "AUTHORITY_GRANT_AMBIGUOUS"
        elif grant is not None:
            permission_reason = "AUTHORITY_GRANT_EXACT_MATCH"

        prerequisite_reason = "PREREQUISITE_OBSERVATION_NOT_MATCHED"
        matching_observations: list[PrerequisiteObservation] = []
        expected_paths = tuple(self.required_paths_by_day.get(intent.selected_day, ()))
        try:
            observations = self.observation_store.records()
            for observation in observations:
                if (
                    expected_paths
                    and observation.project_id == "local_llm_lab"
                    and observation.selected_day == intent.selected_day
                    and observation.local_llm_commit == head
                    and observation.git_fingerprint == intent.git_fingerprint
                    and observation.ready
                    and not observation.reason_codes
                    and observation.required_paths == expected_paths
                    and all(self._path_ready(path) for path in expected_paths)
                ):
                    matching_observations.append(observation)
        except (OSError, ValueError):
            prerequisite_reason = "PREREQUISITE_OBSERVATION_UNREADABLE"

        observation = matching_observations[0] if len(matching_observations) == 1 else None
        if len(matching_observations) > 1:
            prerequisite_reason = "PREREQUISITE_OBSERVATION_AMBIGUOUS"
        elif observation is not None:
            prerequisite_reason = "PREREQUISITE_OBSERVATION_EXACT_MATCH"

        record = PreflightFactRecord(
            run_id=intent.run_id,
            selected_day=intent.selected_day,
            contract_fingerprint=intent.contract_fingerprint,
            policy_fingerprint=intent.policy_fingerprint,
            config_fingerprint=intent.config_fingerprint,
            git_fingerprint=intent.git_fingerprint,
            observed_at=now,
            effective_permission=(True if grant is not None else None),
            external_prerequisite=(True if observation is not None else None),
            authority_grant_id=(grant.grant_id if grant else None),
            authority_decision_id=(grant.decision_id if grant else None),
            authority_record_sha256=(grant.authority_record_sha256 if grant else None),
            prerequisite_observation_ids=((observation.observation_id,) if observation else ()),
            prerequisite_observation_hashes=(
                {
                    observation.observation_id: sha256(
                        observation.model_dump_json().encode("utf-8")
                    ).hexdigest()
                }
                if observation else {}
            ),
            permission_reason=permission_reason,
            prerequisite_reason=prerequisite_reason,
        )
        self.fact_store.create(record)
        return AuthorityFactResolution(
            effective_permission=record.effective_permission,
            external_prerequisite=record.external_prerequisite,
            record=record,
        )
