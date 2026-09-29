"""Production composition root for one durable local-LLM run.

The component owns no new workflow state.  It wires the accepted coordinator,
execution controllers, telemetry store, and read projection to the same stores
and rejects cross-run data before it can become observable product state.
"""

from __future__ import annotations

from backend.control.local_llm_day_program import LocalLLMDayProgram
from backend.control.run_execution_composition import RunExecutionComposition
from backend.control.run_projection_composition import build_run_read_model
from backend.control.run_store import RunStore
from backend.control.run_telemetry_store import RunTelemetryStore
from backend.models.local_llm_day import RunTelemetry


class RunProductComposition:
    """Bind execution, telemetry, and readback to one production run store."""

    def __init__(
        self,
        program: LocalLLMDayProgram,
        run_store: RunStore,
        telemetry_store: RunTelemetryStore,
    ) -> None:
        self.program = program
        self.run_store = run_store
        self.telemetry_store = telemetry_store
        self.execution = RunExecutionComposition(program, run_store)

    def record_telemetry(self, run_id: str, telemetry: RunTelemetry) -> dict[str, object]:
        current = self.run_store.current()
        if current is None or current.intent.run_id != run_id:
            return {"outcome": "REJECTED", "reason_code": "RUN_NOT_CURRENT", "run_id": run_id}
        if telemetry.run_id != run_id:
            return {
                "outcome": "REJECTED",
                "reason_code": "TELEMETRY_RUN_ID_MISMATCH",
                "run_id": run_id,
            }
        self.telemetry_store.create(telemetry)
        return {"outcome": "ACCEPTED", "run_id": run_id}

    def read(self) -> dict[str, object]:
        return build_run_read_model(
            run_store=self.run_store,
            telemetry_store=self.telemetry_store,
            program=self.program,
        ).read()
