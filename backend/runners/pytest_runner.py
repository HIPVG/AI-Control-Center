from backend.models.result import TestResult


class PytestRunner:
    """Deterministic test-runner abstraction; mock mode avoids subprocesses."""

    def mock_pass(self, command: str) -> TestResult:
        return TestResult(command=command, passed=True, exit_code=0, summary="Mock deterministic test passed.")
