import json

from backend.control.context_broker import TaskContext
from backend.models.result import ExecutionResult, TokenUsage


class CodexRunner:
    """Future adapter boundary for `codex exec --json`."""

    @staticmethod
    def parse_usage(raw_json: str) -> TokenUsage:
        payload = json.loads(raw_json)
        usage = payload.get("usage", payload)
        return TokenUsage(
            input_tokens=int(usage.get("input_tokens", 0)),
            cached_input_tokens=int(usage.get("cached_input_tokens", 0)),
            output_tokens=int(usage.get("output_tokens", 0)),
        )


class MockCodexRunner(CodexRunner):
    def run(self, context: TaskContext) -> ExecutionResult:
        return ExecutionResult(
            status="completed",
            files_changed=[context.allowed_files[0]],
            tests_run=context.acceptance_tests,
            test_result="pass",
            summary="Mock builder applied an in-scope change.",
            token_usage=TokenUsage(),
        )
