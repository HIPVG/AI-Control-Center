# G7 limited product revalidation — 2026-09-30

## Scope and fixed inputs

- Action class: `VALIDATION`
- Authority: `AUTH-G7-LIMITED-PRODUCT-REVALIDATION-20260930-001`
- AI-Control-Center build: `7b849803de140454b9f67beca98c52132a7bdb6f`
- Isolated product worktree:
  `C:/Users/広瀬剛/.codex/worktrees/g7-authority-revalidation/AI-Control-Center`
- Clean LocalLLM-Lab baseline:
  `e33b0a410fb8647711f02ae4e6e0b66472e6eff0`
- Day: 6
- Limits: 30 ACTIVE_WORK minutes, at most two Go attempts, 0 JPY
- Actual use: one Go attempt, no model invocation, 0 JPY
- Reviewer Bus: disabled by `AI_CONTROL_CENTER_DISABLE_REVIEWER_BUS=1`

The original dirty worktrees were not reset, cleaned, restored, staged or changed.
The previously created clean LocalLLM-Lab validation worktree was verified at the
approved commit with an empty status before and after the run.

## Current-build authority and prerequisite facts

A new Grant was created from the direct human decision instead of reusing the stale
historical Grant. It exactly matched Day 6, allowed effect, current product commit,
contract/policy/config/Git fingerprints, clean LocalLLM commit and requested limits.
A fresh server-side prerequisite observation confirmed the three declared Day 6
paths in the clean checkout.

The resulting same-run preflight fact for
`run-b229e3cee8a347b5bd621b799b146cda` recorded:

- `effective_permission: true` / `AUTHORITY_GRANT_EXACT_MATCH`;
- `external_prerequisite: true` / `PREREQUISITE_OBSERVATION_EXACT_MATCH`;
- Grant and decision ID
  `AUTH-G7-LIMITED-PRODUCT-REVALIDATION-20260930-001`;
- authority record SHA-256
  `7f55671a34e66f37602b1c693c29828fe91f4f91956578ff184378192e70aad6`;
- prerequisite observation source hash
  `378e8af4ffdedb82161af6ec5a0efd5a0fc5ff7097c3cc710866f97b9e54728c`.

The product API classified admission as `ADMISSIBLE`. This closes the prior
`EFFECTIVE_PERMISSION_UNKNOWN` blocker for the current build.

## One browser Go and observed stop

Chrome selected Day 6 without creating a run, then issued exactly one product Go.
The access log contains one `POST /api/local-llm/day/go` with HTTP 200. The Day
controller traversed `PREFLIGHT`, contract load, inventory, validation, diagnosis and
normal Day work selection, then stopped at:

- Day state: `EXTERNAL_ACTION_REQUIRED`;
- classification: `EXTERNAL_AUTHORITY_REQUIRED`;
- reason: `REAL_MODE_REQUIRED`;
- message: `The configured runtime does not authorize real Codex execution.`;
- fixed configuration: `config/runtime.yaml` has `codex.mode: mock`.

No Day evidence, source change, Codex execution, model invocation, telemetry, token
use or cost was produced. A second Go was not attempted and the runtime configuration
was not changed because the validation authority required stopping at the first
blocker and did not grant real-runtime execution authority.

## Product-state consistency finding

The main Day panel correctly showed `EXTERNAL_ACTION_REQUIRED`, but the read-only run
projection for the same run remained `PREFLIGHT`, `ADMISSIBLE`, with no blocker and
unknown runtime. The persisted RunRecord SHA-256 is
`a59447375cb00071c7c0fb53b8bed54f0f41fe3eb90927b0f050d176fb152023`;
the persisted preflight fact SHA-256 is
`5029d2d33acab87d7fff659bb97f5a7d063443535a1aaba83d51390f858411c9`.

Read-only call-path inspection explains the mismatch: production
`RunCoordinator.go()` returns the executor result but does not call
`RunExecutionComposition.project_day_state()` after the default
`_execute_composed_local_llm_day()` changes the Day snapshot. This is a product
composition gap, not a missing authority fact.

## G7 classification and stop

| Requirement | Result |
|---|---|
| A01 selected-Day Go/admission | Partial product `PASS`: current-build authority and prerequisite facts admitted one same-run Go. |
| A02 plan, Evidence and judgment | `INPUT_BLOCKED`: real Codex runtime was not authorized/configured; no Day evidence was produced. |
| A03 repair and revalidation | `NOT_EVALUABLE`: validation stopped before an engineering result existed. |
| A04 current review/stop/recovery | `NOT_EVALUABLE`: Reviewer Bus remained intentionally disabled. |
| A05 actual-state dashboard/readback | `FAIL`: Day state and durable run projection disagree after the executor returns. |
| A06 outcome/relay/cost | Partial product `PASS` only for preserved blocker and 0 JPY; no execution telemetry exists. |

Proposed G7 result: `RETURN` to the smallest G6 correction that projects the default
executor's same-run Day state into the durable RunRecord, while separately retaining
`REAL_MODE_REQUIRED` as a genuine runtime-authority boundary. Do not enable real mode,
retry Go, implement the correction, start G8 or claim product acceptance from this
record.

## Preserved evidence

- Service stdout SHA-256:
  `e4d9b59525e4adfd67173fd913213fb8f19a4683401a0c3a664183f84776fa2d`
- Service stderr SHA-256:
  `0c655b6b307249140e5278cbdafe8cb6ae6196e56e97f3e645394348cd2246df`
- Prerequisite file SHA-256:
  `e09f5fd92d18e0208e8224cc5b9bf6962e5c2d660c0798b42e03c3dd4d1c2339`
- The loopback service was stopped and port 8020 no longer responded.
- Browser evidence showed Day 6 selection without action, then the final
  `EXTERNAL_ACTION_REQUIRED / REAL_MODE_REQUIRED` state and the divergent
  `PREFLIGHT` run panel.

`ARTIFACT_QUALITY_CHECK: PASS`
