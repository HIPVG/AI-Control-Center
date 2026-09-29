# Review Pack: G7-VERIFICATION-PLAN-20260929-001

## Identity

- `PACK_ID`: `G7-VERIFICATION-PLAN-20260929-001`
- `GATE_TYPE`: `PLAN_REVIEW`
- `CURRENT_TASK`: `G7 verification planning`
- `REVIEWED_BRANCH`: `agent/g0-g5-baseline-publication`
- `REVIEWED_COMMIT`: `142c97c1c5cb6012dd6aa79c0aaa98ede5fdc142`
- `CREATED_AT`: `2026-09-29T03:13:34Z`
- `REVIEW_POLICY_CONTEXT`: `docs/WORKING_RULES.md` at
  `60c0fe7dcf8935fad4c6d3818256a94e95965501`

## Decision requested

Determine whether
`docs/ai-control-center-gates/2026-09/G7_AI_CONTROL_CENTER_VERIFICATION_PLAN_2026-09.md`
is a sufficient, bounded G7 plan for the accepted G6 implementation baseline.
Specifically verify that it covers the standard's focused acceptance tests, related
regression, important failure injection, independent readback and test-integrity
checks without converting unavailable product E2E into a fixture pass.

## Fixed inputs and scope

- Human G7-start authority: `AUTH-G7-START-20260929-001`.
- Accepted G6 implementation baseline:
  `a30ed2303a85ff00ebbb5b0721bea4fe5c66ad0f`.
- G2 acceptance conditions: A01 through A06.
- Planned cards: GV-00 baseline/test integrity, GV-01 deterministic regression,
  GV-02 real boundaries, GV-03 traceability and G7 result.
- Verification role: ChatGPT is separate from implementation actor CODEX, while its
  review/verification dual role is not represented as independence between those two
  review roles.
- Limits: 30 ACTIVE_WORK minutes, each fixed command at most twice, cost 0 JPY.

## Evidence boundaries

The plan preserves three proof layers:

1. WC-01 through WC-10 deterministic contract/model/API/DOM fixtures;
2. the fixed VC-11 actual Reviewer/Watcher actor trace; and
3. product E2E requiring live service/browser, selected-Day and measured telemetry
   conditions.

The third layer remains `INPUT_BLOCKED` or `NOT_EVALUABLE` until its concrete inputs
and authority are fixed. The plan does not call the first two layers product E2E and
does not authorize a Day, service/browser operation, model, credential change or
spending.

## Test-integrity controls

- The plan is reviewed before executing the G7 test set.
- G7 does not edit implementation code, acceptance expectations or existing evidence.
- Failures are retained and returned to G6 or G4; they are not repaired inside G7.
- G6 rejected packs remain failed history and are not counted as passing evidence.
- Commit/path/hash, test history, exclusions, expected failures and mock/stub use are
  checked before execution.
- Result counts or exit code alone are not acceptance evidence.

## Expected response boundary

If accepted, authorize only GV-00 and then the fixed GV-01 deterministic commands in
dependency order. GV-02 read-only VC-11 evidence inspection may follow, but any live
service/browser, new delivery, Watcher restart, product Go or Day operation remains
blocked until separately authorized at that exact boundary. Do not authorize G8 or
product acceptance.

If rejected, identify the one concrete missing G7 requirement or unsafe expansion and
return the plan for bounded correction without running tests.

## Artifact quality

- `ARTIFACT_QUALITY_CHECK`: `PASS`
- Plan maps every A01-A06 requirement to a verification card or explicit unevaluated
  product boundary.
- Roles, lost independence, mechanical substitute, budgets, stop and return paths are
  explicit.
- Template T36/T37 fields are integrated rather than copied into additional forms.
- Existing unrelated dirty work and `main` remain outside the reviewed commit.

## Required review metadata

- `SIMPLE_REPORT`: `yes`
- `ACTION_CLASS`: `VALIDATION`
- `MINIMUM_SUFFICIENT_ACTION`: Review the fixed plan and either authorize GV-00/GV-01
  or name one concrete plan defect.
- `WHY_NOT_BROADER`: G7 execution should not begin until its criteria are fixed, and
  product E2E lacks separately fixed live inputs and authority.
- `REVIEWER_GUIDANCE`: Eliminate unnecessary overreach. Give only the
  minimum-sufficient, result-oriented instruction needed for the current objective.
  Do not recommend broader work merely because it is possible, cleaner, more general,
  more future-proof, or theoretically better. No speculative redesign, broad
  refactor, full-repository operation, extra validation, extra research, or
  higher-level optimization unless it is required to achieve the current DoD or
  remove the current blocker.

