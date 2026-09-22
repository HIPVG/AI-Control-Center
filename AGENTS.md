# AI Control Center agent instructions

## Required startup sequence

Before planning or modifying code, read in order:

1. `docs/WORKING_RULES.md`
2. `docs/CURRENT_WORK.md`
3. The authoritative scenario/runbook named by `CURRENT_WORK.md`
4. The current Git and working-tree state

`WORKING_RULES.md` is the canonical operational rule set. `CURRENT_WORK.md`
defines the active objective, Definition of Done (DoD), and stop condition. The
scenario/runbook supplies domain-specific intent. `docs/ARCHITECTURE.md` is the
structural baseline unless `CURRENT_WORK.md` explicitly authorizes a structural
change. Historical documents cannot override those sources.

## Project constraints

AI Control Center is a Windows-first local orchestration dashboard for
deterministic checks, bounded Codex roles, tests, repair/replan, Git inspection,
and token monitoring. Use Python 3.12, FastAPI, Uvicorn, Pydantic, and
HTML/CSS/vanilla JavaScript; default binding is `127.0.0.1`. Do not add React,
Node build tooling, Docker, Redis, or other infrastructure without explicit
authorization. Keep initial persistence as JSON behind an interface.

Critical scope, Git, budget, retry, and state protections remain enforced in
code. Codex may act in bounded Architect, Builder, Reviewer, or configured
Evaluator roles; responsibilities and structured contracts must remain
separate.
