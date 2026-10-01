# G6 terminal-state conflict guard — 2026-10-01

## Scope and authority

- Rejection source: `G6-PRODUCT-RUN-RECONCILIATION-STAGE-COMPLETION-20261001-001`
- Authority: `AUTH-G6-TERMINAL-STATE-CONFLICT-GUARD-20261001-001`
- Action class: `IMPLEMENTATION`
- Additional active work: approximately 4 of 10 minutes
- Cost: `0 JPY`

## Correction

`RunProductComposition.settle_terminal_run()` now reads the current RunRecord before
branching on the Day snapshot. When the exact current RunRecord is already
`COMPLETE`, a non-`COMPLETE` Day snapshot is rejected with
`COMPLETED_RUN_DAY_STATE_CONFLICT` at `STATE_REPLAY`; the method never delegates that
conflict to state projection.

The focused assertion creates a completed product run, changes only the persisted Day
snapshot to `FAILED`, and confirms the rejection, unchanged current RunRecord,
unchanged RunRecord version history and no second executor effect.

## Validation

The one additionally authorized execution of:

`python -m pytest -q tests/test_run_product_composition.py tests/test_run_execution_composition.py`

returned `24 passed, 6 warnings in 14.72s`, exit `0`. The warnings are existing
FastAPI/Starlette deprecations. No second additional execution occurred.

## Boundary

This correction addresses only invariant 9's completed-state conflict. It does not
reopen PR-00 through PR-03 or authorize service/browser, actual Day/Go, model,
Watcher, G7/G8 or product acceptance.

`ARTIFACT_QUALITY_CHECK: PASS`
