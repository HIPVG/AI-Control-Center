"""WC-01 persistence boundary; deliberately not wired to Go or live state.

Exclusive file creation rejects duplicate run IDs across store instances. The
single execution manager owns later control updates; no update API is exposed
until that integration card supplies state-transition guards.
"""

from hashlib import sha256
from pathlib import Path
from typing import Protocol

from backend.models.local_llm_day import RunRecord


class RunStore(Protocol):
    def create(self, record: RunRecord) -> None: ...
    def get(self, run_id: str) -> RunRecord | None: ...


class JsonRunStore:
    def __init__(self, directory: Path) -> None:
        self.directory = directory

    def _path(self, run_id: str) -> Path:
        # User-supplied identity is data, never a filesystem path.
        return self.directory / (sha256(run_id.encode("utf-8")).hexdigest() + ".json")

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
