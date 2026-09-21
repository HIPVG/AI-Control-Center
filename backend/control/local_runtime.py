"""Fixed, server-owned readiness checks for approved local dependencies."""

from __future__ import annotations

import shutil
import subprocess
import time
from collections.abc import Callable

from backend.models.local_runtime import LocalRuntimeReadiness, LocalRuntimeReadinessState


class ApprovedLocalRuntimeService:
    """Prepare the one approved local Ollama runtime without installation or input.

    The command vectors and retry bound are deliberately constants.  This class
    accepts no browser data and never downloads a runtime or model.
    """

    RUNTIME_ID = "ollama"
    CHECK_COMMAND = ("ollama", "list")
    START_COMMAND = ("ollama", "serve")
    START_WAIT_ATTEMPTS = 8
    CHECK_TIMEOUT_SECONDS = 5

    def __init__(
        self,
        *,
        which: Callable[[str], str | None] = shutil.which,
        run: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
        popen: Callable[..., subprocess.Popen[bytes]] = subprocess.Popen,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._which = which
        self._run = run
        self._popen = popen
        self._sleep = sleep

    def readiness(self) -> LocalRuntimeReadiness:
        """Return readiness, starting only the fixed approved runtime if needed."""
        if not self._which(self.RUNTIME_ID):
            return self._result(LocalRuntimeReadinessState.EXTERNAL_ACTION_REQUIRED, "OLLAMA_NOT_INSTALLED", 0)
        if self._is_ready():
            return self._result(LocalRuntimeReadinessState.READY, "OLLAMA_READY", 0)
        try:
            self._popen(
                list(self.START_COMMAND), shell=False, stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        except (OSError, subprocess.SubprocessError):
            return self._result(LocalRuntimeReadinessState.EXTERNAL_ACTION_REQUIRED, "OLLAMA_START_FAILED", 0)
        for attempt in range(1, self.START_WAIT_ATTEMPTS + 1):
            self._sleep(1)
            if self._is_ready():
                return self._result(LocalRuntimeReadinessState.STARTED, "OLLAMA_STARTED", attempt, started=True)
        return self._result(LocalRuntimeReadinessState.EXTERNAL_ACTION_REQUIRED, "OLLAMA_START_TIMEOUT", self.START_WAIT_ATTEMPTS)

    def _is_ready(self) -> bool:
        try:
            completed = self._run(
                list(self.CHECK_COMMAND), shell=False, capture_output=True,
                text=True, timeout=self.CHECK_TIMEOUT_SECONDS, check=False,
            )
        except (OSError, subprocess.SubprocessError):
            return False
        return completed.returncode == 0

    @staticmethod
    def _result(
        state: LocalRuntimeReadinessState, reason_code: str, attempts: int, *, started: bool = False,
    ) -> LocalRuntimeReadiness:
        return LocalRuntimeReadiness(
            state=state, reason_code=reason_code, attempts=attempts,
            started_by_control_center=started,
        )
