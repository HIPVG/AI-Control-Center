"""Durable run-record persistence behind a small create/update interface.

Exclusive creation protects immutable run identity.  Updates retain the prior
version before replacing the current projection, so state evolution cannot erase
the history that authorized it.
"""

from hashlib import sha256
from pathlib import Path
from datetime import datetime
import os
from typing import Protocol

from backend.models.local_llm_day import RunRecord


class RunStore(Protocol):
    def create(self, record: RunRecord) -> None: ...
    def get(self, run_id: str) -> RunRecord | None: ...
    def update(self, record: RunRecord, *, expected_updated_at: datetime) -> None: ...
    def records(self) -> tuple[RunRecord, ...]: ...
    def current(self) -> RunRecord | None: ...
    def versions(self, run_id: str) -> tuple[RunRecord, ...]: ...


class JsonRunStore:
    def __init__(self, directory: Path) -> None:
        self.directory = directory

    def _path(self, run_id: str) -> Path:
        # User-supplied identity is data, never a filesystem path.
        return self.directory / (sha256(run_id.encode("utf-8")).hexdigest() + ".json")

    def _history_directory(self, run_id: str) -> Path:
        return self.directory / "history" / sha256(run_id.encode("utf-8")).hexdigest()

    def create(self, record: RunRecord) -> None:
        # Revalidate even instances created with Pydantic's unchecked copy API.
        checked = RunRecord.model_validate_json(record.model_dump_json())
        self.directory.mkdir(parents=True, exist_ok=True)
        with self._path(checked.intent.run_id).open("x", encoding="utf-8") as stream:
            stream.write(checked.model_dump_json(indent=2))
        # Write failures propagate; partial files are retained and fail closed.

    def get(self, run_id: str) -> RunRecord | None:
        try:
            payload = self._path(run_id).read_text(encoding="utf-8")
        except FileNotFoundError:
            return None
        record = RunRecord.model_validate_json(payload)
        if record.intent.run_id != run_id:
            raise ValueError("Stored run ID does not match lookup")
        return record

    def update(self, record: RunRecord, *, expected_updated_at: datetime) -> None:
        checked = RunRecord.model_validate_json(record.model_dump_json())
        current = self.get(checked.intent.run_id)
        if current is None:
            raise FileNotFoundError(checked.intent.run_id)
        if current.intent != checked.intent:
            raise ValueError("Run intent is immutable")
        if current.control.updated_at != expected_updated_at:
            raise ValueError("Stale run update")
        if checked.control.updated_at <= current.control.updated_at:
            raise ValueError("Run update time must advance")
        expected_history = current.control.state_history + (current.control.current_state,)
        if checked.control.state_history != expected_history:
            raise ValueError("Run state history must append the previous state")

        history_directory = self._history_directory(checked.intent.run_id)
        history_directory.mkdir(parents=True, exist_ok=True)
        history_path = history_directory / (
            current.control.updated_at.astimezone().isoformat().replace(":", "-") + ".json"
        )
        with history_path.open("x", encoding="utf-8") as stream:
            stream.write(current.model_dump_json(indent=2))

        path = self._path(checked.intent.run_id)
        temporary = path.with_suffix(".json.tmp")
        try:
            with temporary.open("x", encoding="utf-8") as stream:
                stream.write(checked.model_dump_json(indent=2))
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)

    def records(self) -> tuple[RunRecord, ...]:
        if not self.directory.exists():
            return ()
        records = tuple(
            RunRecord.model_validate_json(path.read_text(encoding="utf-8"))
            for path in self.directory.glob("*.json")
        )
        return tuple(sorted(records, key=lambda item: (item.intent.go_at, item.intent.run_id)))

    def current(self) -> RunRecord | None:
        records = self.records()
        return records[-1] if records else None

    def versions(self, run_id: str) -> tuple[RunRecord, ...]:
        history_directory = self._history_directory(run_id)
        versions = [] if not history_directory.exists() else [
            RunRecord.model_validate_json(path.read_text(encoding="utf-8"))
            for path in history_directory.glob("*.json")
        ]
        current = self.get(run_id)
        if current is not None:
            versions.append(current)
        return tuple(sorted(versions, key=lambda item: item.control.updated_at))
