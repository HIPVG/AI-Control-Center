# Day 7–14 operations runbook review pack

PACK_ID: DAY7-14-OPERATIONS-RUNBOOK-20261002-001

REVIEWED_COMMIT: 3a12e5efd647dc0c4543b5710fff02c486a9f6c2

ACTION_CLASS: VALIDATION

## Review request

Review the new Day 7–14 operator procedure for correctness, usability and
non-expansion of authority. This is a documentation review. It does not request a
service/Watcher start, Task mutation, Day selection/Go, model execution, credential
change, paid work, release expansion or product acceptance.

Primary artifact:

- `docs/DAY7_14_OPERATIONS_RUNBOOK.md`

Supporting navigation and current-state records:

- `README.md`
- `docs/CURRENT_WORK.md`
- `docs/ENGINEERING_WORK_HISTORY.md`

## Fixed sources checked while authoring

- `docs/WORKING_RULES.md`
  - last modifying commit: `60c0fe7dcf8935fad4c6d3818256a94e95965501`
  - Git blob: `d45b5f47093d32c9f855689f9bc8fa91567e80b2`
- `docs/CURRENT_WORK.md` at the reviewed commit
- `C:\LocalLLM-Lab\docs\runbooks\work-plan-day1-14.md`
- `backend/app.py` Git blob `09bb4a5c7f2d0af1f9a35dbc169fa67b552954c6`
- `backend/control/reviewer_bus.py` Git blob
  `f069923392931842de373f87855224b3d81ed997`
- `scripts/start.ps1` Git blob `8409aa9e6a435ae6c08840639971f21bcb6f0f03`
- `frontend/app.js` Git blob `4f7f674ef03e67cb6f86c5706f55a8f5497844bb`
- Review Bridge PR #1 current head observed during authoring:
  `poc/review-loop-report-types-20260924` at
  `4a06e00c93f70e564cbbce9092e04490d84dbae9`
- Reviewer instruction read from that head:
  `poc/reviewer-task-prompt.md`

Primary artifact Git blob:
`448ad9eb43089c249861a29320d19207b8f07b88`.

## Claims to verify

1. The manual clearly separates the immutable Day 6 bounded-release candidate from
   the development workspace used for Days 7–14.
2. It does not treat documentation as Day/Go/model/service authority.
3. It correctly states that FastAPI starts and stops the local Reviewer Bus Watcher,
   while the ChatGPT Reviewer Task is a separate GitHub-event actor.
4. It correctly records the normal 120-second Watcher cadence, exact
   `REPORT_ID`/`IN_REPLY_TO` correlation, serialized continuation and managed
   `C:\AI-Control-Center\state\codex-sqlite` runtime state.
5. The Task bootstrap prompt reads the complete current PR-head instruction instead
   of embedding a stale copy, excludes scheduled polling and prevents routine human
   relay.
6. Startup, health checks, UI selection/Smoke/Go/Resume/repair/Stop boundaries and
   shutdown instructions match the fixed source implementation.
7. The Day 7–14 loop keeps per-Day authority, evidence, telemetry, reviewer
   acceptance and next-Day authorization distinct.
8. Troubleshooting is fail-closed and does not recommend hand-editing state,
   mismatching responses, destructive Git recovery or silent authority expansion.
9. The procedure remains usable by the named human operator without claiming that
   the service, Watcher, Task or any Day was started by this change.

## Author checks

- `git diff --check`: PASS before the reviewed commit.
- Required sections present: Task setup, startup checks, Watcher startup/status, UI
  operation, reviewer path, Day 7–14 loop, shutdown, troubleshooting and checklists.
- Existing user changes in `config/runtime.yaml` and untracked state were not staged
  or modified.
- No service, Watcher, Task, browser Day/Go, model, credential or external operation
  was started.

## Requested result

Return one of `ACCEPT` or `REJECT` for the fixed reviewed commit. If rejecting, name
only the smallest concrete correctness or operability gap and the minimum document
change required. Do not request live Day execution or broader product validation to
review this operator document.

MINIMUM_SUFFICIENT_ACTION: Verify the fixed runbook against the listed current
policy, source lifecycle, UI and reviewer-transport boundaries.

WHY_NOT_BROADER: The artifact is an operator procedure for already implemented
components; live operation and Day 7 authority are separate boundaries.

REVIEWER_GUIDANCE: Do not turn this documentation review into service startup,
Watcher validation, Task reconfiguration, Day selection/Go, model execution,
implementation work, credential changes, release expansion or product acceptance.

REVIEW_POLICY_CONTEXT: AI-Control-Center `docs/WORKING_RULES.md` last modifying
commit `60c0fe7dcf8935fad4c6d3818256a94e95965501`, file blob
`d45b5f47093d32c9f855689f9bc8fa91567e80b2`; Review Bridge PR #1 head
`4a06e00c93f70e564cbbce9092e04490d84dbae9`, instruction
`poc/reviewer-task-prompt.md`, both read in full for this task.
