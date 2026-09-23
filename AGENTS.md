# AI Control Center agent instructions

## Required startup sequence

Before planning, modifying code, resuming a Day, or acting on a reviewer response:

1. Read the **complete latest human/reviewer message**.
2. Read the current-branch `docs/WORKING_RULES.md` in full. Do not rely on a cached copy.
3. Read `docs/CURRENT_WORK.md`.
4. Read the authoritative scenario/runbook named by `CURRENT_WORK.md`.
5. Read relevant execution/engineering history and persisted Day state.
6. Inspect current Git/working-tree state.

`docs/WORKING_RULES.md` is the single canonical operational policy. Historical
zero-touch/autonomous documents are subordinate reference material when they conflict.
`CURRENT_WORK.md` defines the active objective, DoD, and stop condition. The runbook
supplies domain intent; `docs/ARCHITECTURE.md` is the structural baseline unless the
active work explicitly authorizes a change.

Before any reviewer-facing report, re-check the current policy commit and include the
required `REVIEW_POLICY_CONTEXT`. If the policy changed since the prior report, read
the new version before continuing.

After a blocking `DECISION_REQUEST` or `COMPLETION_REPORT`, do not act on the first
line or on an old `NEXT_ACTION`; read and apply the complete latest reviewer response.

## Reporting and reviewer transport

Follow `docs/WORKING_RULES.md` exactly. In particular:

- `PROGRESS_UPDATE` is non-blocking and is emitted about every 5 minutes during active work.
- `DECISION_REQUEST` and `COMPLETION_REPORT` are blocking.
- Blocking reports require successful delivery to the ChatGPT reviewer directly or
  through `HIPVG/AI-Control-Center-Review-Bridge`; user-facing display alone is not delivery.
- If both blocking-report channels fail, use the canonical 2-minute retry sequence
  (initial attempt plus 2 retries) before declaring `DELIVERY_FAILED`.
- Composer-draft protection never excuses reviewer delivery.
- Completion requires `ARTIFACT_QUALITY_CHECK: PASS` and reviewer clearance before the next Day.

## Project constraints

AI Control Center is a Windows-first local orchestration dashboard for deterministic
checks, bounded Codex roles, tests, repair/replan, Git inspection, and token
monitoring. Use Python 3.12, FastAPI, Uvicorn, Pydantic, and HTML/CSS/vanilla
JavaScript; default binding is `127.0.0.1`. Do not add React, Node build tooling,
Docker, Redis, or other infrastructure without explicit authorization. Keep initial
persistence as JSON behind an interface.

Critical scope, Git, budget, retry, state, command, and evidence protections remain
deterministic and auditable. Codex roles and structured contracts remain separate.