# G7 SP-00 product revalidation — 2026-09-30

## Scope and fixed inputs

- Action class: `VALIDATION`
- Authority: `AUTH-G7-SP00-PRODUCT-REVALIDATION-20260930-001`
- AI-Control-Center implementation: `3e82626faebab8e9722939b92267deb51075d93b`
- Isolated product worktree:
  `C:/Users/広瀬剛/.codex/worktrees/g7-sp00-revalidation/AI-Control-Center`
- Clean LocalLLM-Lab baseline:
  `e33b0a410fb8647711f02ae4e6e0b66472e6eff0`
- Day: 6
- Limits: 30 ACTIVE_WORK minutes, one Go, 0 JPY
- Actual use: one Go, no model invocation, 0 JPY
- Reviewer Bus: disabled by `AI_CONTROL_CENTER_DISABLE_REVIEWER_BUS=1`

The original dirty worktrees were not reset, cleaned, restored, staged or modified.
The clean LocalLLM-Lab validation worktree had an empty status before and after the
run. The loopback service ran on `127.0.0.1:8021` and was stopped after readback.

## Current-build authority and prerequisite facts

The validation used a new exact Grant rather than reusing the prior build's Grant:

- decision/grant ID:
  `AUTH-G7-SP00-PRODUCT-REVALIDATION-20260930-001`;
- authority record SHA-256:
  `fb3fe1ca830d63dd2bec26c456556f226c956961d098bd6884016e7644c30455`;
- prerequisite observation:
  `G7-SP00-PRODUCT-REVALIDATION-PREREQUISITE-20260930-001`;
- prerequisite observation hash:
  `6ad2dc9fcfe6da479b498d290ec25a9a1f7abcc2d74ae1195ae9b423ea913c4d`;
- LocalLLM Git fingerprint:
  `c4846dcb97261e309426d80bcfe7be02021a409ea98816dd3e1877233de82f07`.

The server-derived preflight fact for
`run-7ea73560dbac4d27aebaad042022d61a` recorded exact Grant and prerequisite
matches. Admission was `ADMISSIBLE`.

## One browser Go and asynchronous settlement

Chrome selected Day 6 without creating a run and issued exactly one Go. The access
log contains one `POST /api/local-llm/day/go` with HTTP 200.

The persisted history version captured the required early state:

- run ID: `run-7ea73560dbac4d27aebaad042022d61a`;
- state: `PREFLIGHT`;
- updated at: `2026-09-30T08:49:58.632513Z`;
- history file SHA-256:
  `c7c1f87608d6d85e2581b4bf435fca85fdec84fca4b2fa9750da4c8834847960`.

After the asynchronous worker stopped, the dashboard, Day status API, run API and
durable current RunRecord all showed the same run at:

- state: `EXTERNAL_ACTION_REQUIRED`;
- issue classification: `EXTERNAL_AUTHORITY_REQUIRED`;
- blocker/result: `REAL_MODE_REQUIRED`;
- RunRecord updated at: `2026-09-30T08:49:59.148653Z`;
- Day snapshot updated at: `2026-09-30T08:49:59.146648Z`;
- current RunRecord SHA-256:
  `fef6604fab03907ed2d71c8dacc9aa29d74acd02a49f3140e0a3b1eeefed8551`;
- preflight fact SHA-256:
  `c5bd6f0fdcdda3b7735295cd706be4df73309ef9f5a192fa0e092eaf844896d3`.

This closes the previously accepted A05 same-run projection defect with live
service/browser evidence. The early `PREFLIGHT` record remains distinct evidence and
was not overwritten or misreported as the final state.

## G7 classification and stop

| Requirement | Result |
|---|---|
| A01 selected-Day Go/admission | Product `PASS`: exact current-build facts admitted one Day 6 Go on the clean baseline. |
| A02 plan, Evidence and judgment | `INPUT_BLOCKED`: mock runtime stopped before real Codex execution and produced no Day Evidence. |
| A03 repair and revalidation | `NOT_EVALUABLE`: no engineering result existed before the runtime-authority stop. |
| A04 current review/stop/recovery | `NOT_EVALUABLE`: Reviewer Bus remained intentionally disabled. |
| A05 actual-state dashboard/readback | Product `PASS`: dashboard, Day API, run API and durable RunRecord converged on the same run and blocker after async settlement. |
| A06 outcome/relay/cost | Partial product `PASS` for the preserved blocker and 0 JPY; execution telemetry is absent because no model ran. |

G7 remains stopped at the separate `REAL_MODE_REQUIRED` authority boundary. This
record does not authorize real mode, a model, another Go, repair, Watcher, G8 or
product acceptance.

## Preserved evidence

- Service stdout SHA-256:
  `37df220ff78ca619b2ea7dc243bd7dae1195ac76d0165c2a5ddedda0c38b8a23`.
- Service stderr SHA-256:
  `92e7f05908e0faf1c513afb37ce06c03c3f3ed57bad0f6b30173d3b3b3fc0b90`.
- stderr contains only normal Uvicorn startup lines.
- Port 8021 stopped responding after the exact service process was stopped.
- No source repair, real-mode change, model invocation, Watcher action or second Go
  occurred.

`ARTIFACT_QUALITY_CHECK: PASS`
