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

- Use the validated event-driven reviewer bus at
  `HIPVG/AI-Control-Center-Review-Bridge` PR #1. Normal reviewer transport does not
  use the ChatGPT composer.
- Keep exactly one reviewer report outstanding. Every report has a unique
  `REPORT_ID`; apply only a response whose `IN_REPLY_TO` exactly matches it.
- A local deterministic fetch loop checks PR #1 about every 2 minutes for the matching
  reviewer response. The 2-minute cadence is transport/fetch cadence, not report cadence.
- `PROGRESS_UPDATE` is normally due after **10 minutes of ACTIVE_WORK**. Report at the
  next safe boundary, allow at most +3 active minutes to finish a bounded subtask, and
  never exceed 15 active minutes without progress reporting.
- Reviewer/report waiting time is excluded from the 30-minute ACTIVE_WORK budget.
  Reset the 10-minute progress counter after the full matching reviewer response is
  applied.
- `DECISION_REQUEST` and `COMPLETION_REPORT` are event-driven and blocking.
- Completion requires `ARTIFACT_QUALITY_CHECK: PASS`; do not start the next Day until
  the matching reviewer response accepts completion and authorizes the boundary.
- Every report must include
  `ACTION_CLASS: IMPLEMENTATION|VALIDATION|DIAGNOSIS|AUTHORITY`,
  `MINIMUM_SUFFICIENT_ACTION`, `WHY_NOT_BROADER`, and the mandatory anti-overreach
  `REVIEWER_GUIDANCE`.
- Do not turn VALIDATION into more IMPLEMENTATION, a diagnostic checkpoint into a stop,
  or history/reporting bookkeeping into self-generating engineering work.
- Human involvement is exceptional and must not be used as a routine copy/paste relay.
  Use it only for genuine authority/product-direction boundaries or an actual reviewer
  transport failure.

## Project constraints

AI Control Center is a Windows-first local orchestration dashboard for deterministic
checks, bounded Codex roles, tests, repair/replan, Git inspection, and token
monitoring. Use Python 3.12, FastAPI, Uvicorn, Pydantic, and HTML/CSS/vanilla
JavaScript; default binding is `127.0.0.1`. Do not add React, Node build tooling,
Docker, Redis, or other infrastructure without explicit authorization. Keep initial
persistence as JSON behind an interface.

Critical scope, Git, budget, retry, state, command, and evidence protections remain
deterministic and auditable. Codex roles and structured contracts remain separate.