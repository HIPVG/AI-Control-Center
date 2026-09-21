"""Bounded, user-local Windows automatic-start support for daily operation."""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from typing import Callable


TASK_NAME = "AI Control Center"
STARTUP_LOG_NAME = "startup.log"
STARTUP_CODES = {
    "REPOSITORY_ROOT_UNAVAILABLE", "REPOSITORY_ROOT_READY", "PYTHON_UNAVAILABLE",
    "PYTHON_312_UNAVAILABLE", "PYTHON_RESOLVED", "UVICORN_LAUNCHED", "UVICORN_EXITED", "LAUNCH_EXCEPTION",
}
STARTUP_REASONS = {"PYTHON_INVOCATION_FAILED", "STARTUP_INITIALIZATION_FAILED"}
STARTUP_EXCEPTION_TYPES = {
    "ApplicationFailedException", "CommandNotFoundException", "IOException",
    "RuntimeException", "UnauthorizedAccessException", "UNKNOWN_EXCEPTION",
}


class DailyOperationService:
    """Expose only the fixed automatic-start action required by the dashboard.

    The service never accepts a browser-supplied executable, path, or command.
    It registers a user-logon task only after the user explicitly selects the
    Dashboard control; it does not start or alter a task that already exists.
    """

    def __init__(
        self,
        project_root: Path,
        *,
        platform_name: str | None = None,
        command_runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    ) -> None:
        self.project_root = project_root.resolve()
        self.platform_name = platform_name or os.name
        self.command_runner = command_runner

    def autostart_status(self) -> dict[str, object]:
        diagnostics = self.startup_diagnostics()
        if self.platform_name != "nt":
            return {"supported": False, "enabled": False, "task_name": TASK_NAME, "state": "WINDOWS_REQUIRED", "startup_diagnostics": diagnostics}
        completed = self._run(["schtasks.exe", "/Query", "/TN", TASK_NAME])
        return {
            "supported": True,
            "enabled": completed.returncode == 0,
            "task_name": TASK_NAME,
            "state": "ENABLED" if completed.returncode == 0 else "NOT_ENABLED",
            "startup_diagnostics": diagnostics,
        }

    def startup_diagnostics(self) -> list[dict[str, object]]:
        """Return only allow-listed startup state codes from the fixed local log."""
        path = self.project_root / "logs" / STARTUP_LOG_NAME
        try:
            lines = path.read_text(encoding="utf-8").splitlines()[-12:]
        except OSError:
            return []
        diagnostics: list[dict[str, object]] = []
        for line in lines:
            match = re.fullmatch(r"[^|]{1,40}\s+\|\s+([A-Z_]+)(?:\s+\|\s+(.{1,160}))?", line.strip())
            if not match or match.group(1) not in STARTUP_CODES:
                continue
            item: dict[str, object] = {"code": match.group(1)}
            details = match.group(2) or ""
            for key, value in re.findall(r"(port|exit_code|version|reason|type)=([^\s]+)", details):
                if key in {"port", "exit_code"} and value.isdigit() and len(value) <= 5:
                    item["value"] = int(value)
                elif key == "version" and value == "3.12":
                    item["version"] = value
                elif key == "reason" and value in STARTUP_REASONS:
                    item["reason"] = value
                elif key == "type" and value in STARTUP_EXCEPTION_TYPES:
                    item["exception_type"] = value
            diagnostics.append(item)
        return diagnostics

    def enable_autostart(self) -> dict[str, object]:
        current = self.autostart_status()
        if not current["supported"]:
            return {**current, "action": "NOT_SUPPORTED"}
        if current["enabled"]:
            return {**current, "action": "ALREADY_ENABLED"}

        launcher = (self.project_root / "scripts" / "start.ps1").resolve()
        if not launcher.is_file() or not launcher.is_relative_to(self.project_root):
            return {**current, "action": "CONFIGURATION_BLOCKED"}
        powershell = Path(os.environ.get("WINDIR", r"C:\\Windows")) / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe"
        task_command = f'"{powershell}" -NoProfile -ExecutionPolicy Bypass -File "{launcher}"'
        completed = self._run([
            "schtasks.exe", "/Create", "/TN", TASK_NAME, "/SC", "ONLOGON", "/RL", "LIMITED", "/TR", task_command,
        ])
        if completed.returncode != 0:
            return {**current, "action": "ENABLE_FAILED"}
        return {**self.autostart_status(), "action": "ENABLED"}

    def _run(self, argv: list[str]) -> subprocess.CompletedProcess[str]:
        try:
            return self.command_runner(argv, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=5, check=False)
        except (OSError, subprocess.TimeoutExpired):
            # Automatic start is optional operational convenience. Its local
            # availability must never make the Dashboard health endpoint fail.
            return subprocess.CompletedProcess(argv, 1, "", "")
