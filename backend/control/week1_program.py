"""Deterministic authority checks for the remaining approved Week 1 program."""

import json
from pathlib import Path

from backend.models.week1 import Week1DayRecord, Week1DayStatus


class Week1Program:
    DAYS = (4, 5, 6, 7)

    def __init__(self, local_llm_root: Path) -> None:
        self.root = local_llm_root

    def run(self, day: int, records: list[dict]) -> Week1DayRecord:
        if day == 4:
            matrix = self._json("config/model-matrix.json")
            candidates = [m for m in matrix.get("models", []) if m.get("family") != "qwen3" and m.get("runtime_model_name")]
            if not candidates:
                return Week1DayRecord(day=4, status=Week1DayStatus.EXTERNAL_ACTION_REQUIRED, reason_code="APPROVED_CROSS_FAMILY_RUNTIME_MISSING", evidence={"required_capability": "approved Gemma or Llama runtime"})
            phi = next((m for m in candidates if m.get("runtime_model_name") == "phi4:14b"), None)
            if phi is None:
                return Week1DayRecord(day=4, status=Week1DayStatus.EXTERNAL_ACTION_REQUIRED, reason_code="APPROVED_PHI4_RUNTIME_MISSING")
            return Week1DayRecord(day=4, status=Week1DayStatus.COMPLETE, reason_code="DAY4_CROSS_FAMILY_EXPERIMENT_CONFIGURED", evidence={"experiment_id": "week1_day4_cross_family", "approved_models": ["qwen3-14b-q4", "phi4-14b-q4"]})
        if day == 5:
            plan = self._json("config/benchmark-plan.yaml")
            if not plan.get("execution_enabled", False):
                return Week1DayRecord(day=5, status=Week1DayStatus.EXTERNAL_ACTION_REQUIRED, reason_code="APPROVED_BENCHMARK_NOT_ENABLED", evidence={"required_capability": "configured approved benchmark"})
            return Week1DayRecord(day=5, status=Week1DayStatus.EXTERNAL_ACTION_REQUIRED, reason_code="BENCHMARK_RUNNER_NOT_CONFIGURED")
        if day == 6:
            profiles = self._json("config/run-profiles.json")
            context = next((item for item in profiles.get("profiles", []) if item.get("id") == "context"), {})
            if context.get("execution_enabled") is not False:
                return Week1DayRecord(day=6, status=Week1DayStatus.EXTERNAL_ACTION_REQUIRED, reason_code="CONTEXT_AUTHORITY_REQUIRES_APPROVED_CONFIGURATION")
            return Week1DayRecord(day=6, status=Week1DayStatus.COMPLETE, reason_code="CONTEXT_PREPARATION_RECORDED", evidence={"execution_enabled": False, "context_profile": "preparation_only"})
        completed = [item for item in records if item.get("status") == Week1DayStatus.COMPLETE.value]
        if len(completed) < 3:
            return Week1DayRecord(day=7, status=Week1DayStatus.EXTERNAL_ACTION_REQUIRED, reason_code="WEEK1_EVIDENCE_INCOMPLETE", evidence={"completed_days": [int(item["day"]) for item in completed]})
        return Week1DayRecord(day=7, status=Week1DayStatus.HUMAN_DECISION_REQUIRED, reason_code="NEXT_PHASE_DIRECTION_REQUIRED", evidence={"completed_days": [int(item["day"]) for item in completed], "recommendation_options": ["RAG_GOLD_CORPUS", "GENERATOR_V1_2", "MORE_MODEL_COMPARISON", "LONG_CONTEXT", "STRUCTURED_TASKS", "PERFORMANCE_SCALING"]})

    def _json(self, relative: str) -> dict:
        path = self.root / relative
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}
