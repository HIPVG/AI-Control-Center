from pathlib import Path

from backend.models.day import DayPlanRegistry


def load_plan_registry(path: Path) -> DayPlanRegistry:
    if not path.exists():
        return DayPlanRegistry()
    import yaml

    return DayPlanRegistry.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")) or {})
