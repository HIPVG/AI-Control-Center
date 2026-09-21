# AI-Control-Center

Local Windows-first control plane for AI-assisted engineering workflows.

The default runtime is **Codex Core**: a read-only Codex Architect selects a
trusted configured task, Codex Builder works only after deterministic failure
triage, and an optional read-only Codex First Reviewer handles bounded,
inconclusive repair evidence. Python remains authoritative for deterministic
facts, state transitions, budgets, retries, Scope Guard, Git Guard, and task
authority. OpenAI providers are optional independent providers, never a normal
startup requirement.

## Start here

- Architecture: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- Agent rules: [AGENTS.md](AGENTS.md)
- Model / reasoning routing: [docs/MODEL_ROUTING.md](docs/MODEL_ROUTING.md)
- Autonomous Day operation: [docs/AUTONOMOUS_DAY.md](docs/AUTONOMOUS_DAY.md)
- Daily Dashboard operation: [docs/DAILY_OPERATION.md](docs/DAILY_OPERATION.md)
- Initial Codex implementation prompt: [prompts/CODEX_BOOTSTRAP.md](prompts/CODEX_BOOTSTRAP.md)

## Core operating principle

```text
Codex Core           = Architect, Builder, First Review
Python / tests        = Determine objective facts and enforce authority
OpenAI / other providers = Optional independent evaluation
Git                   = Record
Human                 = Decide exceptions and final approval
```

The first implementation milestone is v0.1: a local FastAPI + HTML/JavaScript dashboard with mock orchestration, state management, token accounting, progress display, and safety guards.

## Local launch and Day validation

Use the project launchers on `127.0.0.1:8000`:

```powershell
& C:\AI-Control-Center\scripts\start_dev.ps1
```

For a non-reloading production-style server, use `& C:\AI-Control-Center\scripts\start.ps1`.
The default Codex-Core Day plan can then be run one trusted task at a time. In
the tracked mock runtime this safely simulates the Codex Architect; production
Codex validation uses the same plan with `runtime.local.yaml` set to `real`:

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/day/start/week1-day3-local-llm-v3-codex-core?mode=single-step | ConvertTo-Json -Depth 20
```

## Dashboard v2

Opening `http://127.0.0.1:8000` shows the live Autonomous Day dashboard. It
defaults to `week1-day3-local-llm-v3-codex-core` and can start only a
configured plan. Use **Run continuously** only for a plan that advertises
continuous support; a matching paused Day resumes its remaining trusted queue.
The dashboard reads trusted Day state to display
the queue, `PAUSED` progress, ModelRouter selection, Codex role counts,
gross/cached/uncached Architect tokens, Human Review, and the audit timeline.
It never accepts browser-supplied commands, prompts, paths, budgets, or task
definitions.

## Daily operation

The Dashboard is the normal control surface for start, continuous resume,
stop, and server health. Its **Enable automatic startup** control optionally
registers a fixed, user-local Windows logon task; it accepts no browser-supplied
command or path and never overwrites an existing task. See
[daily operation](docs/DAILY_OPERATION.md) for the explicit safety boundary and
browser-only validation steps.

`config/model_profiles.yaml` defines the logical reasoning profiles and their
concrete provider mappings. Codex Core maps simple/normal/complex work to
economical/standard/deep (Low/Medium/High); the Router, not a provider, selects
the profile. OpenAI remains opt-in through `OPENAI_API_KEY`; no API key or
network call is needed for normal Codex-Core validation.

## Local runtime overrides

Tracked `config/runtime.yaml` and `config/budget.yaml` are safe defaults.
Ordinary local operation reads optional ignored overrides afterwards:
`config/runtime.local.yaml` and `config/budget.local.yaml`. Copy the matching
`.example.yaml` file to create a local override; local values must never be
committed.

## Real Codex smoke

`config/runtime.yaml` defaults to `mode: mock`. To enable an explicitly requested real smoke, change it to `mode: real`, then start the application from a normal Windows PowerShell session (not from a nested Codex development sandbox):

```powershell
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8765
```

The real smoke is started only by the fixed endpoint below; it accepts no command or prompt input and writes only to its isolated smoke directory.

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8765/api/run/codex-smoke
```

## Configured LocalLLM-Lab smoke

`config/projects.yaml` contains the only external project target accepted by this workflow: `local_llm_lab` at `C:\LocalLLM-Lab`. With `config/runtime.yaml` set to `mode: real`, start Uvicorn as a normal Windows user (not inside a Codex development task) and call the fixed endpoint:

```powershell
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8765
```

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8765/api/run/project-smoke/local_llm_lab
```

The endpoint captures existing Git changes as a baseline, creates a unique `.ai-control-center-smoke/<run_id>/status.txt` fixture, and permits Codex to change only that fixture from `FAIL` to `PASS`.

## Configured real task execution

Configured tasks are listed without command internals at `GET /api/tasks/configured`. The first task, `PC-001-A`, creates an isolated local Git worktree under Control Center state and runs only its configured deterministic dry-run check. It never writes to the user's LocalLLM-Lab checkout.

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8765/api/run/task/PC-001-A | ConvertTo-Json -Depth 15
```
