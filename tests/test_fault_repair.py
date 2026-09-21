import subprocess
from pathlib import Path

from backend.control.faults import FaultProfile, FaultRegistry, load_fault_registry
from backend.control.projects import ConfiguredProject, ProjectRegistry
from backend.control.tasks import TaskCommand
from backend.models.result import ExecutionResult, ProcessDiagnostics, TokenUsage
from backend.models.runtime import CodexMode, CodexRuntimeConfig, CommandRunResult, RuntimeConfig
from backend.orchestrator.engine import ControlCenterEngine


ORIGINAL = "anomalous=difference>0\n"
INJECTED = "anomalous=0<difference<60\n"


def profile(*, max_retry=1):
    return FaultProfile(
        fault_id="PC-001-A-CONTROLLED-FAULT",
        project_id="local_llm_lab",
        task_id="PC-001-A-FAULT-REPAIR",
        base_case="PC-001-A",
        title="Controlled repair",
        target_file="scripts/process_consistency.py",
        fault_type="comparison reversal",
        fault_description="Never include this explicit injection answer in Codex context.",
        expected_original=ORIGINAL,
        injected_text=INJECTED,
        baseline=TaskCommand(argv=["python", "scripts/validate.py"]),
        postcheck=TaskCommand(argv=["python", "scripts/validate.py"]),
        allowed_files=["scripts/process_consistency.py"],
        context_files=["scripts/process_consistency.py"],
        max_retry=max_retry,
        expected_precheck_text="case_semantics",
    )


def git_source(tmp_path: Path) -> Path:
    root = tmp_path / "LocalLLM-Lab"
    (root / "scripts").mkdir(parents=True)
    (root / "scripts" / "process_consistency.py").write_text(ORIGINAL, encoding="utf-8")
    for argv in (
        ["git", "init"],
        ["git", "add", "scripts/process_consistency.py"],
        ["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-m", "initial"],
    ):
        completed = subprocess.run(argv, cwd=root, capture_output=True, text=True, check=False)
        assert completed.returncode == 0, completed.stderr
    return root


class RepairWriter:
    def __init__(self, *, mode="restore"):
        self.mode = mode
        self.called = 0
        self.prompts = []

    def run_worktree_task(self, working_directory, prompt):
        self.called += 1
        self.prompts.append(prompt)
        target = working_directory / "scripts" / "process_consistency.py"
        if self.mode == "restore":
            target.write_text(ORIGINAL, encoding="utf-8")
        elif self.mode == "different":
            target.write_text("anomalous=difference>=0\n", encoding="utf-8")
        elif self.mode == "outside":
            target.write_text(ORIGINAL, encoding="utf-8")
            (working_directory / "outside.py").write_text("unexpected\n", encoding="utf-8")
        return ExecutionResult(
            status="completed", test_result="pending", summary="mock repair", exit_code=0,
            token_usage=TokenUsage(input_tokens=11, cached_input_tokens=4, output_tokens=3, available=True),
            diagnostics=ProcessDiagnostics(thread_started=True, turn_started=True, turn_completed=True),
        )


def engine_for(tmp_path, runner, *, profile_value=None):
    source = git_source(tmp_path)
    project = ProjectRegistry(projects={"local_llm_lab": ConfiguredProject(name="LocalLLM-Lab", path=source, default_branch="main")})
    faults = FaultRegistry(faults={"PC-001-A-CONTROLLED-FAULT": profile_value or profile()})
    runtime = RuntimeConfig(codex=CodexRuntimeConfig(mode=CodexMode.REAL, executable="codex"))
    engine = ControlCenterEngine(runtime_config=runtime, real_runner=runner, project_registry=project, fault_registry=faults, worktree_root=tmp_path / "worktrees")
    return engine, source


def command_results(engine, values):
    sequence = iter(values)

    def fake(command, cwd, artifact_root):
        value = next(sequence)
        return CommandRunResult(argv=command.argv, cwd=str(cwd), **value)

    engine._run_task_command = fake


def passing_sequence():
    return [
        {"exit_code": 0, "passed": True},
        {"exit_code": 1, "passed": False, "stdout": '{"code":"case_semantics","detail":"PC-001-A"}'},
        {"exit_code": 0, "passed": True},
    ]


def test_fault_profile_is_narrow_and_real_profile_is_configured():
    actual = load_fault_registry(Path("config/faults.yaml")).get("PC-001-A-CONTROLLED-FAULT")
    assert actual is not None
    assert actual.base_case == "PC-001-A"
    assert actual.allowed_files == ["scripts/process_consistency.py"]
    assert actual.context_files == ["scripts/process_consistency.py"]
    assert actual.max_retry == 1


def test_baseline_then_worktree_only_fault_repair_completes_and_records_tokens(tmp_path):
    runner = RepairWriter()
    engine, source = engine_for(tmp_path, runner)
    command_results(engine, passing_sequence())
    result = engine.run_fault_repair("PC-001-A-CONTROLLED-FAULT")
    assert result["final_result"] == "COMPLETE"
    assert result["baseline_result"] == "PASS"
    assert result["fault_injected"] is True
    assert result["precheck_result"] == "FAIL"
    assert result["scope_guard_result"] == "PASS"
    assert result["repair_delta_files"] == ["scripts/process_consistency.py"]
    assert result["postcheck_result"] == "PASS"
    assert result["original_file_match"] is True
    assert result["token_usage"] == TokenUsage(input_tokens=11, cached_input_tokens=4, output_tokens=3, available=True).model_dump()
    assert source.joinpath("scripts/process_consistency.py").read_text(encoding="utf-8") == ORIGINAL
    assert Path(result["worktree_path"], "scripts/process_consistency.py").read_text(encoding="utf-8") == ORIGINAL
    assert "Never include this explicit injection answer" not in runner.prompts[0]
    assert "scripts/process_consistency.py" in runner.prompts[0]
    assert result["context_character_count"] > 0
    assert result["context_byte_count"] >= result["context_character_count"]


def test_baseline_failure_blocks_injection_and_codex(tmp_path):
    runner = RepairWriter()
    engine, source = engine_for(tmp_path, runner)
    command_results(engine, [{"exit_code": 1, "passed": False, "stdout": "baseline failure"}])
    result = engine.run_fault_repair("PC-001-A-CONTROLLED-FAULT")
    assert result["final_result"] == "HUMAN_REVIEW"
    assert result["error_code"] == "BASELINE_FAILED"
    assert not result["fault_injected"]
    assert runner.called == 0
    assert source.joinpath("scripts/process_consistency.py").read_text(encoding="utf-8") == ORIGINAL


def test_fault_that_does_not_fail_is_rejected_without_codex(tmp_path):
    runner = RepairWriter()
    engine, _ = engine_for(tmp_path, runner)
    command_results(engine, [{"exit_code": 0, "passed": True}, {"exit_code": 0, "passed": True}])
    result = engine.run_fault_repair("PC-001-A-CONTROLLED-FAULT")
    assert result["error_code"] == "FAULT_INJECTION_INVALID"
    assert result["fault_injected"]
    assert not result["codex_invoked"]
    assert runner.called == 0


def test_infrastructure_precheck_does_not_invoke_codex(tmp_path):
    runner = RepairWriter()
    engine, _ = engine_for(tmp_path, runner)
    command_results(engine, [{"exit_code": 0, "passed": True}, {"passed": False, "error_code": "COMMAND_NOT_FOUND"}])
    result = engine.run_fault_repair("PC-001-A-CONTROLLED-FAULT")
    assert result["final_result"] == "HUMAN_REVIEW"
    assert result["triage_result"] == "INFRASTRUCTURE_FAILURE"
    assert runner.called == 0


def test_out_of_scope_repair_is_human_review(tmp_path):
    runner = RepairWriter(mode="outside")
    engine, _ = engine_for(tmp_path, runner)
    command_results(engine, passing_sequence())
    result = engine.run_fault_repair("PC-001-A-CONTROLLED-FAULT")
    assert result["error_code"] == "SCOPE_GUARD_FAILED"
    assert result["scope_guard_result"] == "FAIL"
    assert result["final_result"] == "HUMAN_REVIEW"


def test_passing_but_different_repair_requires_human_review(tmp_path):
    runner = RepairWriter(mode="different")
    engine, _ = engine_for(tmp_path, runner)
    command_results(engine, passing_sequence())
    result = engine.run_fault_repair("PC-001-A-CONTROLLED-FAULT")
    assert result["postcheck_result"] == "PASS"
    assert result["original_file_match"] is False
    assert result["error_code"] == "ORIGINAL_FILE_MISMATCH"
    assert result["final_result"] == "HUMAN_REVIEW"


def test_postcheck_failure_uses_only_configured_bounded_retry(tmp_path):
    runner = RepairWriter()
    engine, _ = engine_for(tmp_path, runner)
    command_results(engine, [
        {"exit_code": 0, "passed": True},
        {"exit_code": 1, "passed": False, "stdout": "case_semantics"},
        {"exit_code": 1, "passed": False, "stdout": "still failing"},
        {"exit_code": 1, "passed": False, "stdout": "still failing"},
    ])
    result = engine.run_fault_repair("PC-001-A-CONTROLLED-FAULT")
    assert result["error_code"] == "RETRY_LIMIT_EXCEEDED"
    assert len(result["codex_attempts"]) == 2
    assert runner.called == 2
