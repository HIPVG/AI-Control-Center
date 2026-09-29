# G6 runtime-composition stage evidence — revision 002

## Prior rejection addressed

This revision preserves the accepted RI-00 through RI-03 card history and corrects
only the two gaps identified against `G6-RUNTIME-COMPOSITION-COMPLETION-20260930-001`.

### Invariant 5 — Evidence cannot cross the snapshot run boundary

`RunExecutionComposition.evaluate_criterion` now requires
`LocalLLMDaySnapshot.run_id` to exactly equal the target RunRecord run ID before the
contract or supplied Evidence is evaluated. A new assertion supplies valid Evidence
for the target RunRecord while the same-Day/same-contract snapshot names another run.
It requires `DAY_SNAPSHOT_RUN_ID_MISMATCH` and proves both the persisted RunRecord and
complete snapshot are unchanged.

### Invariant 8 — required review blocks completion

`project_day_state` now rejects `COMPLETE` with `REQUIRED_REVIEW_UNVERIFIED` while a
run-bound review is not `VERIFIED`. The guard uses the persisted
`REVIEW_RESPONSE_REQUIRED` blocker as well as the in-memory ReviewControl, so an
Engine/composition reconstruction cannot erase the requirement. The new assertion:

- validates every declared Day 6 Evidence type;
- opens a required review and persists its blocker;
- reconstructs `RunExecutionComposition` from the durable store;
- requests `COMPLETE`; and
- proves the RunRecord remains byte-equivalent at the model boundary.

An exactly verified review already clears the persisted blocker through the accepted
same-run continuation path, so this guard does not manufacture a new approval state.

## Focused validation

Command, executed twice within the rejection-repair limit:

```text
python -m pytest -q tests/test_run_execution_composition.py tests/test_run_product_composition.py tests/test_runtime_composition.py tests/test_run_projection_composition.py tests/test_api.py
```

- Attempt 1: `44 passed, 6 warnings in 10.35s`, exit `0`.
- Attempt 2 after strengthening restart persistence: `44 passed, 6 warnings in 9.86s`, exit `0`.

Warnings are the already-recorded FastAPI/Starlette deprecations. Scoped `compileall`
and `git diff --check` passed. No service/browser, real Day/Go, model, Watcher,
credential, external delivery, spending, G7 or G8 action occurred.

## Corrected DoD result

- Invariant 5 exact same-run binding: `PASS` with pre-application non-mutation proof.
- Invariant 8 Evidence plus required-review completion guard: `PASS`, including
  reconstructed-composition proof.
- Other invariants and accepted card evidence: unchanged from the first stage record.

The proposed result remains `COMPLETE` only for G6 runtime-composition implementation
and deterministic fixtures. It is not product E2E or authority to begin G7 activity.

`ARTIFACT_QUALITY_CHECK: PASS`
