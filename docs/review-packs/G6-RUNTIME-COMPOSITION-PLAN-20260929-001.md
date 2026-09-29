# Review Pack: G6-RUNTIME-COMPOSITION-PLAN-20260929-001

## Identity

- `PACK_ID`: `G6-RUNTIME-COMPOSITION-PLAN-20260929-001`
- `GATE_TYPE`: `PLAN`
- `REVIEWED_BRANCH`: `agent/g0-g5-baseline-publication`
- `REVIEWED_COMMIT`: `12b93f7f2ff5d017ec38bd9fe5b14ed21a115c40`
- `CREATED_AT`: `2026-09-29T04:38:46Z`
- `REVIEW_POLICY_CONTEXT`: `docs/WORKING_RULES.md` at
  `60c0fe7dcf8935fad4c6d3818256a94e95965501`
- `RETURN_SOURCE`: accepted `G7-MUST-CLOSURE-20260929-001`

## Decision requested

Review whether
`docs/ai-control-center-gates/2026-09/G6_RUNTIME_COMPOSITION_REPAIR_PLAN_2026-09.md`
is the minimum sufficient G6 repair plan for the accepted G7 return. This is a plan
review only; do not authorize implementation or live operations.

## Cause and unchanged design

G7 confirmed that the accepted G6 components exist but are not composed into the
G4-required same-run product route. The repair does not change G4: one RunIntent must
flow through admission, execution, typed Evidence, repair/review, telemetry and
dashboard readback. The accepted fixture and historical-actor results remain valid at
their named layers.

## Planned cards

1. `G6-RI-00`: durable RunRecord spine and guarded Go. Persist before effect, resolve
   trusted facts server-side, and remove the legacy direct-start bypass.
2. `G6-RI-01`: adapt existing Day execution/results into existing Evidence,
   repair/review and human-decision contracts under the same run ID.
3. `G6-RI-02`: persist telemetry and build `/api/local-llm/runs` from persisted
   same-run sources instead of the startup-time empty singleton.
4. `G6-RI-03`: actual FastAPI endpoints plus the production composition root and a
   deterministic injected executor. Prove success/failure/restart behavior without a
   real Day.

The cards are dependency ordered and stop on a G4 contradiction. Existing components
are reused; no framework, alternate state machine, Watcher redesign or real Day is
included.

## Protections and proof boundary

- Exact run identity is required for every state and evidence item.
- Blocked admission persists a blocker and creates no Day effect.
- Completion remains validator- and review-dependent.
- Duplicate/restart/cross-run paths fail closed.
- Existing AI-Control-Center and LocalLLM-Lab dirty work is preserved.
- Per proposed card: 30 ACTIVE_WORK minutes, two runs per declared command, 0 JPY.
- G6 fixture success returns to G7; it is not product E2E acceptance.
- Implementation, test execution, service/browser, Day/Go, model, Watcher, credential,
  spending and G8 remain unauthorized by this plan review.

## Review metadata

- `ARTIFACT_QUALITY_CHECK`: `PASS`
- `SIMPLE_REPORT`: `yes`
- `ACTION_CLASS`: `IMPLEMENTATION`
- `MINIMUM_SUFFICIENT_ACTION`: Verify that RI-00 through RI-03 connect the accepted
  contracts into one production composition root, remove the bypass, and provide a
  sufficient G7 handoff without redesigning G4; accept or identify one concrete plan
  gap.
- `WHY_NOT_BROADER`: The accepted return identifies runtime composition as the sole
  blocking implementation boundary. Rebuilding accepted components, redesigning the
  Watcher, running a real Day or revisiting unrelated cards would exceed it.
- `REVIEWER_GUIDANCE`: Eliminate unnecessary overreach. Give only the
  minimum-sufficient, result-oriented instruction needed for the current objective.
  Do not recommend broader work merely because it is possible, cleaner, more general,
  more future-proof, or theoretically better. No speculative redesign, broad
  refactor, full-repository operation, extra validation, extra research, or
  higher-level optimization unless it is required to achieve the current DoD or
  remove the current blocker.

## Minimum next action

If accepted, record plan acceptance and stop for separate human implementation
authority. Do not begin RI-00 from Reviewer plan acceptance alone.
