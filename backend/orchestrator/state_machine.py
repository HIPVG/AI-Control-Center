from backend.models.state import RunState, WorkflowState


class InvalidTransition(ValueError):
    """Raised when a workflow attempts a transition not sanctioned by policy."""


class StateManager:
    """The only component allowed to mutate a workflow's state."""

    _TRANSITIONS: dict[WorkflowState, set[WorkflowState]] = {
        WorkflowState.IDLE: {WorkflowState.PLANNING, WorkflowState.STOPPED},
        WorkflowState.PLANNING: {WorkflowState.PRECHECK, WorkflowState.HUMAN_REVIEW, WorkflowState.STOPPED},
        WorkflowState.PRECHECK: {WorkflowState.RUNNING_TEST, WorkflowState.HUMAN_REVIEW, WorkflowState.FAILED, WorkflowState.STOPPED},
        WorkflowState.RUNNING_TEST: {WorkflowState.COMPLETE, WorkflowState.TRIAGE, WorkflowState.EVALUATING, WorkflowState.FAILED, WorkflowState.STOPPED},
        WorkflowState.TRIAGE: {WorkflowState.CODEX_FIX, WorkflowState.HUMAN_REVIEW, WorkflowState.FAILED, WorkflowState.STOPPED},
        WorkflowState.CODEX_FIX: {WorkflowState.RUNNING_TEST, WorkflowState.HUMAN_REVIEW, WorkflowState.FAILED, WorkflowState.STOPPED},
        WorkflowState.EVALUATING: {WorkflowState.COMPLETE, WorkflowState.CODEX_FIX, WorkflowState.HUMAN_REVIEW, WorkflowState.FAILED, WorkflowState.STOPPED},
        WorkflowState.COMPLETE: {WorkflowState.IDLE},
        WorkflowState.HUMAN_REVIEW: {WorkflowState.IDLE, WorkflowState.STOPPED},
        WorkflowState.FAILED: {WorkflowState.IDLE, WorkflowState.STOPPED},
        WorkflowState.STOPPED: {WorkflowState.IDLE},
    }

    def __init__(self, initial: RunState | None = None) -> None:
        self._run_state = initial or RunState()

    @property
    def current(self) -> RunState:
        return self._run_state.model_copy(deep=True)

    def transition(self, target: WorkflowState, *, reason: str | None = None) -> RunState:
        source = self._run_state.state
        if target not in self._TRANSITIONS[source]:
            raise InvalidTransition(f"{source.value} cannot transition to {target.value}")
        self._run_state = self._run_state.model_copy(update={"state": target, "reason": reason})
        return self.current

    def start_task(self, task_id: str) -> RunState:
        if self._run_state.state != WorkflowState.IDLE:
            raise InvalidTransition("a task can start only from IDLE")
        self._run_state = RunState(state=WorkflowState.IDLE, task_id=task_id)
        return self.current

    def increment_retry(self) -> RunState:
        self._run_state = self._run_state.model_copy(update={"retry_count": self._run_state.retry_count + 1})
        return self.current
