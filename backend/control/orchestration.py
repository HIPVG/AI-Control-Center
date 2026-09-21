from pathlib import Path

from backend.models.orchestration import OrchestrationConfig


def load_orchestration_config(path: Path) -> OrchestrationConfig:
    if not path.exists():
        return OrchestrationConfig()
    import yaml

    return OrchestrationConfig.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")) or {})
