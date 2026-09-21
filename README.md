# AI-Control-Center

Local Windows-first control plane for AI-assisted engineering workflows.

The project separates planning, deterministic checks, Codex implementation, automated testing, independent evaluation, token governance, Git safety, and human approval.

## Start here

- Architecture: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- Agent rules: [AGENTS.md](AGENTS.md)
- Model / reasoning routing: [docs/MODEL_ROUTING.md](docs/MODEL_ROUTING.md)
- Autonomous Day operation: [docs/AUTONOMOUS_DAY.md](docs/AUTONOMOUS_DAY.md)
- Initial Codex implementation prompt: [prompts/CODEX_BOOTSTRAP.md](prompts/CODEX_BOOTSTRAP.md)

## Core operating principle

```text
ChatGPT / Architect = Think and structure
Codex               = Build
Python / tests      = Determine objective facts
Git                  = Record
Human                = Decide
```

The first implementation milestone is v0.1: a local FastAPI + HTML/JavaScript dashboard with mock orchestration, state management, token accounting, progress display, and safety guards.

## Local launch and Day validation

Use the project launchers on `127.0.0.1:8000`:

```powershell
& C:\AI-Control-Center\scripts\start_dev.ps1
```

For a non-reloading production-style server, use `& C:\AI-Control-Center\scripts\start.ps1`.
The mock Day plan can then be run one deterministic task at a time:

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/day/start/week1-day3-local-llm-v2?mode=single-step | ConvertTo-Json -Depth 20
```

`config/model_profiles.yaml` defines the logical reasoning profiles. Real
providers remain opt-in through `OPENAI_API_KEY` and explicit
`config/orchestration.yaml` model configuration; no credential or network call
is made during normal mock validation.

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
