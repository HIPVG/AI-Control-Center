# AI-Control-Center

Local Windows-first control plane for AI-assisted engineering workflows.

The project separates planning, deterministic checks, Codex implementation, automated testing, independent evaluation, token governance, Git safety, and human approval.

## Start here

- Architecture: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- Agent rules: [AGENTS.md](AGENTS.md)
- Model / reasoning routing: [docs/MODEL_ROUTING.md](docs/MODEL_ROUTING.md)
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
