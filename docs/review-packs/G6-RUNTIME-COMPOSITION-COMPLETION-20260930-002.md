# G6 runtime-composition return completion review pack — revision 002

PACK_ID: G6-RUNTIME-COMPOSITION-COMPLETION-20260930-002
REPORT_TYPE: COMPLETION_REPORT
ACTION_CLASS: IMPLEMENTATION
REVIEWED_COMMIT: a71ab7a30edad05a1b6310fb87548764fe5e17c1
BASELINE_COMMIT: bff5990bf11b40892f1841f9ab72deda1a1bcb39
SUPERSEDES_PACK: G6-RUNTIME-COMPOSITION-COMPLETION-20260930-001
PRIOR_RESULT: REJECT
POLICY_COMMIT: 60c0fe7dcf8935fad4c6d3818256a94e95965501
ARTIFACT_QUALITY_CHECK: PASS

## Rejection addressed

The first stage pack's accepted-card identities were correct, but its DoD claim lacked
two guards. Revision 002 changes only those rejected boundaries.

### Exact snapshot run binding before Evidence

`evaluate_criterion` now checks `LocalLLMDaySnapshot.run_id == target run_id` before
contract or Evidence evaluation. The focused assertion provides otherwise valid
same-Day/same-contract Evidence while the snapshot identifies another run and proves:

- `DAY_SNAPSHOT_RUN_ID_MISMATCH` is returned;
- the target RunRecord is unchanged; and
- the entire Day snapshot, including criteria and Evidence store, is unchanged.

### Required review before `COMPLETE`

`project_day_state` now rejects `COMPLETE` while required review is unverified. It
checks both the in-memory ReviewControl and the persisted
`REVIEW_RESPONSE_REQUIRED` blocker. The focused assertion validates all declared
Evidence, persists a required-review wait, reconstructs `RunExecutionComposition`,
then proves `COMPLETE` is rejected with `REQUIRED_REVIEW_UNVERIFIED` and the durable
RunRecord is unchanged.

The accepted verified-response path already clears the blocker and returns the same
run to `PREFLIGHT`; no new approval or completion state was introduced.

## Fixed paths and validation

- `backend/control/run_execution_composition.py`
- `tests/test_run_execution_composition.py`
- `docs/review-records/G6_RUNTIME_COMPOSITION_COMPLETION_REJECTION_2026-09-30.md`
- `docs/review-records/G6_RUNTIME_COMPOSITION_STAGE_REVISION_002_2026-09-30.md`

Focused command:

```text
python -m pytest -q tests/test_run_execution_composition.py tests/test_run_product_composition.py tests/test_runtime_composition.py tests/test_run_projection_composition.py tests/test_api.py
```

- Attempt 1: `44 passed, 6 warnings in 10.35s`.
- Attempt 2 after restart-proof strengthening: `44 passed, 6 warnings in 9.86s`.

Scoped compile and diff checks passed. The warnings are existing FastAPI/Starlette
deprecations. No real service/browser/Day 6/product E2E, model, Watcher, credential,
spending, G7 or G8 action occurred.

## Decision boundary

Recheck only invariants 5 and 8 at the fixed commit. All other accepted-card evidence
and boundaries are unchanged. Acceptance closes the G6 runtime-composition repair only
at implementation/deterministic-fixture scope and does not start G7 or product E2E.

MINIMUM_SUFFICIENT_ACTION: Verify that mismatched snapshot-run Evidence is rejected
before mutation and that an unverified required review remains completion-blocking
after composition reconstruction; accept the corrected G6 stage or identify one
remaining concrete defect in those two guards.

WHY_NOT_BROADER: The first review isolated exactly two completion defects. No broader
refactor, real service/browser/Day operation, product E2E or G7 work is needed for the
current decision.

SIMPLE_REPORT: yes

REVIEWER_GUIDANCE: Eliminate unnecessary overreach. Give only the minimum-sufficient,
result-oriented instruction needed for the current objective. Do not recommend broader
work merely because it is possible, cleaner, more general, more future-proof, or
theoretically better. No speculative redesign, broad refactor, full-repository
operation, extra validation, extra research, or higher-level optimization unless it is
required to achieve the current DoD or remove the current blocker.

REVIEW_POLICY_CONTEXT: commit=60c0fe7dcf8935fad4c6d3818256a94e95965501;
read=yes; changed=no; latest_response_read=yes; instruction_applied=exact snapshot-run
Evidence guard and persisted unverified-review completion guard; deviation=none.
