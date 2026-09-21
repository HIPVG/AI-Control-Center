# AI-Control-Center

Local Windows-first control plane for AI-assisted engineering workflows.

The project separates planning, deterministic checks, Codex implementation, automated testing, independent evaluation, token governance, Git safety, and human approval.

## Start here

- Architecture: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- Agent rules: [AGENTS.md](AGENTS.md)
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

## Real Codex smoke

`config/runtime.yaml` defaults to `mode: mock`. To enable an explicitly requested real smoke, change it to `mode: real`, then start the application from a normal Windows PowerShell session (not from a nested Codex development sandbox):

```powershell
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8765
```

The real smoke is started only by the fixed endpoint below; it accepts no command or prompt input and writes only to its isolated smoke directory.

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8765/api/run/codex-smoke
```
