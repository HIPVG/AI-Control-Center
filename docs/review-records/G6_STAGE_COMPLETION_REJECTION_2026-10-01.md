# G6 returned-stage completion rejection — 2026-10-01

- Pack: `G6-PRODUCT-RUN-RECONCILIATION-STAGE-COMPLETION-20261001-001`
- Reviewed commit: `33774514309495ca0dd353ea6240ef653ff96ab2`
- Result: `REJECT`
- Action class: `IMPLEMENTATION`, pending separate human authority

## Unmet invariant

The accepted plan's invariant 9 includes immutable first-persisted terminal state.
`RunProductComposition.settle_terminal_run()` currently branches on the Day snapshot
before checking whether the current RunRecord is already `COMPLETE`. If the durable
RunRecord is `COMPLETE` but the same-run Day snapshot later presents another state,
the method can delegate to `project_day_state()` and write that conflicting state.

The required correction is limited to rejecting this completed-record/Day-state
conflict before projection and proving the RunRecord remains unchanged. It does not
require another service, Day, model, G7 action or review of other cards.

## Authority boundary

The PR-03 focused command already used both authorized executions. No source change
or additional test may occur until separate human authority grants the bounded guard,
one non-mutation assertion and an additional focused execution.
