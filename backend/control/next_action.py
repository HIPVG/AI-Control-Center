"""Trusted policy for choosing the next bounded autonomous action."""

from typing import Any

from backend.control.goal_policy import TRUSTED_LOCAL_LLM_EXPERIMENT
from backend.models.experiment import ExperimentOutcome
from backend.models.next_action import NextAction, NextActionType


EXTERNAL_OUTCOMES = {
    ExperimentOutcome.ENGINE_UNAVAILABLE.value,
    ExperimentOutcome.MODEL_NOT_FOUND.value,
    ExperimentOutcome.TIMEOUT.value,
    ExperimentOutcome.CONFIGURATION_BLOCKED.value,
    ExperimentOutcome.HARNESS_FAILURE.value,
}


def recommend_next_action(experiment_runs: list[dict[str, Any]], configured_experiment_ids: set[str], git_candidates: list[dict[str, Any]] | None = None, zero_touch_runs: list[dict[str, Any]] | None = None) -> NextAction:
    """Return only a configured experiment action, or explicit attention.

    Browser input is deliberately absent from this decision.  A successful
    continuation remains inside the fixed LocalLLM experiment authority.
    """
    if git_candidates:
        candidate = git_candidates[0]
        return NextAction(
            action_type=NextActionType.COMPLETE_VERIFIED_WORK,
            target_id=str(candidate["run_id"]),
            summary="Commit and push the verified agent-branch work, then prepare its pull request.",
            reason=f"{candidate['task_id']} passed deterministic verification and scope validation.",
            policy_result="VERIFIED_AGENT_BRANCH_ONLY",
        )
    latest_zero_touch = zero_touch_runs[-1] if zero_touch_runs else None
    if latest_zero_touch and latest_zero_touch.get("status") == "COMPLETE":
        return NextAction(
            action_type=NextActionType.NO_FURTHER_ACTION,
            summary="The bounded Zero-Touch flow is complete.",
            reason=str(latest_zero_touch.get("completion_reason") or "TRUSTED_FLOW_COMPLETE"),
            policy_result="TERMINAL_COMPLETION",
        )
    latest = experiment_runs[-1] if experiment_runs else None
    if latest and latest.get("outcome") in EXTERNAL_OUTCOMES:
        return NextAction(
            action_type=NextActionType.EXTERNAL_ACTION_REQUIRED,
            summary="External runtime action is required before continuing.",
            reason=str(latest.get("classification_reason") or latest["outcome"]),
            human_attention_required=True,
            policy_result="EXTERNAL_ACTION_REQUIRED",
        )
    if TRUSTED_LOCAL_LLM_EXPERIMENT in configured_experiment_ids:
        reason = "No prior trusted experiment result is recorded." if latest is None else "The prior trusted experiment completed without a runtime-blocking outcome."
        return NextAction(
            action_type=NextActionType.RUN_TRUSTED_EXPERIMENT,
            target_id=TRUSTED_LOCAL_LLM_EXPERIMENT,
            summary="Continue with the configured trusted LocalLLM process-consistency experiment.",
            reason=reason,
            policy_result="TRUSTED_EXPERIMENT_ONLY",
        )
    return NextAction(
        action_type=NextActionType.HUMAN_DECISION_REQUIRED,
        summary="No configured trusted continuation is available.",
        reason="TRUSTED_EXPERIMENT_NOT_CONFIGURED",
        human_attention_required=True,
        policy_result="NO_SAFE_ACTION",
    )
