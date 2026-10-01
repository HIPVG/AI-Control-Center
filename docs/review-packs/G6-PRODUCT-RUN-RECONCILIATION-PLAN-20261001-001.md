# Review Pack: G6-PRODUCT-RUN-RECONCILIATION-PLAN-20261001-001

## Identity

- `PACK_ID`: `G6-PRODUCT-RUN-RECONCILIATION-PLAN-20261001-001`
- `GATE_TYPE`: `PLAN`
- `REVIEWED_BRANCH`: `agent/g0-g5-baseline-publication`
- `REVIEWED_COMMIT`: `73cfcafd85f285cdc5db6afba5d322d48af7d304`
- `CREATED_AT`: `2026-10-01T00:43:04Z`
- `REVIEW_POLICY_CONTEXT`: `docs/WORKING_RULES.md` at
  `60c0fe7dcf8935fad4c6d3818256a94e95965501`
- `RETURN_SOURCE`: accepted `G7-PRODUCT-E2E-20261001-007`

## Decision requested

Review whether
`docs/ai-control-center-gates/2026-10/G6_PRODUCT_RUN_RECONCILIATION_REPAIR_PLAN_2026-10.md`
is the minimum sufficient G6 repair plan for the three accepted real-product
discrepancies. This is a plan review only. Do not authorize implementation, tests,
another Go, model execution, service/browser work, Watcher, G8 or product acceptance.

## Accepted facts

For product run `run-8b9fb7cac4c948098af3e9aa7dfeaf8d`:

- one admitted Go and one actual Codex execution completed;
- the Day persisted four satisfied criteria and `COMPLETE`;
- the durable RunRecord remained `PREFLIGHT`;
- all five completion Evidence Records had null `run_id` and `criterion_id`;
- actual attempt/token/budget-warning facts existed in Day/task state while product
  run telemetry was null; and
- measured run cost availability was not established.

The Reviewer accepted A01 `PASS`, A02/A05/A06 `FAIL`, A03/A04-current
`NOT_EVALUABLE`, and a G7 return without another Day 6 reproduction run.

## Proposed repair cards

1. `G6-PR-00`: reuse the strict Evidence evaluator to create deterministic
   run-and-criterion-bound records. Nullable historical records cannot satisfy
   product completion; shared Evidence types receive separate criterion bindings.
2. `G6-PR-01`: build one immutable same-run telemetry snapshot from persisted
   terminal task facts, preserving actual attempts, token split, budget decision and
   measured cost or explicit cost unavailability with provenance.
3. `G6-PR-02`: at the existing SP-00 post-save boundary, reconcile Evidence and
   telemetry before reusing the existing guarded Day-state projection. Exact replay
   is non-duplicating; conflicting facts fail closed.
4. `G6-PR-03`: verify the production composition root with actual FastAPI handlers,
   disposable stores and an injected deterministic executor. No real Day or model.

## Design and scope judgment

G4 already requires exact run-bound Evidence, evidence-based completion, same-run
attempt/token/cost telemetry, provenance and explicit unknowns. G5 WC-05 and WC-08
already allocate the corresponding implementation contracts. The plan therefore
does not reopen G4 or replace accepted components. If the persisted telemetry model
needs an explicit budget-decision field, implementation must version it read-
compatibly and update only the WC-08 contract description and compatibility table.

The accepted real run and artifacts are immutable evidence and are not migrated or
rewritten. Proposed implementation limits are 30 ACTIVE_WORK minutes for the stage,
at most two executions per named focused command and 0 JPY, after separate human
authority.

## Review metadata

- `ARTIFACT_QUALITY_CHECK`: `PASS`
- `SIMPLE_REPORT`: `yes`
- `ACTION_CLASS`: `IMPLEMENTATION`
- `MINIMUM_SUFFICIENT_ACTION`: Verify that PR-00 through PR-03 close only the
  accepted Evidence, terminal projection and telemetry composition gaps, preserve
  fail-closed identity/provenance behavior, and provide sufficient deterministic
  proof before a separately authorized G7 revalidation.
- `WHY_NOT_BROADER`: The discrepancies were reproduced and independently accepted
  from one fixed product run. Another Go, model execution, G4 redesign, unrelated
  refactor, broad regression, Watcher work, G8 or product acceptance is unnecessary.
- `REVIEWER_GUIDANCE`: Eliminate unnecessary overreach. Give only the
  minimum-sufficient, result-oriented instruction needed for the current objective.
  Do not recommend broader work merely because it is possible, cleaner, more
  general, more future-proof or theoretically better.

## Minimum next action

If accepted, record plan acceptance and stop for a separate explicit implementation
authority decision by 広瀬剛. Reviewer plan acceptance alone does not start PR-00.
