import pytest

from backend.models.state import WorkflowState
from backend.orchestrator.state_machine import InvalidTransition, StateManager


def test_valid_transition_sequence():
    manager = StateManager()
    manager.start_task("T-1")
    assert manager.transition(WorkflowState.PLANNING).state == WorkflowState.PLANNING
    assert manager.transition(WorkflowState.PRECHECK).state == WorkflowState.PRECHECK
    assert manager.transition(WorkflowState.RUNNING_TEST).state == WorkflowState.RUNNING_TEST
    assert manager.transition(WorkflowState.COMPLETE).state == WorkflowState.COMPLETE


def test_forbidden_transition_is_rejected():
    with pytest.raises(InvalidTransition):
        StateManager().transition(WorkflowState.COMPLETE)
