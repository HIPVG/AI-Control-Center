"""Research-only execution boundary; no engineering or repair privileges."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from uuid import uuid4
from pydantic import BaseModel, ConfigDict, Field

from backend.control.day_git import approved, files, GitSafetyError
from backend.control.evidence_registry import REGISTRY


@dataclass(frozen=True)
class ResearchCondition:
    action_id: str
    script: str
    configuration: str
    model: str
    input_paths: tuple[str, ...]
    evidence_types: tuple[str, ...]
    condition_identity: str = ""
    frozen_hashes: tuple[tuple[str, str], ...] = ()
    output_path: str = "output"
    execution_plan: dict | None = None


class ResearchExecutionPlan(BaseModel):
    """An Architect proposal, never execution authority."""
    model_config = ConfigDict(extra="forbid", frozen=True)
    action_id: str
    day: int = Field(ge=1, le=14)
    script_path: str
    config_paths: list[str] = Field(min_length=1, max_length=4)
    input_paths: list[str] = Field(default_factory=list, max_length=30)
    output_paths: list[str] = Field(min_length=1, max_length=1)
    arguments: list[str] = Field(default_factory=list, max_length=30)
    condition_fingerprint: str
    expected_evidence_types: list[str]
    rationale: str = Field(min_length=1, max_length=1200)
    reference_sources: list[str] = Field(min_length=1, max_length=20)


def plan_fingerprint(root: Path, paths: list[str]) -> str:
    if any(not isinstance(p, str) or Path(p).is_absolute() or ".." in Path(p).parts
           or not (root / p).resolve().is_relative_to(root.resolve()) for p in paths):
        raise ValueError("RESEARCH_PATH_OUTSIDE_TRUSTED_SCOPE")
    return hashlib.sha256(json.dumps({p: digest(root / p) for p in sorted(set(paths))}, sort_keys=True).encode()).hexdigest()


def validate_research_plan(root, contract, template, proposal):
    """Deterministic authority, condition, path and evidence guard.

    Research kind is a condition property, not a Day->filename map. Script
    and input identity may be discovered by the Architect at runtime.
    """
    plan = ResearchExecutionPlan.model_validate(proposal)
    if plan.day != contract.day:
        raise ValueError("RESEARCH_DAY_AUTHORITY_MISMATCH")
    if plan.action_id != template.template_id or set(plan.expected_evidence_types) != set(template.post_action_evidence_types):
        raise ValueError("RESEARCH_EVIDENCE_AUTHORITY_MISMATCH")
    kinds = {"D3_FIXED_REGRESSION": "fixed_regression", "D4_FREEZE_HOLDOUT": "fresh_holdout",
             "D4_DAGB_RUN": "fresh_holdout", "D5_PLAN_SELECTION_PRECISION": "plan_selection",
             "D8_NOVELTY_SCOUT": "novelty_scout", "D10_PERFORMANCE_RUN": "performance",
             "D13_NEW_HOLDOUT": "fresh_holdout"}
    read_paths = [plan.script_path, *plan.config_paths, *plan.input_paths, *plan.reference_sources]
    for relative in read_paths:
        path = root / relative
        if (Path(relative).is_absolute() or ".." in Path(relative).parts or ":" in relative
                or not path.resolve().is_relative_to(root.resolve()) or not path.is_file()
                or not relative.startswith(("scripts/", "config/", "schemas/", "docs/", "datasets/", "results/"))):
            raise ValueError("RESEARCH_PATH_OUTSIDE_TRUSTED_SCOPE")
    if not plan.script_path.startswith("scripts/") or not plan.script_path.endswith(".py"):
        raise ValueError("RESEARCH_SCRIPT_SCOPE")
    if any(not p.startswith("config/") or not p.endswith(".json") for p in plan.config_paths):
        raise ValueError("RESEARCH_CONFIG_SCOPE")
    if not set(contract.authoritative_sources).issubset(plan.reference_sources):
        raise ValueError("RESEARCH_AUTHORITY_REFERENCES_REQUIRED")
    output = plan.output_paths[0]
    if (Path(output).is_absolute() or ".." in Path(output).parts or ":" in output
            or not any(output.startswith(prefix) for prefix in template.allowed_output_scope)):
        raise ValueError("RESEARCH_OUTPUT_SCOPE")
    config = json.loads((root / plan.config_paths[0]).read_text(encoding="utf-8"))
    if config.get("research_kind") != kinds.get(template.template_id):
        raise ValueError("RESEARCH_CONDITION_SEMANTICS_UNRESOLVED")
    if config.get("entrypoint") != plan.script_path:
        raise ValueError("RESEARCH_SCRIPT_CONFIG_SEMANTICS_UNRESOLVED")
    if config.get("execution", {}).get("retry") is not False:
        raise ValueError("RESEARCH_RETRY_POLICY_REQUIRED")
    matrix_path = "config/model-matrix.json"
    matrix = json.loads((root / matrix_path).read_text(encoding="utf-8"))
    models = {m.get("runtime_model_name") for m in matrix.get("models", []) if m.get("enabled") is True}
    if not isinstance(config.get("model"), str) or config["model"] not in models:
        raise ValueError("RESEARCH_MODEL_AUTHORITY")
    if set(config.get("inputs", [])) != set(plan.input_paths):
        raise ValueError("RESEARCH_INPUT_SEMANTICS_CHANGED")
    if len(plan.config_paths) != 1:
        raise ValueError("RESEARCH_ADDITIONAL_CONFIG_SEMANTICS_UNRESOLVED")
    # Parameters affecting model/seed/cases/holdout are configuration-owned.
    # CLI paths are exact references, not executable shell text.
    expected_arguments = ["--config", plan.config_paths[0], "--output-root", output]
    if plan.arguments != expected_arguments:
        raise ValueError("RESEARCH_ARGUMENT_AUTHORITY")
    if kinds.get(template.template_id) == "fresh_holdout":
        freeze = config.get("holdout")
        if not isinstance(freeze, dict) or freeze.get("frozen") is not True or not freeze.get("input_hashes"):
            raise ValueError("RESEARCH_HOLDOUT_NOT_FROZEN")
        if freeze["input_hashes"] != {p: digest(root / p) for p in plan.input_paths}:
            raise ValueError("RESEARCH_HOLDOUT_CHANGED_AFTER_FREEZE")
    if matrix_path not in plan.reference_sources:
        raise ValueError("RESEARCH_MODEL_AUTHORITY_REFERENCE_REQUIRED")
    fingerprint = plan_fingerprint(root, read_paths)
    if plan.condition_fingerprint != fingerprint:
        raise ValueError("RESEARCH_CONDITION_FINGERPRINT_MISMATCH")
    condition = ResearchCondition(plan.action_id, plan.script_path, plan.config_paths[0], config["model"],
        tuple(dict.fromkeys([*plan.input_paths, *plan.reference_sources])), tuple(plan.expected_evidence_types),
        fingerprint, tuple((p, digest(root / p)) for p in dict.fromkeys(read_paths)),
        output, plan.model_dump(mode="json"))
    return condition


def research_inventory(root, contract, template):
    """Bounded trusted context; no model-generated conditions or new files."""
    paths = [p for p in files(root) if approved(p) and p.startswith(("scripts/", "config/"))]
    context = {}
    for relative in [*contract.authoritative_sources, *paths[:100]]:
        path = root / relative
        if path.is_file() and path.resolve().is_relative_to(root.resolve()):
            context[relative] = path.read_text(encoding="utf-8", errors="replace")[:16000]
    # Deterministic candidate discovery is the mock/offline Architect. REAL
    # Architect receives the same inventory and can construct other plans;
    # both must pass the identical guard.
    candidates = []
    for relative in paths:
        if not relative.startswith("config/") or not relative.endswith(".json"):
            continue
        try:
            config = json.loads((root / relative).read_text(encoding="utf-8"))
            if not isinstance(config, dict) or not config.get("research_kind"):
                continue
            scripts = [config["entrypoint"]] if isinstance(config.get("entrypoint"), str) else [
                p for p in paths if p.endswith(".py") and "--config" in context.get(p, "") and "--output-root" in context.get(p, "")]
            for script in scripts:
                refs = list(dict.fromkeys([*contract.authoritative_sources, "config/model-matrix.json"]))
                inputs = config.get("inputs", [])
                output = template.allowed_output_scope[0] + "run"
                read_paths = [script, relative, *inputs, *refs]
                candidate = ResearchExecutionPlan(action_id=template.template_id, day=contract.day, script_path=script,
                    config_paths=[relative], input_paths=inputs, output_paths=[output],
                    arguments=["--config", relative, "--output-root", output],
                    condition_fingerprint=plan_fingerprint(root, read_paths),
                    expected_evidence_types=list(template.post_action_evidence_types),
                    rationale="Existing configuration and script discovered in trusted repository.",
                    reference_sources=refs)
                validate_research_plan(root, contract, template, candidate)
                candidates.append(candidate.model_dump(mode="json"))
        except (ValueError, OSError, TypeError, KeyError):
            continue
    return {"contract": contract.model_dump(mode="json"), "action_id": template.template_id,
            "allowed_output_scope": list(template.allowed_output_scope),
            "expected_evidence_types": list(template.post_action_evidence_types),
            "context": context, "candidates": candidates}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ResearchRun:
    """Execute fixed research input in a separate source snapshot.

    The callable boundary is the deterministic subprocess runner in production
    and may be a fake model/CLI in a disposable conformance fixture. Output is
    always read from the same persisted artifact and validated independently.
    """
    def __init__(self, root: Path, storage: Path, run_command=subprocess.run):
        self.root, self.storage, self.run_command = root.resolve(), storage.resolve(), run_command

    def execute(self, condition: ResearchCondition) -> dict:
        inputs = (condition.script, condition.configuration, *condition.input_paths)
        for path in inputs:
            if not (self.root / path).resolve().is_relative_to(self.root) or not (self.root / path).is_file():
                return {"final_result": "HUMAN_ACTION_REQUIRED", "issue_classification": "HUMAN_PRODUCT_DECISION_REQUIRED",
                        "error_code": "RESEARCH_CONDITION_REQUIRED", "reason": f"Frozen research input is unavailable: {path}"}
        hashes = {path: digest(self.root / path) for path in inputs}
        if not condition.frozen_hashes or hashes != dict(condition.frozen_hashes):
            return {"final_result": "HUMAN_ACTION_REQUIRED", "issue_classification": "HUMAN_PRODUCT_DECISION_REQUIRED",
                    "error_code": "RESEARCH_CONDITION_CHANGED", "reason": "Admitted research inputs changed; a new authorized condition binding is required."}
        semantic = hashlib.sha256(json.dumps([condition.action_id, condition.condition_identity, condition.model, hashes], sort_keys=True).encode()).hexdigest()
        run = self.storage / condition.action_id / semantic
        output = run / condition.output_path
        terminal = run / "terminal.json"
        if terminal.exists():
            if json.loads(terminal.read_text(encoding="utf-8")).get("safety") != "PRESERVED":
                raise GitSafetyError("RESEARCH_SOURCE_MUTATION")
            return self._adapt(condition, run, hashes, semantic)
        if run.exists():
            return {"final_result": "HUMAN_ACTION_REQUIRED", "issue_classification": "HUMAN_PRODUCT_DECISION_REQUIRED",
                    "error_code": "RESEARCH_INFLIGHT_RECONCILIATION", "reason": "An interrupted research invocation may already have executed; it cannot be repeated unchanged."}
        run.mkdir(parents=True)
        workspace = run / "source"
        workspace.mkdir()
        for relative in files(self.root):
            if approved(relative) and (self.root / relative).is_file():
                target = workspace / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(self.root / relative, target)
        # Protected datasets/retained manifests may be read as immutable inputs,
        # but they are never copied into or staged in the user's source tree.
        for relative in inputs:
            target = workspace / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(self.root / relative, target)
        before = self._snapshot(workspace)
        source_before = self._source_snapshot()
        output.mkdir(parents=True)
        request = {"model": condition.model, "model_fingerprint": hashlib.sha256(condition.model.encode()).hexdigest(),
                   "configuration_fingerprint": hashes[condition.configuration], "input_fingerprint": semantic,
                   "action_id": condition.action_id, "condition_identity": condition.condition_identity, "input_hashes": hashes}
        (run / "condition.json").write_text(json.dumps(request, sort_keys=True), encoding="utf-8")
        (run / "execution-plan.json").write_text(json.dumps(condition.execution_plan, sort_keys=True), encoding="utf-8")
        run_before = self._snapshot(run)
        argv = [sys.executable, "-B", str(workspace / condition.script), "--config", str(workspace / condition.configuration), "--output-root", str(output)]
        try:
            completed = self.run_command(argv, cwd=workspace, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
                                         capture_output=True, timeout=3600)
            exit_code = completed.returncode
        except (OSError, subprocess.TimeoutExpired):
            exit_code = -1
        # Never persist stdout/stderr from the model boundary: it may contain
        # raw response text or hidden reasoning. Persist typed artifacts only.
        workspace_after = self._snapshot(workspace)
        run_after = self._snapshot(run)
        changed_run_paths = {
            path for path in set(run_before) | set(run_after)
            if run_before.get(path) != run_after.get(path)
        }
        allowed_output = condition.output_path.rstrip("/") + "/"
        if (before != workspace_after or source_before != self._source_snapshot()
                or any(not path.startswith(allowed_output) for path in changed_run_paths)):
            terminal.write_text(json.dumps({"exit_code": exit_code, "safety": "SOURCE_MUTATION"}), encoding="utf-8")
            raise GitSafetyError("RESEARCH_SOURCE_MUTATION")
        terminal.write_text(json.dumps({"exit_code": exit_code, "safety": "PRESERVED"}), encoding="utf-8")
        return self._adapt(condition, run, hashes, semantic)

    @staticmethod
    def _snapshot(root: Path) -> dict:
        return {path.relative_to(root).as_posix(): digest(path) for path in root.rglob("*") if path.is_file()}

    def _source_snapshot(self) -> dict:
        """Observe every source file a research command is forbidden to edit."""
        snapshot = {}
        for relative in files(self.root):
            if not approved(relative):
                continue
            path = self.root / relative
            snapshot[relative] = digest(path) if path.is_file() else "DELETED"
        return snapshot

    def _adapt(self, condition: ResearchCondition, run: Path, hashes: dict, semantic: str) -> dict:
        artifact = run / condition.output_path / "evidence.json"
        if not artifact.is_file():
            return {"final_result": "FAILED", "issue_classification": "ENGINEERING_REPAIR",
                    "error_code": "RESEARCH_RESULT_ADAPTER_MISSING", "retained_artifact_reference": str(run)}
        document = json.loads(artifact.read_text(encoding="utf-8"))
        if set(document) - {"values", "outcome"} or document.get("outcome") not in {"OBSERVED", "MODEL_QUALITY_FINDING"}:
            raise GitSafetyError("RESEARCH_ARTIFACT_CONTRACT")
        values = document.get("values", {})
        evidence = {}
        for name in condition.evidence_types:
            value = values.get(name)
            record = {"evidence_type": name, "value": value, "verified": True,
                      "source": str(artifact), "validation": {"passed": True},
                      "source_paths": [str(artifact), str(run / "condition.json")],
                      "source_hashes": {str(artifact): digest(artifact), str(run / "condition.json"): digest(run / "condition.json")},
                      "retained_artifact_reference": str(run)}
            if REGISTRY.validate(name, record):
                evidence[name] = record
        return {"final_result": "COMPLETE", "issue_classification": document["outcome"], "evidence": evidence,
                "retained_artifact_reference": str(run), "configuration_fingerprint": hashes[condition.configuration],
                "input_fingerprint": semantic}
