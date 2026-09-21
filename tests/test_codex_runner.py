import subprocess

import pytest

from backend.control.token_budget import BudgetConfig, CodexBudget, TokenBudgetManager
from backend.models.result import ExecutionResult, TokenUsage
from backend.models.runtime import CodexMode, CodexRuntimeConfig, RuntimeConfig
from backend.orchestrator.engine import ControlCenterEngine
from backend.runners.codex import CodexRunner, RealCodexRunner, SMOKE_CONTENT, SmokeWorkspace


def real_config(executable="codex"):
    return CodexRuntimeConfig(mode=CodexMode.REAL, executable=executable, timeout_seconds=5)


def test_default_runtime_mode_is_mock():
    assert RuntimeConfig().codex.mode == CodexMode.MOCK


def test_jsonl_usage_parsing_uses_reported_values_only():
    parsed = CodexRunner.parse_jsonl('{"type":"started"}\n{"usage":{"input_tokens":12,"cached_input_tokens":3,"output_tokens":4}}')
    assert parsed.malformed_lines == 0
    assert parsed.token_usage == TokenUsage(input_tokens=12, cached_input_tokens=3, output_tokens=4, available=True)


def test_malformed_jsonl_is_reported_without_raising(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "backend.runners.codex.subprocess.run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0, stdout="not-json", stderr=""),
    )
    workspace = SmokeWorkspace(tmp_path / "smoke")
    run = workspace.create_run()
    result = RealCodexRunner(real_config()).run_smoke(run, workspace.result_path(run))
    assert result.error_code == "MALFORMED_JSONL"


def test_executable_not_found_is_structured_error(tmp_path):
    workspace = SmokeWorkspace(tmp_path / "smoke")
    run = workspace.create_run()
    result = RealCodexRunner(real_config("missing-codex-executable")).run_smoke(run, workspace.result_path(run))
    assert result.error_code == "CODEX_NOT_FOUND"


def test_timeout_is_structured_error(monkeypatch, tmp_path):
    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(args[0], kwargs["timeout"], stderr="timed out")

    monkeypatch.setattr("backend.runners.codex.subprocess.run", timeout)
    workspace = SmokeWorkspace(tmp_path / "smoke")
    run = workspace.create_run()
    result = RealCodexRunner(real_config()).run_smoke(run, workspace.result_path(run))
    assert result.error_code == "CODEX_TIMEOUT"


def test_smoke_workspace_rejects_path_outside_root(tmp_path):
    workspace = SmokeWorkspace(tmp_path / "smoke")
    with pytest.raises(ValueError):
        workspace.result_path(tmp_path)


def test_smoke_acceptance_is_deterministic(tmp_path):
    workspace = SmokeWorkspace(tmp_path / "smoke")
    run = workspace.create_run()
    target = workspace.result_path(run)
    target.write_text(SMOKE_CONTENT, encoding="utf-8")
    assert workspace.accepts(target)
    target.write_text(f"{SMOKE_CONTENT}\n", encoding="utf-8")
    assert not workspace.accepts(target)


def test_real_smoke_is_rejected_while_mode_is_mock(tmp_path):
    engine = ControlCenterEngine(runtime_config=RuntimeConfig(), smoke_root=tmp_path / "smoke")
    result = engine.run_codex_smoke()
    assert result["status"] == "rejected"
    assert result["error_code"] == "REAL_MODE_REQUIRED"


class SmokeWriter:
    def __init__(self):
        self.called = False

    def run_smoke(self, smoke_directory, target):
        self.called = True
        target.write_text(SMOKE_CONTENT, encoding="utf-8")
        return ExecutionResult(
            status="completed",
            test_result="pending",
            summary="mocked real smoke",
            token_usage=TokenUsage(input_tokens=7, cached_input_tokens=2, output_tokens=3, available=True),
        )


def test_budget_guard_runs_before_real_execution(tmp_path):
    runner = SmokeWriter()
    runtime = RuntimeConfig(codex=real_config())
    engine = ControlCenterEngine(runtime_config=runtime, smoke_root=tmp_path / "smoke", real_runner=runner)
    engine.budgets = TokenBudgetManager(BudgetConfig(codex=CodexBudget(max_retry=0)))
    result = engine.run_codex_smoke()
    assert result["error_code"] == "RETRY_LIMIT_EXCEEDED"
    assert not runner.called


def test_real_smoke_records_actual_reported_usage(tmp_path):
    runtime = RuntimeConfig(codex=real_config())
    engine = ControlCenterEngine(runtime_config=runtime, smoke_root=tmp_path / "smoke", real_runner=SmokeWriter())
    result = engine.run_codex_smoke()
    assert result["status"] == "completed"
    assert result["deterministic_passed"]
    assert engine.status()["token_usage"]["input_tokens"] == 7
