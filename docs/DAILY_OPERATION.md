# PowerShell-free daily operation

## Purpose

M23 makes the Dashboard the normal daily control surface. PowerShell remains a
setup and diagnostic tool, not part of a normal Day run.

## Dashboard controls

Once the local server is available, the Dashboard shows a bounded **Daily
Operation** card and provides only trusted controls:

- **HEALTHY** confirms that this Control Center server responded and shows the
  current Day state.
- **Enable automatic startup** explicitly registers the fixed, per-user Windows
  logon task named `AI Control Center`. It runs only this repository's
  `scripts/start.ps1` on `127.0.0.1:8000` at the next sign-in.
- **Run Codex-Core single step** starts the selected configured plan.
- **Run continuously** starts or resumes only the remaining trusted queue.
- **Stop Day** stops the active Day. The state remains visible and a supported
  Day can later be resumed from the same Dashboard.

The browser never sends a command, path, port, prompt, model, budget, or task
definition. The automatic-start endpoint also accepts no browser parameters.

## Automatic-start safety

Automatic start is opt-in and user-local. The implementation:

- uses the fixed Windows task name `AI Control Center`;
- creates an `ONLOGON`, `LIMITED` task only when no task with that name exists;
- never overwrites an existing task and never uses `/F`;
- exposes no task command or filesystem path in Dashboard/API results;
- records a successful enablement as a structured audit event;
- fails closed when Windows Task Scheduler is unavailable.

The production launcher resolves its own repository root from `$PSScriptRoot`
before importing `backend.app`; it therefore does not depend on the Scheduled
Task caller's working directory. It writes at most 40 short lifecycle records
to `logs/startup.log`. Dashboard health exposes only the last allow-listed
startup codes (for example `REPOSITORY_ROOT_READY`, `PYTHON_UNAVAILABLE`,
`UVICORN_LAUNCHED`, or `UVICORN_EXITED`), never a command, absolute path,
environment value, exception text, prompt, or secret.

It does not install software, open a network listener beyond the existing
loopback server, elevate privileges, register a system-wide service, or start a
new server process from a browser request.

## M23 external validation

With the normal server already running, the human needs only the browser:

1. Open the Dashboard and confirm **HEALTHY**.
2. Click **Enable automatic startup** and confirm the card reports enabled.
3. Run a configured Day, click **Stop Day**, and confirm its stopped state and
   audit event.
4. Click **Run continuously** to resume the same trusted queue and confirm the
   Day state refreshes without PowerShell or API/DevTools interaction.
5. At the next Windows sign-in, open the Dashboard and confirm it is available
   on the normal loopback address without manually starting the server. If it
   is unavailable, inspect only the bounded `logs/startup.log` codes to identify
   the startup stage; no PowerShell diagnosis is needed.

The sign-in observation is the only external operational fact; no live Codex
or LocalLLM call is required for this milestone.
