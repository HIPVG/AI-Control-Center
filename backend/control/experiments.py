from pathlib import Path

from backend.models.experiment import TrustedExperiment


def load_experiments(path: Path) -> dict[str, TrustedExperiment]:
    if not path.exists():
        return {}
    import yaml
    values = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return {key: TrustedExperiment(experiment_id=key, **value) for key, value in values.get("experiments", {}).items()}
