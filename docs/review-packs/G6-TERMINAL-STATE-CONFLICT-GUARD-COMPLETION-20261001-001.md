# G6 terminal-state conflict guard completion review pack

PACK_ID: G6-TERMINAL-STATE-CONFLICT-GUARD-COMPLETION-20261001-001
REPORT_TYPE: COMPLETION_REPORT
ACTION_CLASS: IMPLEMENTATION
REVIEWED_COMMIT: 656711367ed837ddbb75e6df65234a955e44900d
BASELINE_COMMIT: 33774514309495ca0dd353ea6240ef653ff96ab2
POLICY_COMMIT: d45b5f47093d32c9f855689f9bc8fa91567e80b2
AUTHORITY_RECORD: docs/review-records/G6_TERMINAL_STATE_CONFLICT_GUARD_AUTHORITY_2026-10-01.md
ACTIVE_WORK_MINUTES: approximately 4 of 10 additional authorized minutes
CURRENT_TASK: completed RunRecord conflicting Day-state guard
STATE: COMPLETION_REVIEW
ARTIFACT_QUALITY_CHECK: PASS
LOCAL_LLM_INVOCATIONS: 0
MAIN_UNCHANGED: yes

## Review target

The returned-stage review found one unmet portion of invariant 9. Review only:

- `backend/control/run_product_composition.py`
- `tests/test_run_product_composition.py`
- `docs/review-records/G6_TERMINAL_STATE_CONFLICT_GUARD_AUTHORITY_2026-10-01.md`
- `docs/review-records/G6_TERMINAL_STATE_CONFLICT_GUARD_2026-10-01.md`

The rejected stage pack remains unchanged. PR-00 through PR-03 are not reopened.

## Bounded correction

`settle_terminal_run()` now reads the current RunRecord before branching on the Day
snapshot. For the exact current run, when the durable RunRecord is already
`COMPLETE` and the Day snapshot is not `COMPLETE`, it returns:

- `outcome: REJECTED`
- `reason_code: COMPLETED_RUN_DAY_STATE_CONFLICT`
- `stage: STATE_REPLAY`

It does not call `project_day_state()`, bind Evidence, write telemetry or append a
RunRecord version. The existing exact COMPLETE replay path is unchanged.

The new assertion completes one deterministic product run, persists a conflicting
`FAILED` Day snapshot, invokes settlement and verifies the current RunRecord, complete
version history and single executor-effect count are unchanged.

## Validation

The prior PR-03 command allowance was exhausted. Human authority
`AUTH-G6-TERMINAL-STATE-CONFLICT-GUARD-20261001-001` granted one additional execution
of:

```text
python -m pytest -q tests/test_run_product_composition.py tests/test_run_execution_composition.py
```

The single execution returned `24 passed, 6 warnings in 14.72s`, exit `0`. The six
warnings are existing FastAPI/Starlette deprecations. No second additional execution
occurred.

## Boundary and next action

REMAINING_GAPS: none within this isolated invariant-9 correction.

No service/browser, actual Day/Go, model, Watcher, credential, spending, G7/G8 or
product-acceptance action occurred.

NEXT_ACTION_AFTER_REVIEW: If accepted, record this guard accepted and submit revision
002 of the G6 product-run-reconciliation stage completion pack; otherwise identify
one concrete remaining conflict path.

REVIEWER_DELIVERY_CHANNEL: none (manual fixed-pack pilot)
REVIEWER_DELIVERY_STATUS: pending

MINIMUM_SUFFICIENT_ACTION: Verify that an already COMPLETE current RunRecord is
checked before the Day-state branch, that a non-COMPLETE Day snapshot is rejected
without projection, and that the current record and version history remain unchanged;
then accept or identify one concrete defect.

WHY_NOT_BROADER: The stage rejection identified only this completed-state conflict.
Other cards, live product execution and G7 are unnecessary and unauthorized.

SIMPLE_REPORT: yes

REVIEWER_GUIDANCE: Eliminate unnecessary overreach. Give only the minimum-sufficient,
result-oriented instruction needed for the current objective. Do not recommend broader
work merely because it is possible, cleaner, more general, more future-proof, or
theoretically better. No speculative redesign, broad refactor, full-repository
operation, extra validation, extra research, or higher-level optimization unless it is
required to achieve the current DoD or remove the current blocker.

REVIEW_POLICY_CONTEXT: commit=d45b5f47093d32c9f855689f9bc8fa91567e80b2;
read=yes; changed=no; latest_human_and_reviewer_messages_read=yes;
instruction_applied=completed RunRecord conflicting Day-state guard and one additional
focused execution under AUTH-G6-TERMINAL-STATE-CONFLICT-GUARD-20261001-001;
deviation=none.
