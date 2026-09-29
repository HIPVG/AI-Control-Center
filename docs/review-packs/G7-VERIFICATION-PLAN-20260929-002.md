# Review Pack: G7-VERIFICATION-PLAN-20260929-002

## Identity

- `PACK_ID`: `G7-VERIFICATION-PLAN-20260929-002`
- `GATE_TYPE`: `PLAN_REVIEW`
- `CURRENT_TASK`: `G7 verification planning — bounded resubmission`
- `REVIEWED_BRANCH`: `agent/g0-g5-baseline-publication`
- `REVIEWED_COMMIT`: `3b267223d507aefe113df671a9331be5c1fc0a13`
- `CREATED_AT`: `2026-09-29T03:21:05Z`
- `REVIEW_POLICY_CONTEXT`: `docs/WORKING_RULES.md` at
  `60c0fe7dcf8935fad4c6d3818256a94e95965501`

## Previous decision and requested decision

Pack `G7-VERIFICATION-PLAN-20260929-001` was rejected because GV-00 did not define
how to judge three standard G7 test-integrity areas. Determine whether revision 002
closes only that gap and is now sufficient to authorize GV-00 followed by the fixed
GV-01 deterministic validation set.

Do not authorize or request implementation changes, additional E2E, a Day, service,
browser, Watcher, model, credential or spending operation as part of this decision.

## Bounded correction

GV-00 now fixes a judgment table for:

1. whether each fixture input traverses the same production entrypoint/function path,
   with adapter bypass classified as lower-contract evidence and product path
   `NOT_EVALUABLE`;
2. whether expected answers or case-specific outcomes leak into production inputs,
   validators or prompt/context, while still checking deterministic-case overfitting
   when no AI prompt exists;
3. retention of exact command, start/end time, wall duration, exit code,
   stdout/stderr, warnings and failures, with token recorded as
   `NOT_APPLICABLE (no model invocation)` rather than zero for GV-01; and
4. retention of disconnect/failure causes, intermediate/terminal states, timestamps
   and absent downstream effects, while distinguishing fixture disconnect evidence
   from an unevaluated real external disconnect.

Each row now defines `NOT_APPLICABLE`, `NOT_EVALUABLE` and `FAIL` conditions and
requires path/test references and evidence locations in the GV-00 result.

## Unchanged scope

- Fixed implementation baseline remains
  `a30ed2303a85ff00ebbb5b0721bea4fe5c66ad0f`.
- A01-A06 mapping, fixed Python/Node sets, limits, roles and return paths are unchanged.
- No test, source, service or external actor was executed for this correction.
- Product UI/Day/telemetry E2E remains `INPUT_BLOCKED`.
- The first rejected pack and its decision remain preserved.

## Expected response boundary

If accepted, authorize only GV-00 and then GV-01 under the existing fixed commands,
30 ACTIVE_WORK minutes, two attempts per command and zero cost. GV-02 live operations
remain separately blocked. If rejected, identify one remaining concrete completeness
criterion and do not start validation.

## Artifact quality

- `ARTIFACT_QUALITY_CHECK`: `PASS`
- `SIMPLE_REPORT`: `yes`
- `ACTION_CLASS`: `VALIDATION`
- `MINIMUM_SUFFICIENT_ACTION`: Verify the four added GV-00 integrity judgments and
  either authorize GV-00/GV-01 or identify one concrete remaining plan defect.
- `WHY_NOT_BROADER`: The prior rejection identified only missing plan-level integrity
  judgments; no implementation or E2E work is required to resolve it.
- `REVIEWER_GUIDANCE`: Eliminate unnecessary overreach. Give only the
  minimum-sufficient, result-oriented instruction needed for the current objective.
  Do not recommend broader work merely because it is possible, cleaner, more general,
  more future-proof, or theoretically better. No speculative redesign, broad
  refactor, full-repository operation, extra validation, extra research, or
  higher-level optimization unless it is required to achieve the current DoD or
  remove the current blocker.

