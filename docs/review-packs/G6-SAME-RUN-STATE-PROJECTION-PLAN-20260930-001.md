# Review Pack: G6-SAME-RUN-STATE-PROJECTION-PLAN-20260930-001

## Identity

- `PACK_ID`: `G6-SAME-RUN-STATE-PROJECTION-PLAN-20260930-001`
- `GATE_TYPE`: `PLAN`
- `REVIEWED_BRANCH`: `agent/g0-g5-baseline-publication`
- `REVIEWED_COMMIT`: `575108e0a73d1d8ffdffb95724c0341e0e2ef108`
- `REVIEW_POLICY_CONTEXT`: `docs/WORKING_RULES.md` at
  `60c0fe7dcf8935fad4c6d3818256a94e95965501`
- `RETURN_SOURCE`: accepted `G7-PRODUCT-E2E-20260930-004`

## Decision requested

Review whether
`docs/ai-control-center-gates/2026-09/G6_SAME_RUN_STATE_PROJECTION_REPAIR_PLAN_2026-09.md`
is the minimum sufficient G6 repair plan for the accepted G7 return. This is a plan
review only; do not authorize implementation or live operations.

## Accepted cause and unchanged design

One admitted product Go reached a trusted Day 6 stop at
`EXTERNAL_ACTION_REQUIRED / REAL_MODE_REQUIRED`, while the durable RunRecord for the
same run remained `PREFLIGHT`. The existing guarded `project_day_state()` already
implements exact current-run, snapshot, Day, contract, Evidence and review checks;
production Go simply does not invoke it after the executor settles.

The plan therefore keeps G4/G5 semantics unchanged and does not treat
`REAL_MODE_REQUIRED` as part of this defect.

## Planned repair

One card, `SP-00`, adds a narrow post-execution projection callback to the existing
coordinator and wires it to the already-created
`RunProductComposition.execution.project_day_state` path. The executor result may
confirm identity but may not supply RunControl state. Blocked admission and executor
run-ID mismatch cannot invoke projection. Rejection or exception is reported as a
non-applied projection failure.

Focused proof covers:

- `REAL_MODE_REQUIRED` projected to the exact durable run and restart readback;
- one ordinary settled state with no duplicate executor effect;
- blocked admission, executor identity mismatch, snapshot/current-run mismatch and
  projection failure as non-applying paths;
- preservation of existing admission/preflight evidence and accepted composition
  regressions.

## Scope boundary

- This pack does not authorize implementation or test execution.
- Proposed later implementation limit: 30 ACTIVE_WORK minutes, at most two executions
  of each named focused command and 0 JPY.
- Do not start a service/browser, Go, real Day, model, real-mode/config change,
  Watcher, credential operation, G8 or product acceptance.
- A plan acceptance still requires a separate implementation decision by 広瀬剛.

## Quality and control

- `ARTIFACT_QUALITY_CHECK`: `PASS`
- `ACTION_CLASS`: `IMPLEMENTATION`
- `MINIMUM_SUFFICIENT_ACTION`: Confirm that SP-00 reuses the existing guarded
  projection at the correct post-execution boundary and has sufficient non-applying
  failure proof, or identify one concrete plan gap.
- `WHY_NOT_BROADER`: The accepted G7 return isolated one missing production call;
  redesigning state contracts, enabling real mode or rerunning the product cannot
  repair that wiring defect.
- `SIMPLE_REPORT`: `yes`
- `REVIEWER_GUIDANCE`: Eliminate unnecessary overreach. Give only the
  minimum-sufficient, result-oriented instruction needed for the current objective.
  Do not recommend broader work merely because it is possible, cleaner, more general,
  more future-proof, or theoretically better. No speculative redesign, broad
  refactor, full-repository operation, extra validation, extra research, or
  higher-level optimization unless it is required to achieve the current DoD or
  remove the current blocker.

## Minimum next action

If accepted, record plan acceptance and stop for separate human implementation
authority. Do not begin SP-00 from Reviewer plan acceptance alone.
