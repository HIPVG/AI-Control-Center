from pathlib import Path

from pydantic import BaseModel, Field, field_validator

from backend.control.tasks import TaskCommand, _safe_relative_paths


class FaultProfile(BaseModel):
    """Trusted, worktree-only mutation used to validate one repair workflow."""

    fault_id: str = Field(min_length=1, max_length=120)
    project_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1, max_length=120)
    base_case: str = Field(min_length=1)
    title: str = Field(min_length=1, max_length=300)
    working_directory: str = "."
    target_file: str
    fault_type: str = Field(min_length=1, max_length=300)
    fault_description: str = Field(min_length=1, max_length=1000)
    expected_original: str = Field(min_length=1)
    injected_text: str = Field(min_length=1)
    baseline: TaskCommand
    postcheck: TaskCommand
    allowed_files: list[str] = Field(min_length=1)
    context_files: list[str] = Field(min_length=1)
    max_retry: int = Field(default=1, ge=0, le=20)
    context_max_characters: int = Field(default=30000, ge=1, le=100000)
    expected_precheck_exit_code: int = 1
    expected_precheck_text: str = Field(min_length=1, max_length=200)

    @field_validator("working_directory", "target_file")
    @classmethod
    def safe_path(cls, value: str) -> str:
        return _safe_relative_paths([value])[0]

    @field_validator("allowed_files", "context_files")
    @classmethod
    def safe_paths(cls, value: list[str]) -> list[str]:
        return _safe_relative_paths(value)

    @field_validator("injected_text")
    @classmethod
    def injection_must_differ(cls, value: str, info) -> str:
        if value == info.data.get("expected_original"):
            raise ValueError("injected text must differ from expected original")
        return value

    def validate_scope(self) -> None:
        if self.allowed_files != [self.target_file]:
            raise ValueError("controlled fault repair must allow exactly its target file")
        if self.context_files != [self.target_file]:
            raise ValueError("controlled fault repair must include only its target file")


class FaultRegistry(BaseModel):
    faults: dict[str, FaultProfile] = Field(default_factory=dict)

    def get(self, fault_id: str) -> FaultProfile | None:
        return self.faults.get(fault_id)


def load_fault_registry(path: Path) -> FaultRegistry:
    if not path.exists():
        return FaultRegistry()
    import yaml

    registry = FaultRegistry.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")) or {})
    for profile in registry.faults.values():
        profile.validate_scope()
    return registry
