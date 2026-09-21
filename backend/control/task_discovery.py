import json
from datetime import datetime
from pathlib import Path
from typing import Callable, Literal
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator

from backend.control.tasks import TaskCommand
from backend.models.runtime import CommandRunResult


class DiscoveryDefinition(BaseModel):
    discovery_id: str = Field(min_length=1, max_length=120)
    project_id: str = Field(min_length=1)
    working_directory: str = "."
    candidate_case_ids: list[str] = Field(min_length=1)
    precheck: TaskCommand
    code_fix_error_codes: list[str] = Field(default_factory=list)

    @field_validator("candidate_case_ids")
    @classmethod
    def case_ids_must_be_unique(cls, value: list[str]) -> list[str]:
        if any(not item.strip() for item in value) or len(value) != len(set(value)):
            raise ValueError("candidate case IDs must be non-empty and unique")
        return value


class DiscoveryRegistry(BaseModel):
    discoveries: dict[str, DiscoveryDefinition] = Field(default_factory=dict)

    def get(self, discovery_id: str) -> DiscoveryDefinition | None:
        return self.discoveries.get(discovery_id)


class DiscoveryCaseResult(BaseModel):
    case_id: str
    status: Literal["PASS", "FAIL", "INFRASTRUCTURE_ERROR"]
    classification: Literal["CODE_FIX", "DATA_ISSUE", "ENVIRONMENT", "CONFIGURATION", "UNKNOWN", "none"]
    command: CommandRunResult


class FailingTaskDiscoveryResult(BaseModel):
    run_id: str = Field(default_factory=lambda: uuid4().hex)
    discovery_id: str
    project_id: str
    started_at: datetime
    completed_at: datetime | None = None
    cases: list[DiscoveryCaseResult] = Field(default_factory=list)
    selected_case_id: str | None = None
    final_result: Literal["CODE_FIX_SELECTED", "HUMAN_REVIEW_REQUIRED", "FAILED"]
    human_review_reason: str | None = None
    error_code: str | None = None


def load_discovery_registry(path: Path) -> DiscoveryRegistry:
    if not path.exists():
        return DiscoveryRegistry()
    import yaml

    return DiscoveryRegistry.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")) or {})


class DeterministicTaskDiscovery:
    """Runs only configured prechecks and stops at the first eligible code failure."""

    def discover(
        self,
        definition: DiscoveryDefinition,
        *,
        run_id: str,
        started_at: datetime,
        run_command: Callable[[TaskCommand, Path, Path], CommandRunResult],
        working_directory: Path,
        artifact_root: Path,
    ) -> FailingTaskDiscoveryResult:
        result = FailingTaskDiscoveryResult(
            run_id=run_id,
            discovery_id=definition.discovery_id,
            project_id=definition.project_id,
            started_at=started_at,
            final_result="HUMAN_REVIEW_REQUIRED",
        )
        for case_id in definition.candidate_case_ids:
            command = TaskCommand(argv=[str(artifact_root / case_id) if value == "{artifact_root}" else case_id if value == "{case_id}" else value for value in definition.precheck.argv])
            execution = run_command(command, working_directory, artifact_root / case_id)
            status, classification = self._classify(execution, definition.code_fix_error_codes)
            result.cases.append(DiscoveryCaseResult(case_id=case_id, status=status, classification=classification, command=execution))
            if classification == "CODE_FIX":
                result.selected_case_id = case_id
                result.final_result = "CODE_FIX_SELECTED"
                result.completed_at = datetime.now(started_at.tzinfo)
                return result
        result.completed_at = datetime.now(started_at.tzinfo)
        result.human_review_reason = "no configured candidate produced an eligible CODE_FIX failure"
        return result

    @staticmethod
    def _classify(execution: CommandRunResult, code_fix_error_codes: list[str]) -> tuple[str, str]:
        reported_error = DeterministicTaskDiscovery._reported_error_code(execution)
        if reported_error:
            execution.error_code = reported_error
        if execution.passed:
            return "PASS", "none"
        if execution.error_code in {"COMMAND_NOT_FOUND", "COMMAND_TIMEOUT"}:
            return "INFRASTRUCTURE_ERROR", "ENVIRONMENT"
        if execution.error_code in {"OUTPUT_ERROR", "LOCAL_IO"}:
            return "INFRASTRUCTURE_ERROR", "ENVIRONMENT"
        if execution.error_code in {"INVALID_CASE", "CONFIGURATION"}:
            return "FAIL", "CONFIGURATION"
        if execution.error_code in code_fix_error_codes:
            return "FAIL", "CODE_FIX"
        return "FAIL", "UNKNOWN"

    @staticmethod
    def _reported_error_code(execution: CommandRunResult) -> str | None:
        if execution.error_code:
            return execution.error_code
        if not execution.stdout:
            return None
        try:
            payload = json.loads(execution.stdout.splitlines()[-1])
            value = payload.get("error", {}).get("code") if isinstance(payload, dict) else None
        except (json.JSONDecodeError, IndexError, AttributeError):
            return None
        return value.upper() if isinstance(value, str) else None
