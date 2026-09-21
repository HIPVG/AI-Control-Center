from pathlib import Path
import subprocess

from backend.control.daily_operation import DailyOperationService, TASK_NAME


def completed(returncode: int) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess([], returncode, "", "")


def test_non_windows_autostart_fails_closed_without_subprocess(tmp_path: Path):
    calls = []
    service = DailyOperationService(tmp_path, platform_name="posix", command_runner=lambda *args, **kwargs: calls.append(args))
    assert service.autostart_status()["state"] == "WINDOWS_REQUIRED"
    assert service.enable_autostart()["action"] == "NOT_SUPPORTED"
    assert calls == []


def test_enable_autostart_uses_only_fixed_logon_task_and_never_overwrites(tmp_path: Path):
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "start.ps1").write_text("# launcher", encoding="utf-8")
    calls: list[list[str]] = []

    def runner(argv, **kwargs):
        calls.append(argv)
        return completed(1 if argv[1] == "/Query" and len(calls) == 1 else 0)

    result = DailyOperationService(tmp_path, platform_name="nt", command_runner=runner).enable_autostart()
    create = next(call for call in calls if call[1] == "/Create")
    assert result["action"] == "ENABLED"
    assert create[:7] == ["schtasks.exe", "/Create", "/TN", TASK_NAME, "/SC", "ONLOGON", "/RL"]
    assert "/F" not in create
    assert "start.ps1" in create[-1]


def test_existing_autostart_is_left_unchanged(tmp_path: Path):
    calls = []
    service = DailyOperationService(tmp_path, platform_name="nt", command_runner=lambda argv, **kwargs: calls.append(argv) or completed(0))
    assert service.enable_autostart()["action"] == "ALREADY_ENABLED"
    assert calls == [["schtasks.exe", "/Query", "/TN", TASK_NAME]]


def test_unavailable_scheduler_fails_closed_without_leaking_a_system_error(tmp_path: Path):
    service = DailyOperationService(tmp_path, platform_name="nt", command_runner=lambda *args, **kwargs: (_ for _ in ()).throw(OSError("unavailable")))
    assert service.autostart_status()["state"] == "NOT_ENABLED"
    assert service.enable_autostart()["action"] == "CONFIGURATION_BLOCKED"


def test_startup_diagnostics_expose_only_allow_listed_bounded_codes(tmp_path: Path):
    log = tmp_path / "logs" / "startup.log"
    log.parent.mkdir()
    log.write_text(
        "2026-09-22T00:00:00.0000000Z | REPOSITORY_ROOT_READY\n"
        "2026-09-22T00:00:01.0000000Z | UVICORN_LAUNCHED | port=8000\n"
        "2026-09-22T00:00:02.0000000Z | SECRET=must-not-render\n",
        encoding="utf-8",
    )
    diagnostics = DailyOperationService(tmp_path, platform_name="nt").startup_diagnostics()
    assert diagnostics == [{"code": "REPOSITORY_ROOT_READY"}, {"code": "UVICORN_LAUNCHED", "value": 8000}]


def test_production_launcher_is_cwd_independent_and_writes_bounded_startup_codes():
    launcher = Path("scripts/start.ps1").read_text(encoding="utf-8")
    assert "$RepositoryRoot = Split-Path -Parent $PSScriptRoot" in launcher
    assert "Set-Location -LiteralPath $RepositoryRoot" in launcher
    assert "Get-Command python -CommandType Application" in launcher
    assert "& $python.Path -m uvicorn" in launcher
    assert "REPOSITORY_ROOT_READY" in launcher
    assert "PYTHON_UNAVAILABLE" in launcher
    assert "UVICORN_LAUNCHED" in launcher
