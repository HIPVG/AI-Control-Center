"""Bounded, user-local Windows automatic-start support for daily operation."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Callable


TASK_NAME = "AI Control Center"


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
        if self.platform_name != "nt":
            return {"supported": False, "enabled": False, "task_name": TASK_NAME, "state": "WINDOWS_REQUIRED"}
        completed = self._run(["schtasks.exe", "/Query", "/TN", TASK_NAME])
        return {
            "supported": True,
            "enabled": completed.returncode == 0,
            "task_name": TASK_NAME,
            "state": "ENABLED" if completed.returncode == 0 else "NOT_ENABLED",
        }

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
