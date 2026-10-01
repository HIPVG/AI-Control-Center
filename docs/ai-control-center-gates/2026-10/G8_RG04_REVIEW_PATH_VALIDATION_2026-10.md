# G8 RG-04 — Current Reviewer-Path Validation

- **Validation ID:** `G8-RG04-REVIEW-PATH-VALIDATION-20261001-001`
- **Authority:** `AUTH-G8-RG04-REVIEW-PATH-VALIDATION-20261001-001`
- **Candidate:** `AI-Control-Center-Day6-Bounded-RC1`
- **Fixed source commit:** `656711367ed837ddbb75e6df65234a955e44900d`
- **Probe report ID:** `G8-RG04-REVIEW-PATH-PROBE-20261001-001`
- **State:** `INPUT_BLOCKED_PRE_WATCHER`
- **Release state:** `NO_RELEASE`

## Objective

Establish whether the current GitHub Review Bridge PR #1, production
`ReviewerBusWatcher` and Control Center-managed `CODEX_SQLITE_HOME` provide one
current, bounded, exactly-correlated reviewer round trip without product effects.

The production Watcher/application blobs at the fixed candidate commit and current
branch are identical:

- `backend/control/reviewer_bus.py` Git blob
  `f069923392931842de373f87855224b3d81ed997`;
- `backend/app.py` Git blob
  `09bb4a5c7f2d0af1f9a35dbc169fa67b552954c6`.

## Procedure

1. Preserve the existing project Watcher registry unchanged. It contains historical
   unfinished records and is not a valid clean probe ledger.
2. Start one production `ReviewerBusWatcher` instance with an empty create-only
   isolated ledger under
   `state/rg04-review-path-validation-20261001-001/`.
3. Keep the continuation working directory at `C:\AI-Control-Center`; the production
   Watcher must set `CODEX_SQLITE_HOME` to
   `C:\AI-Control-Center\state\codex-sqlite`.
4. Publish exactly one top-level no-effect `PROGRESS_UPDATE` to Review Bridge PR #1
   using the fixed probe report ID.
5. Require a single response whose sole `IN_REPLY_TO` equals the probe ID.
6. Permit exactly one Codex continuation. Its only allowed result is `NO_REPORT`;
   it may not change files, execute product work or publish a follow-up.
7. Stop the Watcher after applied correlation or the first failure/timeout. Preserve
   report/response IDs, hashes, timestamps, continuation count/result, final Watcher
   state and autostart-query results as machine-readable evidence.
8. Reuse accepted deterministic fixture evidence for mismatch/duplicate rejection;
   do not inject misleading live PR comments merely to recreate those paths.

## Pass conditions

- exactly one probe report is delivered and read back;
- exactly one later response has the exact sole `IN_REPLY_TO`;
- the isolated Watcher ledger records that response for the probe;
- exactly one Codex continuation exits zero with `NO_REPORT`;
- no follow-up report is attempted or published;
- the Watcher ends with `running: false`, no pending/outstanding probe and the probe
  marked applied exactly once;
- no Windows service or scheduled task registers the validation harness; and
- no Day/Go, model, product-state, source, credential, distribution or release effect
  occurs.

Any failed condition stops the validation without repair. The evidence may support
RG-04 review but cannot itself authorize RG-06 or release.

## Attempt 001 result

The validation process exited before constructing the Watcher because the versioned
probe script could not import the project `backend` package from its script-relative
module path. Watcher starts, probe posts, responses and Codex continuations therefore
all remain zero. The failure is fixed at
`docs/review-evidence/G8-RG04-REVIEW-PATH-VALIDATION-20261001-001/preflight-failure-trace.json`.
The trace is 2,333 bytes with SHA-256
`c90ff21181d061dbb1bb6303f73c23723fe8d9347f0d5951eb1e8e81b0edb146`.

Per the authority's stop-on-problem condition, no import-path correction or retry was
performed. RG-04 remains incomplete and requires a new human retry authority.
