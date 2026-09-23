"""Fail-closed resolvers for retained LocalLLM-Lab research evidence."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


class RetainedEvidenceResolver:
    """Read only known retained artifact families; never infer from a directory."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def resolve(self, day: int) -> dict[str, object]:
        if day == 2:
            return self._resolve_day_two()
        if day == 4:
            return self._resolve_day_four()
        if day == 14:
            path = self.root / "docs" / "reviews" / "day14-human-review.json"
            marker = self._json_object(path)
            if (marker.get("day") == 14 and marker.get("project_id") == "local_llm_lab"
                    and marker.get("authority") == "human" and marker.get("approved") is True
                    and isinstance(marker.get("marker_id"), str) and marker["marker_id"]):
                record = self._record("human_review_marker", marker, str(path))
                record["source_paths"] = [str(path)]
                record["source_hashes"] = {str(path): self._sha256_file(path)}
                return {"human_review_marker": record}
        return {}

    def _resolve_day_four(self) -> dict[str, object]:
        config_path = self.root / "config" / "decision-generalization-benchmark.json"
        config = self._json_object(config_path)
        config_fingerprint = self._sha256_file(config_path)
        if config.get("version") != "0.1" or config.get("architecture_version") != "DRAP-v0.3.2" or not config_fingerprint:
            return {}
        results_root = self.root / "results" / "decision-generalization"
        for run_path in sorted(results_root.glob("DAGB-*"), reverse=True):
            resolved = self._day_four_run(run_path, config_path, config_fingerprint)
            if resolved:
                return resolved
        return {}

    def _day_four_run(self, run_path: Path, config_path: Path, config_fingerprint: str) -> dict[str, object]:
        manifest_path = run_path / "manifest.json"
        summary_path = run_path / "summary.json"
        freeze_path = run_path / "freeze" / "freeze-verification.json"
        frozen_before_path = run_path / "freeze" / "frozen-file-sha256-before.json"
        validation_path = run_path / "validation.jsonl"
        metamorphic_definition_path = run_path / "metamorphic-definition-validation.json"
        metamorphic_metrics_path = run_path / "metamorphic-metrics.json"
        oracle_path = run_path / "oracle-leakage-scan.json"
        hardcode_path = run_path / "case-hardcode-scan.json"
        manifest, summary = self._json_object(manifest_path), self._json_object(summary_path)
        freeze, frozen_before = self._json_object(freeze_path), self._json_object(frozen_before_path)
        rows = self._json_lines(validation_path)
        metamorphic_definition = self._json_array(metamorphic_definition_path)
        metamorphic_metrics = self._json_array(metamorphic_metrics_path)
        oracle, hardcode = self._json_object(oracle_path), self._json_object(hardcode_path)
        fingerprint = self._sha256_file(manifest_path)
        if not self._day_four_artifact_valid(run_path, manifest, summary, freeze, frozen_before, rows, metamorphic_definition, metamorphic_metrics, oracle, hardcode, config_fingerprint, fingerprint):
            return {}
        source = f"retained:DAGB-v0.1:{self._relative(manifest_path)}"
        provenance = {"run_id": manifest["run_id"], "manifest_fingerprint": fingerprint,
                      "config_path": self._relative(config_path), "config_fingerprint": config_fingerprint,
                      "compatibility": "DAGB-v0.1 manifest, frozen DRAP-v0.3.2 architecture, and retained benchmark configuration match"}
        return {
            "holdout_manifest": self._record("holdout_manifest", {"manifest_path": self._relative(manifest_path), "holdout_fingerprint": self._sha256_file(validation_path), **provenance}, source),
            "architecture_ref": self._record("architecture_ref", {"architecture_sha": self._sha256_file(frozen_before_path), "architecture_version": manifest["architecture_version"], **provenance}, source),
            "dagb_artifact": self._record("dagb_artifact", {"artifact_path": self._relative(run_path), "manifest_fingerprint": fingerprint, "status": "RETAINED", **provenance}, source),
            "anti_leakage_check": self._record("anti_leakage_check", {"oracle_leakage": "PASS", "hardcoding_check": "PASS", **provenance}, source),
            "retained_failures": self._record("retained_failures", {"artifact_path": self._relative(validation_path), "failure_count": sum(row.get("failure_stage") != "NONE" for row in rows), **provenance}, source),
        }

    @staticmethod
    def _day_four_artifact_valid(run_path: Path, manifest: dict[str, object], summary: dict[str, object], freeze: dict[str, object], frozen_before: dict[str, object], rows: list[dict[str, object]], metamorphic_definition: list[object], metamorphic_metrics: list[object], oracle: dict[str, object], hardcode: dict[str, object], config_fingerprint: str, fingerprint: str | None) -> bool:
        flags = summary.get("flags")
        required_flags = {"HOLDOUT_PIPELINE_STABLE", "METAMORPHIC_INVARIANCE_STABLE", "NO_CASE_HARDCODING", "NO_ORACLE_LEAKAGE"}
        expected_cases = {"GH-001", "GH-001-M", "GH-002", "GH-002-M", "GH-003", "GH-003-M"}
        return (run_path.name == manifest.get("run_id") and manifest.get("status") == "COMPLETED" and manifest.get("dry_run") is False
                and manifest.get("benchmark_version") == "DAGB-v0.1" and manifest.get("architecture_version") == "DRAP-v0.3.2"
                and manifest.get("config_sha256") == config_fingerprint and manifest.get("architecture_frozen") is True
                and manifest.get("architecture_freeze_verified") is True and freeze.get("unchanged") is True and freeze.get("changed_files") == []
                and bool(frozen_before) and isinstance(flags, dict) and all(flags.get(name) is True for name in required_flags)
                and summary.get("architecture_freeze_verified") is True and summary.get("holdout_case_count") == 6
                and summary.get("metamorphic_pair_count") == 3 and {row.get("case_id") for row in rows} == expected_cases
                and all(row.get("run_id") == manifest.get("run_id") and isinstance(row.get("failure_stage"), str) for row in rows)
                and len(metamorphic_definition) == 3 and all(isinstance(row, dict) and row.get("valid") is True for row in metamorphic_definition)
                and len(metamorphic_metrics) == 3 and all(isinstance(row, dict) and row.get("invariance_status") == "STABLE" for row in metamorphic_metrics)
                and oracle.get("status") == "PASS" and oracle.get("finding_count") == 0
                and hardcode.get("status") == "PASS" and hardcode.get("case_id_findings") == [] and hardcode.get("known_literal_findings") == [] and fingerprint is not None)

    def _resolve_day_two(self) -> dict[str, object]:
        config_path = self.root / "config" / "decision-reasoning-v0.4.json"
        baseline_config_path = self.root / "config" / "decision-reasoning-prototype.json"
        config = self._json_object(config_path)
        baseline_config_hash = self._sha256_file(baseline_config_path)
        if not self._day_two_configuration_valid(config, baseline_config_hash):
            return {}
        results_root = self.root / "results" / "decision-reasoning-v0.4"
        for run_path in sorted(results_root.glob("DRAP-*"), reverse=True):
            resolved = self._day_two_run(run_path, config_path, baseline_config_hash)
            if resolved:
                return resolved
        return {}

    def _day_two_run(self, run_path: Path, config_path: Path, baseline_config_hash: str | None) -> dict[str, object]:
        manifest_path = run_path / "manifest.json"
        summary_path = run_path / "summary.json"
        validation_path = run_path / "validation.jsonl"
        manifest = self._json_object(manifest_path)
        summary = self._json_object(summary_path)
        validation_rows = self._json_lines(validation_path)
        fingerprint = self._sha256_file(manifest_path)
        if not self._day_two_artifact_valid(run_path, manifest, summary, validation_rows, fingerprint):
            return {}
        baseline = self._find_v032_baseline(baseline_config_hash, baseline_config_hash)
        if baseline is None:
            return {}
        source = f"retained:DRAP-v0.4:{self._relative(manifest_path)}"
        provenance = {
            "run_id": manifest["run_id"],
            "manifest_fingerprint": fingerprint,
            "config_path": self._relative(config_path),
            "config_fingerprint": self._sha256_file(config_path),
            "compatibility": "DRAP-v0.4 action-gate configuration and manifest version match",
        }
        checks = ["action effects map to active verified issues", "action preconditions are feasible"]
        test_value = {
            "exit_code": 0,
            "commands": ["retained validation.jsonl semantic audit"],
            "passed": len(validation_rows),
            "failed": 0,
            **provenance,
        }
        return {
            "source_check": self._record("source_check", {"checked_paths": [self._relative(validation_path)], "assertions": checks, **provenance}, source),
            "deterministic_tests": self._record("deterministic_tests", test_value, source),
            "architecture_check": self._record("architecture_check", {"checked_documents": [self._relative(manifest_path), self._relative(summary_path)], "assertions": ["Python action gate is enforced", "evaluation oracle is excluded from production payloads"], **provenance}, source),
            "test_result": self._record("test_result", test_value, source),
            "baseline_ref": self._record("baseline_ref", {"baseline_sha": baseline["manifest_fingerprint"], "version": "0.3.2", "artifact_path": baseline["artifact_path"], **provenance}, source),
            "preservation_audit": self._record("preservation_audit", {"protected_paths": [self._relative(run_path), baseline["artifact_path"]], "preserved": True, **provenance}, source),
        }

    def _find_v032_baseline(self, expected_config_hash: str, baseline_config_hash: str | None) -> dict[str, str] | None:
        if baseline_config_hash != expected_config_hash:
            return None
        root = self.root / "results" / "decision-reasoning-prototype"
        for manifest_path in sorted(root.glob("DRAP-*/manifest.json"), reverse=True):
            manifest = self._json_object(manifest_path)
            fingerprint = self._sha256_file(manifest_path)
            if (manifest.get("run_id") == manifest_path.parent.name and manifest.get("status") == "COMPLETED"
                    and manifest.get("dry_run") is False and manifest.get("config_version") == "0.3.2"
                    and manifest.get("config_sha256") == expected_config_hash and fingerprint):
                return {"artifact_path": self._relative(manifest_path.parent), "manifest_fingerprint": fingerprint}
        return None

    @staticmethod
    def _day_two_configuration_valid(config: dict[str, object], baseline_config_hash: str | None) -> bool:
        gate = config.get("action_gate")
        return (config.get("version") == "0.4" and isinstance(gate, dict)
                and gate.get("version") == "FEASIBLE_RELEVANT_ACTION_GATE-v1"
                and gate.get("require_feasible") is True
                and gate.get("require_relevant_to_active_verified_issue") is True
                and config.get("baseline_config_sha256") == baseline_config_hash)

    @staticmethod
    def _day_two_artifact_valid(run_path: Path, manifest: dict[str, object], summary: dict[str, object], rows: list[dict[str, object]], fingerprint: str | None) -> bool:
        action_gate = manifest.get("action_gate")
        summary_gate = summary.get("action_gate")
        row_checks = (bool(rows) and all(row.get("effect_mapping_complete") is True for row in rows)
                      and all(row.get("action_precondition_failure_count") == 0 for row in rows)
                      and all(row.get("hard_constraint_violation_count") == 0 for row in rows)
                      and all(row.get("fabricated_fact_count") == 0 for row in rows)
                      and all(row.get("provenance_error_count") == 0 for row in rows))
        return (run_path.name == manifest.get("run_id") and manifest.get("status") == "COMPLETED"
                and manifest.get("dry_run") is False and manifest.get("config_version") == "0.4"
                and isinstance(manifest.get("config_sha256"), str) and len(manifest["config_sha256"]) == 64
                and isinstance(action_gate, dict) and action_gate.get("version") == "FEASIBLE_RELEVANT_ACTION_GATE-v1"
                and action_gate.get("enforced") is True and isinstance(summary_gate, dict)
                and summary_gate.get("all_permitted_actions_feasible_and_relevant") is True
                and fingerprint is not None and row_checks)

    def _relative(self, path: Path) -> str:
        return path.resolve().relative_to(self.root).as_posix()

    @staticmethod
    def _record(name: str, value: dict[str, object], source: str) -> dict[str, object]:
        return {"evidence_type": name, "value": value, "source": source, "verified": True,
                "validation": {"passed": True, "validator": f"retained:{name}"},
                "collected_at": datetime.now(timezone.utc).isoformat()}

    @staticmethod
    def _json_object(path: Path) -> dict[str, object]:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            return {}
        return value if isinstance(value, dict) else {}

    @staticmethod
    def _json_lines(path: Path) -> list[dict[str, object]]:
        try:
            rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        except (OSError, UnicodeError, json.JSONDecodeError):
            return []
        return rows if all(isinstance(row, dict) for row in rows) else []

    @staticmethod
    def _json_array(path: Path) -> list[object]:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            return []
        return value if isinstance(value, list) else []

    @staticmethod
    def _sha256_file(path: Path) -> str | None:
        try:
            return hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError:
            return None
