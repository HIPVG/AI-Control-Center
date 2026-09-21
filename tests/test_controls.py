from backend.control.git_guard import GitGuard
from backend.control.scope_guard import ScopeGuard
from backend.control.token_budget import BudgetDecision, BudgetConfig, CodexBudget, TokenBudgetManager
from backend.models.result import TokenUsage
from backend.models.task import TaskType, WorkOrder


def work_order():
    return WorkOrder(task_id="T-1", goal="Fix one file", task_type=TaskType.CODE_FIX, allowed_files=["src/a.py"], acceptance_tests=["pytest tests/test_a.py"], needs_codex=True)


def test_task_token_budget_is_rejected():
    manager = TokenBudgetManager(BudgetConfig(codex=CodexBudget(task_input_tokens=10, task_output_tokens=10)))
    assert manager.check(TokenUsage(input_tokens=11), retry_count=0) == BudgetDecision.TASK_BUDGET_EXCEEDED


def test_retry_limit_is_rejected():
    manager = TokenBudgetManager(BudgetConfig(codex=CodexBudget(max_retry=2)))
    assert manager.check(TokenUsage(), retry_count=2) == BudgetDecision.RETRY_LIMIT_EXCEEDED


def test_scope_guard_accepts_allowed_file():
    assert ScopeGuard().check(work_order(), ["src/a.py"]).allowed


def test_scope_guard_detects_out_of_scope_file():
    check = ScopeGuard().check(work_order(), ["src/a.py", "src/b.py"])
    assert not check.allowed
    assert check.out_of_scope == ["src/b.py"]


def test_git_guard_blocks_destructive_command():
    assert not GitGuard().check("git reset --hard").allowed
