from typing import Protocol

from backend.models.evaluation import EvaluationDecision, EvaluationResult
from backend.models.result import ExecutionResult, TestResult


class Evaluator(Protocol):
    def evaluate(self, execution: ExecutionResult, test: TestResult) -> EvaluationResult: ...


class MockEvaluator:
    def evaluate(self, execution: ExecutionResult, test: TestResult) -> EvaluationResult:
        decision = EvaluationDecision.PASS if execution.test_result == "pass" and test.passed else EvaluationDecision.REPAIR
        return EvaluationResult(
            decision=decision,
            score={"groundedness": 4.8, "process_consistency": 4.7, "instruction_fit": 4.9, "information_capacity": 4.6},
            repair_instruction=None if decision == EvaluationDecision.PASS else "Repair the failing deterministic test.",
        )
