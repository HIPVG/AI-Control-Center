import os
from pathlib import Path

from backend.models.orchestration import OrchestrationConfig, ProviderSettings


def load_orchestration_config(path: Path) -> OrchestrationConfig:
    if not path.exists():
        config = OrchestrationConfig()
    else:
        import yaml
        config = OrchestrationConfig.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")) or {})
    for role in ("architect", "evaluator"):
        configured = getattr(config.orchestration, role)
        provider = os.environ.get(f"AI_CONTROL_CENTER_{role.upper()}_PROVIDER", configured.provider)
        model = os.environ.get(f"AI_CONTROL_CENTER_{role.upper()}_MODEL", configured.model)
        setattr(config.orchestration, role, ProviderSettings(
            provider=provider, model=model, timeout_seconds=configured.timeout_seconds,
            max_transient_retries=configured.max_transient_retries,
        ))
    return config
