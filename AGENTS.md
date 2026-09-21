# AGENTS.md

## Mission

Build and maintain AI Control Center according to `docs/ARCHITECTURE.md`.

The project is a Windows-first local orchestration dashboard for deterministic checks, Codex execution, automated tests, bounded evaluation/repair loops, Git inspection, and token monitoring.

## Mandatory Design Rules

1. Deterministic first. Do not call Codex when Python, pytest, configuration validation, or deterministic rules can resolve the task.
2. Codex is a Builder, not a Planner or final Evaluator.
3. Architect, Builder, Evaluator, and Human responsibilities must remain separate.
4. Agent-to-agent communication must use structured models/schemas rather than large free-form conversational histories.
5. Keep context minimal. Prefer targeted file reads, bounded log excerpts, relevant diffs, and explicit acceptance criteria.
6. Critical rules must be enforced in code, not only in prompts.
7. Never silently exceed token or retry budgets.
8. Prefer small, reviewable diffs over broad refactors.

## Technology

Primary runtime:
- Python 3.12
- Windows 11
- PowerShell 7

Backend:
- FastAPI
- Uvicorn
- Pydantic

Frontend:
- HTML
- CSS
- Vanilla JavaScript

Do not add React, Node.js build tooling, Docker, Redis, or other infrastructure unless a later requirement explicitly calls for it.

Initial persistence should be JSON behind an interface so it can be replaced with SQLite later.

Default server binding must be `127.0.0.1`.

## Safety

Never:
- push directly to `main`
- use destructive Git operations such as `git reset --hard`, `git clean -fd`, or `git branch -D`
- modify files outside the WorkOrder allowed-file scope
- weaken or delete tests merely to make a task pass
- change plans, schemas, or acceptance criteria without explicit authorization
- delete user or benchmark data
- commit secrets or API credentials

Always:
- make the smallest change that satisfies the task
- run specified tests
- inspect the final diff
- report changed files
- preserve auditability
- escalate to HUMAN_REVIEW when scope, safety, or retry limits are exceeded

## Repository Guidance

Authoritative architecture:
- `docs/ARCHITECTURE.md`

Autonomous development reasoning policy:
- `docs/DEVELOPMENT_REASONING_POLICY.md`

Bootstrap implementation instruction:
- `prompts/CODEX_BOOTSTRAP.md`

If implementation details conflict with the architecture, preserve the architecture unless the task explicitly updates it.

Codex should select its development reasoning level according to `docs/DEVELOPMENT_REASONING_POLICY.md` rather than asking the human for routine Low/Medium/High choices.

Keep this file concise. Put detailed design decisions in `docs/`, not here.
