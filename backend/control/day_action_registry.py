"""Frozen, server-owned acquisition strategies for the LocalLLM Day Runner.

This module deliberately has no planner hook.  The key is exactly
``(day, evidence_type)``: adding an evidence name to the contract without a
strategy is a startup error rather than an invitation for a model to choose a
new action.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from types import MappingProxyType
from enum import Enum


class ExecutionMode(str, Enum):
    READ_ONLY = "READ_ONLY"
    BASELINE_CHECKPOINT = "BASELINE_CHECKPOINT"
    ENGINEERING_WORKTREE = "ENGINEERING_WORKTREE"
    RESEARCH_RUN = "RESEARCH_RUN"
    DECISION_OR_DOCUMENTATION_WORKTREE = "DECISION_OR_DOCUMENTATION_WORKTREE"


@dataclass(frozen=True)
class ActionTemplate:
    template_id: str
    execution_mode: ExecutionMode
    mutation_policy: str
    allowed_output_scope: tuple[str, ...]
    verification: str
    context_scope: tuple[str, ...] = ("docs/runbooks/work-plan-day1-14.md", "docs/architecture/decision-reasoning-architecture.md")
    input_evidence_types: tuple[str, ...] = ()
    post_action_evidence_types: tuple[str, ...] = ()
    git_policy: str = "PRESERVE_USER_BRANCH_INDEX_WORKTREE"
    result_adapter: str = "REGISTERED_VALUES_V1"


@dataclass(frozen=True)
class AcquisitionStrategy:
    strategy_id: str
    day: int
    evidence_type: str
    classification: str
    template: ActionTemplate | None
    authority_requirement: str | None
    reuse_policy: str = "VALIDATED_COMPATIBLE_ONLY"
    expected_information_gain: str = "Registered evidence record"
    expected_state_change: str = "None"
    provider_id: str = ""
    validator_id: str = ""
    collection_mode: str = "REUSE_THEN_ACQUIRE"
    research_sensitive: bool = False
    result_adapter: str = "REGISTERED_VALUES_V1"

    @property
    def missing_classification(self) -> str:
        return self.classification

    @property
    def action_template_id(self) -> str | None:
        return self.template.template_id if self.template else None

    @property
    def execution_mode(self) -> ExecutionMode:
        return self.template.execution_mode if self.template else ExecutionMode.READ_ONLY

    @property
    def mutation_policy(self) -> str:
        return self.template.mutation_policy if self.template else "NONE"

    @property
    def allowed_output_scope(self) -> tuple[str, ...]:
        return self.template.allowed_output_scope if self.template else ()


READ_ONLY = ActionTemplate("READ_ONLY_COLLECT", ExecutionMode.READ_ONLY, "NONE", (), "typed validator")
CHECKPOINT = ActionTemplate("D1_BASELINE_CHECKPOINT_V2", ExecutionMode.BASELINE_CHECKPOINT, "TEMPORARY_GIT_INDEX_ONLY", ("refs/heads/ai-control-center/",), "tree equals approved source snapshot")
ENGINEERING = ActionTemplate("ENGINEERING_DAY_WORK", ExecutionMode.ENGINEERING_WORKTREE, "MANAGED_WORKTREE", ("approved source/config/schema/tests/docs",), "configured deterministic tests")
RESEARCH = ActionTemplate("RESEARCH_DAY_WORK", ExecutionMode.RESEARCH_RUN, "RESULTS_ONLY", ("approved results/artifacts/logs",), "artifact validator and provenance")
DECISION = ActionTemplate("DECISION_DOCUMENTATION_DAY_WORK", ExecutionMode.DECISION_OR_DOCUMENTATION_WORKTREE, "MANAGED_WORKTREE", ("approved docs",), "typed document validator")


def _strategies(day: int, names: tuple[str, ...], classification: str, template: ActionTemplate | None, authority: str | None = None) -> dict[tuple[int, str], AcquisitionStrategy]:
    return {
        (day, name): AcquisitionStrategy(
            strategy_id=f"D{day}_{name.upper()}", day=day, evidence_type=name,
            classification=classification, template=template, authority_requirement=authority,
            expected_state_change="Produce validated evidence" if template and template.execution_mode != ExecutionMode.READ_ONLY else "Collect compatible evidence",
            provider_id=f"day-{day}:{name}", validator_id=f"evidence-registry:{name}",
            research_sensitive=bool(template and template.execution_mode == ExecutionMode.RESEARCH_RUN),
        ) for name in names
    }


# Every name is explicit.  Grouping merely avoids duplicating identical frozen
# policy fields; it does not provide a name-only fallback.
STRATEGIES: dict[tuple[int, str], AcquisitionStrategy] = {}
STRATEGIES |= _strategies(1, ("git_head", "origin_ref", "status_audit", "staging_audit", "documentation_check", "test_result"), "COLLECT_EVIDENCE", READ_ONLY)
STRATEGIES |= _strategies(1, ("commit_ref",), "PRODUCE_DAY_EVIDENCE", CHECKPOINT)
STRATEGIES |= _strategies(2, ("baseline_ref",), "HUMAN_PRODUCT_DECISION_REQUIRED", None, "PREREQUISITE_DAY_REQUIRED")
STRATEGIES |= _strategies(2, ("source_check", "deterministic_tests", "architecture_check", "test_result"), "PRODUCE_DAY_EVIDENCE", ENGINEERING)
STRATEGIES |= _strategies(2, ("preservation_audit",), "COLLECT_EVIDENCE", READ_ONLY)
STRATEGIES |= _strategies(3, ("v032_artifact", "v04_artifact"), "HUMAN_PRODUCT_DECISION_REQUIRED", None, "PREREQUISITE_DAY_REQUIRED")
STRATEGIES |= _strategies(3, ("condition_record", "comparison_metrics", "failure_policy"), "PRODUCE_DAY_EVIDENCE", RESEARCH)
STRATEGIES |= _strategies(4, ("holdout_manifest", "architecture_ref", "dagb_artifact", "retained_failures", "anti_leakage_check"), "PRODUCE_DAY_EVIDENCE", RESEARCH)
STRATEGIES |= _strategies(5, ("teacher_evidence",), "EXTERNAL_AUTHORITY_REQUIRED", None, "FROZEN_TEACHER_EVIDENCE_REQUIRED")
STRATEGIES |= _strategies(5, ("validator_result", "local_artifact"), "PRODUCE_DAY_EVIDENCE", RESEARCH)
STRATEGIES |= _strategies(5, ("limitation_record", "decision_record"), "PRODUCE_DAY_EVIDENCE", DECISION)
STRATEGIES |= _strategies(6, ("schema_contract", "source_check", "provenance_test", "deterministic_tests", "architecture_check"), "PRODUCE_DAY_EVIDENCE", ENGINEERING)
STRATEGIES |= _strategies(7, ("deterministic_tests", "validation_report"), "PRODUCE_DAY_EVIDENCE", ENGINEERING)
STRATEGIES |= _strategies(8, ("novelty_artifact", "provenance_artifact"), "PRODUCE_DAY_EVIDENCE", RESEARCH)
STRATEGIES |= _strategies(8, ("source_check", "deterministic_tests", "nonmutation_test"), "PRODUCE_DAY_EVIDENCE", ENGINEERING)
STRATEGIES |= _strategies(9, ("source_check", "deterministic_tests", "nonmutation_test", "schema_contract"), "PRODUCE_DAY_EVIDENCE", ENGINEERING)
STRATEGIES |= _strategies(10, ("performance_artifact", "condition_record", "limitation_record"), "PRODUCE_DAY_EVIDENCE", RESEARCH)
STRATEGIES |= _strategies(11, ("hardware_evidence",), "HUMAN_PRODUCT_DECISION_REQUIRED", None, "PREREQUISITE_DAY_REQUIRED")
STRATEGIES |= _strategies(11, ("deployment_matrix", "advisory_record"), "PRODUCE_DAY_EVIDENCE", DECISION)
STRATEGIES |= _strategies(12, ("operator_docs", "recovery_check", "gitignore_check"), "PRODUCE_DAY_EVIDENCE", DECISION)
STRATEGIES |= _strategies(13, ("full_test_result",), "PRODUCE_DAY_EVIDENCE", RESEARCH)
STRATEGIES |= _strategies(13, ("holdout_manifest", "architecture_ref", "result_artifact", "retained_failures"), "PRODUCE_DAY_EVIDENCE", RESEARCH)
STRATEGIES |= _strategies(13, ("classification_record", "status_summary"), "PRODUCE_DAY_EVIDENCE", DECISION)
STRATEGIES |= _strategies(14, ("sprint_review",), "PRODUCE_DAY_EVIDENCE", DECISION)
STRATEGIES |= _strategies(14, ("human_review_marker",), "HUMAN_PRODUCT_DECISION_REQUIRED", None, "HUMAN_REVIEW_MARKER_REQUIRED")

# Template identities and grouping are the action map in section 12.  Scope is
# executable relative paths, never descriptive text supplied to a model.
_ACTION_GROUPS = (
    (2, "D2_FEASIBLE_RELEVANT_GATE", ("source_check", "deterministic_tests", "architecture_check", "test_result")),
    (3, "D3_FIXED_REGRESSION", ("condition_record", "comparison_metrics", "failure_policy")),
    (4, "D4_FREEZE_HOLDOUT", ("holdout_manifest", "architecture_ref")),
    (4, "D4_DAGB_RUN", ("dagb_artifact", "retained_failures")),
    (4, "D4_ANTI_LEAKAGE", ("anti_leakage_check",)),
    (5, "D5_PLAN_SELECTION_PRECISION", ("validator_result", "local_artifact")),
    (5, "D5_PRECISION_DECISION", ("limitation_record", "decision_record")),
    (6, "D6_TEMPORAL_STATE_DESIGN", ("schema_contract", "source_check", "provenance_test", "deterministic_tests", "architecture_check")),
    (7, "D7_TEMPORAL_CASE_VALIDATION", ("deterministic_tests", "validation_report")),
    (8, "D8_NOVELTY_SCOUT", ("novelty_artifact", "provenance_artifact")),
    (8, "D8_NOVELTY_GUARD", ("source_check", "deterministic_tests", "nonmutation_test")),
    (9, "D9_EXPLANATION_STAGE", ("source_check", "deterministic_tests", "nonmutation_test", "schema_contract")),
    (10, "D10_PERFORMANCE_RUN", ("performance_artifact", "condition_record", "limitation_record")),
    (11, "D11_PRODUCT_CONFIGURATION", ("deployment_matrix", "advisory_record")),
    (12, "D12_REPRODUCIBILITY_OPERATIONS", ("operator_docs", "recovery_check", "gitignore_check")),
    (13, "D13_FULL_REGRESSION", ("full_test_result",)),
    (13, "D13_NEW_HOLDOUT", ("holdout_manifest", "architecture_ref", "result_artifact", "retained_failures")),
    (13, "D13_CLASSIFY_RESULT", ("classification_record", "status_summary")),
    (14, "D14_SPRINT_REVIEW", ("sprint_review",)),
)
ENGINEERING_SCOPES = {
    2: ("scripts/eval/decision_reasoning_v4.py", "tests/test_decision_reasoning_v4.py"),
    6: ("schemas/temporal-state.json", "scripts/eval/temporal_state.py", "tests/test_temporal_state.py", "docs/architecture/temporal-state.md"),
    7: ("tests/test_temporal_cases.py", "docs/reports/temporal-validation.md"),
    8: ("scripts/eval/novelty_scout.py", "tests/test_novelty_scout.py"),
    9: ("scripts/eval/explanation_stage.py", "schemas/explanation-stage.json", "tests/test_explanation_stage.py"),
}
for day, action_id, names in _ACTION_GROUPS:
    first = STRATEGIES[(day, names[0])]
    template = first.template
    assert template is not None
    scope = (f"results/day-runner/day-{day}/",)
    if template.execution_mode == ExecutionMode.ENGINEERING_WORKTREE:
        scope = ENGINEERING_SCOPES[day]
    elif template.execution_mode == ExecutionMode.DECISION_OR_DOCUMENTATION_WORKTREE:
        scope = (f"docs/day-{day}-report.md",)
    if action_id in {"D4_ANTI_LEAKAGE", "D13_FULL_REGRESSION"}:
        template = replace(template, execution_mode=ExecutionMode.READ_ONLY, mutation_policy="NONE")
        scope = ()
    inputs = {"D2_FEASIBLE_RELEVANT_GATE": ("baseline_ref",), "D3_FIXED_REGRESSION": ("v032_artifact", "v04_artifact"),
              "D4_DAGB_RUN": ("holdout_manifest", "architecture_ref"), "D4_ANTI_LEAKAGE": ("dagb_artifact",),
              "D11_PRODUCT_CONFIGURATION": ("hardware_evidence",)}.get(action_id, ())
    template = replace(template, template_id=action_id, allowed_output_scope=scope,
                       post_action_evidence_types=names, input_evidence_types=inputs)
    for name in names:
        STRATEGIES[(day, name)] = replace(STRATEGIES[(day, name)], template=template)
STRATEGIES = MappingProxyType(STRATEGIES)


def assert_coverage(required_pairs: set[tuple[int, str]], validator_names: set[str]) -> None:
    missing_validators = {name for _, name in required_pairs} - validator_names
    missing_strategies = required_pairs - set(STRATEGIES)
    extra_strategies = set(STRATEGIES) - required_pairs
    if missing_validators or missing_strategies or extra_strategies:
        raise ValueError(
            "Day Runner registry coverage failure: "
            f"validators={sorted(missing_validators)} strategies={sorted(missing_strategies)} extras={sorted(extra_strategies)}"
        )
