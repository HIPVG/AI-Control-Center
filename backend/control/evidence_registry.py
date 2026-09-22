"""Fail-closed evidence-type registry for the LocalLLM Day contract."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


Record = dict[str, object]
Validator = Callable[[object], bool]


@dataclass(frozen=True)
class EvidenceDefinition:
    name: str
    validator: Validator


def _mapping_with(*keys: str) -> Validator:
    def validate(value: object) -> bool:
        return isinstance(value, dict) and all(value.get(key) not in (None, "", [], {}) for key in keys)
    return validate


def _list_with(*keys: str) -> Validator:
    def validate(value: object) -> bool:
        return isinstance(value, dict) and all(isinstance(value.get(key), list) and bool(value[key]) for key in keys)
    return validate


class EvidenceRegistry:
    """All configured names have their own explicit semantic strategy."""

    def __init__(self) -> None:
        self._definitions = {
            "git_head": EvidenceDefinition("git_head", _mapping_with("branch", "head", "is_commit")),
            "origin_ref": EvidenceDefinition("origin_ref", _mapping_with("origin_url", "upstream_ref", "upstream_sha")),
            "status_audit": EvidenceDefinition("status_audit", self._status_audit),
            "staging_audit": EvidenceDefinition("staging_audit", _mapping_with("generated_artifacts_not_staged")),
            "documentation_check": EvidenceDefinition("documentation_check", _list_with("checked_files", "checks")),
            "test_result": EvidenceDefinition("test_result", self._test_result),
            "commit_ref": EvidenceDefinition("commit_ref", _mapping_with("branch", "head", "is_commit")),
            "source_check": EvidenceDefinition("source_check", _list_with("checked_paths", "assertions")),
            "deterministic_tests": EvidenceDefinition("deterministic_tests", self._test_result),
            "architecture_check": EvidenceDefinition("architecture_check", _list_with("checked_documents", "assertions")),
            "baseline_ref": EvidenceDefinition("baseline_ref", _mapping_with("baseline_sha", "version")),
            "preservation_audit": EvidenceDefinition("preservation_audit", _mapping_with("protected_paths", "preserved")),
            "v032_artifact": EvidenceDefinition("v032_artifact", self._artifact),
            "v04_artifact": EvidenceDefinition("v04_artifact", self._artifact),
            "condition_record": EvidenceDefinition("condition_record", _mapping_with("condition_fingerprint", "model", "configuration_version")),
            "comparison_metrics": EvidenceDefinition("comparison_metrics", _mapping_with("valid_plan_count", "invalid_plan_count", "prompt_tokens", "output_tokens")),
            "failure_policy": EvidenceDefinition("failure_policy", _mapping_with("policy", "retained_failure_count")),
            "holdout_manifest": EvidenceDefinition("holdout_manifest", _mapping_with("manifest_path", "holdout_fingerprint")),
            "architecture_ref": EvidenceDefinition("architecture_ref", _mapping_with("architecture_sha", "architecture_version")),
            "dagb_artifact": EvidenceDefinition("dagb_artifact", self._artifact),
            "anti_leakage_check": EvidenceDefinition("anti_leakage_check", _mapping_with("oracle_leakage", "hardcoding_check")),
            "retained_failures": EvidenceDefinition("retained_failures", _mapping_with("artifact_path", "failure_count")),
            "validator_result": EvidenceDefinition("validator_result", _mapping_with("validator_version", "result")),
            "local_artifact": EvidenceDefinition("local_artifact", self._artifact),
            "teacher_evidence": EvidenceDefinition("teacher_evidence", self._artifact),
            "limitation_record": EvidenceDefinition("limitation_record", _mapping_with("limitations", "scope")),
            "decision_record": EvidenceDefinition("decision_record", _mapping_with("decision", "evidence_refs")),
            "schema_contract": EvidenceDefinition("schema_contract", _mapping_with("schema_path", "schema_version")),
            "provenance_test": EvidenceDefinition("provenance_test", self._test_result),
            "validation_report": EvidenceDefinition("validation_report", _mapping_with("report_path", "result")),
            "novelty_artifact": EvidenceDefinition("novelty_artifact", self._artifact),
            "provenance_artifact": EvidenceDefinition("provenance_artifact", self._artifact),
            "nonmutation_test": EvidenceDefinition("nonmutation_test", self._test_result),
            "performance_artifact": EvidenceDefinition("performance_artifact", _mapping_with("artifact_path", "prompt_tokens", "output_tokens", "elapsed_seconds", "vram_mb", "cpu_percent", "ram_mb")),
            "deployment_matrix": EvidenceDefinition("deployment_matrix", _mapping_with("matrix_path", "tiers")),
            "hardware_evidence": EvidenceDefinition("hardware_evidence", _mapping_with("evidence_refs", "conclusion")),
            "advisory_record": EvidenceDefinition("advisory_record", _mapping_with("advisory", "limitations")),
            "operator_docs": EvidenceDefinition("operator_docs", _list_with("document_paths", "covered_topics")),
            "recovery_check": EvidenceDefinition("recovery_check", self._test_result),
            "gitignore_check": EvidenceDefinition("gitignore_check", _mapping_with("gitignore_path", "protected_patterns")),
            "full_test_result": EvidenceDefinition("full_test_result", self._test_result),
            "result_artifact": EvidenceDefinition("result_artifact", self._artifact),
            "classification_record": EvidenceDefinition("classification_record", _mapping_with("classification", "artifact_path")),
            "status_summary": EvidenceDefinition("status_summary", _mapping_with("summary_path", "evidence_refs")),
            "sprint_review": EvidenceDefinition("sprint_review", _mapping_with("review_path", "conclusions")),
            "human_review_marker": EvidenceDefinition("human_review_marker", _mapping_with("marker_id", "authority")),
        }

    @property
    def names(self) -> set[str]:
        return set(self._definitions)

    def validate(self, name: str, record: object) -> bool:
        definition = self._definitions.get(name)
        if definition is None or not isinstance(record, dict):
            return False
        if record.get("evidence_type") != name or record.get("verified") is not True:
            return False
        source = record.get("source")
        validation = record.get("validation")
        if not isinstance(source, str) or not source.strip() or not isinstance(validation, dict) or validation.get("passed") is not True:
            return False
        return definition.validator(record.get("value"))

    @staticmethod
    def _artifact(value: object) -> bool:
        return isinstance(value, dict) and all(isinstance(value.get(key), str) and value[key] for key in ("artifact_path", "manifest_fingerprint", "status")) and value.get("status") in {"COMPLETE", "PASS", "RETAINED"}

    @staticmethod
    def _status_audit(value: object) -> bool:
        return isinstance(value, dict) and all(isinstance(value.get(key), list) for key in ("staged_tracked_paths", "unstaged_tracked_paths", "untracked_paths", "relevant_dirty_paths", "generated_paths"))

    @staticmethod
    def _test_result(value: object) -> bool:
        return isinstance(value, dict) and value.get("exit_code") == 0 and isinstance(value.get("commands"), list) and bool(value["commands"]) and isinstance(value.get("passed"), int) and value["passed"] > 0 and isinstance(value.get("failed"), int) and value["failed"] == 0


REGISTRY = EvidenceRegistry()
