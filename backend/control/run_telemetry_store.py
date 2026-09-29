"""WC-08 create-only JSON persistence for immutable run telemetry."""

from hashlib import sha256
from pathlib import Path
from typing import Protocol

from backend.models.local_llm_day import RunTelemetry


class RunTelemetryStore(Protocol):
    def create(self, telemetry: RunTelemetry) -> None: ...
    def get(self, run_id: str) -> RunTelemetry | None: ...


class JsonRunTelemetryStore:
    def __init__(self, directory: Path) -> None:
        self.directory = directory

    def _path(self, run_id: str) -> Path:
        return self.directory / (sha256(run_id.encode("utf-8")).hexdigest() + ".telemetry.json")

    def create(self, telemetry: RunTelemetry) -> None:
        checked = RunTelemetry.model_validate_json(telemetry.model_dump_json())
        self.directory.mkdir(parents=True, exist_ok=True)
        with self._path(checked.run_id).open("x", encoding="utf-8") as stream:
            stream.write(checked.model_dump_json(indent=2))

    def get(self, run_id: str) -> RunTelemetry | None:
        try:
            payload = self._path(run_id).read_text(encoding="utf-8")
        except FileNotFoundError:
            return None
        telemetry = RunTelemetry.model_validate_json(payload)
        if telemetry.run_id != run_id:
            raise ValueError("Stored telemetry run ID does not match lookup")
        return telemetry
