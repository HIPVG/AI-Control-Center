from pathlib import Path

from pydantic import BaseModel, Field, field_validator


class ConfiguredProject(BaseModel):
    """An external project deliberately admitted to Control Center workflows."""

    name: str = Field(min_length=1)
    path: Path
    default_branch: str = Field(min_length=1)

    @field_validator("path")
    @classmethod
    def path_must_be_absolute(cls, value: Path) -> Path:
        if not value.is_absolute():
            raise ValueError("configured project paths must be absolute")
        return value


class ProjectRegistry(BaseModel):
    projects: dict[str, ConfiguredProject] = Field(default_factory=dict)

    def get(self, project_id: str) -> ConfiguredProject | None:
        return self.projects.get(project_id)


def load_project_registry(path: Path) -> ProjectRegistry:
    """Load only administrator-configured external project targets."""
    if not path.exists():
        return ProjectRegistry()
    import yaml

    return ProjectRegistry.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")) or {})
