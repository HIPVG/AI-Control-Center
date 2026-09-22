"""Small configuration-driven Scenario policy for trusted capabilities."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from backend.models.next_action import NextAction, NextActionType
from backend.models.scenario import Scenario, ScenarioKind


@dataclass(frozen=True)
class ScenarioRegistry:
    scenarios: dict[str, Scenario]
    default_scenario_id: str

    def initial_state(self, *, active: bool) -> dict[str, Any]:
        return {"active_scenario_id": self.default_scenario_id if active else None, "runs": {}}

    def metadata(self, state: dict[str, Any]) -> dict[str, Any]:
        active_id = state.get("active_scenario_id")
        return {
            "active_scenario_id": active_id,
            "scenarios": [
                {"scenario_id": item.scenario_id, "title": item.title, "kind": item.kind.value,
                 "active": item.scenario_id == active_id, "max_runs": item.max_runs,
                 "required_successes": item.required_successes,
                 "checkpoint_reference": item.checkpoint_reference}
                for item in self.scenarios.values()
            ],
            "runs": state.get("runs", {}),
        }

    def activate(self, state: dict[str, Any], scenario_id: str) -> None:
        if scenario_id not in self.scenarios:
            raise ValueError("SCENARIO_NOT_CONFIGURED")
        state["active_scenario_id"] = scenario_id
        state.setdefault("runs", {}).setdefault(scenario_id, [])

    def next_action(self, state: dict[str, Any]) -> dict[str, Any] | None:
        scenario_id = state.get("active_scenario_id")
        if not scenario_id:
            return None
        scenario = self.scenarios.get(scenario_id)
        if not scenario:
            return None
        if scenario.kind == ScenarioKind.CHECKPOINT:
            action = NextAction(
                action_type=NextActionType.NO_FURTHER_ACTION,
                summary=f"{scenario.title} is read-only.",
                reason=scenario.checkpoint_reference or "SCENARIO_CHECKPOINT_READ_ONLY",
                policy_result="SCENARIO_CHECKPOINT_READ_ONLY",
            ).model_dump(mode="json")
            action["scenario_id"] = scenario_id
            return action

        runs = state.setdefault("runs", {}).setdefault(scenario_id, [])
        successes = sum(item.get("outcome") == "RESULT_RECORDED" for item in runs)
        if successes >= scenario.required_successes:
            action = NextAction(
                action_type=NextActionType.NO_FURTHER_ACTION,
                summary=f"{scenario.title} is complete.",
                reason="SCENARIO_SUCCESS_TARGET_REACHED",
                policy_result="SCENARIO_COMPLETE",
            ).model_dump(mode="json")
        elif len(runs) >= scenario.max_runs:
            action = NextAction(
                action_type=NextActionType.HUMAN_DECISION_REQUIRED,
                summary=f"{scenario.title} reached its bounded run limit.",
                reason="SCENARIO_RUN_LIMIT_REACHED",
                human_attention_required=True,
                policy_result="SCENARIO_LIMIT_REACHED",
            ).model_dump(mode="json")
        elif runs and runs[-1].get("outcome") != "RESULT_RECORDED":
            action = NextAction(
                action_type=NextActionType.HUMAN_DECISION_REQUIRED,
                summary=f"{scenario.title} stopped after a non-successful result.",
                reason="SCENARIO_RESULT_REVIEW_REQUIRED",
                human_attention_required=True,
                policy_result="SCENARIO_NON_SUCCESS_STOP",
            ).model_dump(mode="json")
        else:
            action = NextAction(
                action_type=NextActionType.RUN_TRUSTED_EXPERIMENT,
                target_id=scenario.capability_id,
                summary=f"Run the next bounded iteration of {scenario.title}.",
                reason=f"{successes}/{scenario.required_successes} successful iterations recorded.",
                policy_result="SCENARIO_TRUSTED_CAPABILITY",
            ).model_dump(mode="json")
        action["scenario_id"] = scenario_id
        return action

    def record_result(self, state: dict[str, Any], scenario_id: str, result: dict[str, Any]) -> None:
        state.setdefault("runs", {}).setdefault(scenario_id, []).append({
            "experiment_id": result.get("experiment_id"),
            "outcome": result.get("outcome"),
            "artifact_path": result.get("artifact_path"),
            "response_count": result.get("response_count", 0),
            "success_count": result.get("success_count", 0),
            "failed_count": result.get("failed_count", 0),
            "classification_reason": result.get("classification_reason"),
        })


def load_scenarios(path: Path, capability_ids: set[str]) -> ScenarioRegistry:
    values = yaml.safe_load(path.read_text(encoding="utf-8")) if path.exists() else {}
    values = values or {}
    if set(values) != {"version", "default_scenario", "scenarios"} or values["version"] != 1:
        raise ValueError("invalid scenario configuration")
    raw_scenarios = values["scenarios"]
    if not isinstance(raw_scenarios, dict) or not raw_scenarios:
        raise ValueError("at least one scenario is required")
    scenarios = {key: Scenario(scenario_id=key, **value) for key, value in raw_scenarios.items()}
    default = values["default_scenario"]
    if default not in scenarios:
        raise ValueError("default scenario is not configured")
    for scenario in scenarios.values():
        if scenario.kind == ScenarioKind.CHECKPOINT:
            if scenario.capability_id or scenario.max_runs or scenario.required_successes or not scenario.checkpoint_reference:
                raise ValueError("invalid checkpoint scenario")
        elif (not scenario.capability_id or scenario.capability_id not in capability_ids
              or scenario.max_runs < 1 or scenario.required_successes < 1
              or scenario.required_successes > scenario.max_runs):
            raise ValueError("invalid repeat scenario")
    return ScenarioRegistry(scenarios=scenarios, default_scenario_id=default)
