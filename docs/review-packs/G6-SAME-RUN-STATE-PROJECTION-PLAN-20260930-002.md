# Review Pack: G6-SAME-RUN-STATE-PROJECTION-PLAN-20260930-002

## Identity

- `PACK_ID`: `G6-SAME-RUN-STATE-PROJECTION-PLAN-20260930-002`
- `GATE_TYPE`: `PLAN`
- `REVIEWED_BRANCH`: `agent/g0-g5-baseline-publication`
- `REVIEWED_COMMIT`: `c6b81eb779350f9f2ed1be47bcc6da1a23c3aa0b`
- `REVIEW_POLICY_CONTEXT`: `docs/WORKING_RULES.md` at
  `60c0fe7dcf8935fad4c6d3818256a94e95965501`
- `SUPERSEDES_REJECTED_PACK`: `G6-SAME-RUN-STATE-PROJECTION-PLAN-20260930-001`

## Decision requested

Review the revised
`docs/ai-control-center-gates/2026-09/G6_SAME_RUN_STATE_PROJECTION_REPAIR_PLAN_2026-09.md`.
Determine whether revision 002 corrects the rejected invocation timing while staying
the minimum sufficient G6 plan. This is a plan review only.

## Rejection addressed

Revision 001 projected after the default executor returned. Fixed-code inspection
shows that `LocalLLMDayProgram.start()` launches `_execute` on a daemon thread and
returns immediately, so the old boundary could observe `PREFLIGHT` before the Day
worker later persisted `REAL_MODE_REQUIRED`.

Revision 002 removes coordinator/executor-return projection. SP-00 instead places one
notification at the Day worker settlement boundary:

1. the worker captures the expected run ID when created;
2. `_execute` reaches a non-active state;
3. the final Day snapshot save succeeds;
4. one immutable same-run notification is emitted for that execution episode;
5. production routes it through the existing guarded `project_day_state()` path;
6. later readback, not the initial asynchronous Go response, exposes the projection.

## Required deterministic proof

- A controlled worker fixture proves `start()` returns before terminal state, the
  terminal save precedes notification, and exactly one notification is emitted.
- `REAL_MODE_REQUIRED` becomes the same durable RunRecord state/blocker only after
  settlement notification.
- Blocked admission, captured-run mismatch, snapshot/current-run mismatch, save
  failure, projection rejection and projection exception remain non-applying.
- The executor is not repeated, notification creates no external effect, and restart
  readback preserves the same projected run.

## Scope boundary

- Do not authorize implementation or test execution from this review.
- Do not add polling, another watcher or a second state machine.
- Do not start a service/browser, Go, real Day, model, real-mode/config change,
  Watcher, credential operation, G8 or product acceptance.
- Plan acceptance still requires a separate implementation decision by 広瀬剛.

## Quality and control

- `ARTIFACT_QUALITY_CHECK`: `PASS`
- `ACTION_CLASS`: `IMPLEMENTATION`
- `MINIMUM_SUFFICIENT_ACTION`: Confirm that post-save worker settlement is the
  correct one-time same-run projection boundary and that the ordering fixture proves
  it, or identify one remaining concrete timing/identity gap.
- `WHY_NOT_BROADER`: The rejection identified only the invocation time. Existing
  state semantics, guarded projection, real-runtime authority and product scope do
  not need to change.
- `SIMPLE_REPORT`: `yes`
- `REVIEWER_GUIDANCE`: Eliminate unnecessary overreach. Give only the
  minimum-sufficient, result-oriented instruction needed for the current objective.
  Do not recommend broader work merely because it is possible, cleaner, more general,
  more future-proof, or theoretically better. No speculative redesign, broad
  refactor, full-repository operation, extra validation, extra research, or
  higher-level optimization unless it is required to achieve the current DoD or
  remove the current blocker.

## Minimum next action

If accepted, record revision 002 plan acceptance and stop for separate human
implementation authority. Do not begin SP-00 from Reviewer plan acceptance alone.
