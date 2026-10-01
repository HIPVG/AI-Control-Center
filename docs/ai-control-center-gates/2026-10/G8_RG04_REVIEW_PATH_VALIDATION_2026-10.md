# G8 RG-04 — Current Reviewer-Path Validation

- **Validation ID:** `G8-RG04-REVIEW-PATH-VALIDATION-20261001-001`
- **Authority:** `AUTH-G8-RG04-REVIEW-PATH-VALIDATION-20261001-001`
- **Candidate:** `AI-Control-Center-Day6-Bounded-RC1`
- **Fixed source commit:** `656711367ed837ddbb75e6df65234a955e44900d`
- **Probe report ID:** `G8-RG04-REVIEW-PATH-PROBE-20261001-001`
- **State:** `INPUT_BLOCKED_PRE_WATCHER`
- **Release state:** `NO_RELEASE`

## Attempt 002 authority and correction

広瀬剛 authorized `UTH-G8-RG04-REVIEW-PATH-RETRY-20261001-001` exactly as
typed. Revision 002 changes only the validation harness import boundary: before
importing `backend`, it derives the canonical project root from the versioned script
path and prepends that root to `sys.path`. It uses create-only runtime directory
`state/rg04-review-path-validation-20261001-002/` and report ID
`G8-RG04-REVIEW-PATH-PROBE-20261001-002`.

The original pass/fail conditions remain unchanged. This is the sole retry. A
failure retains evidence and stops without another repair. `NO_RELEASE` remains.

## Attempt 002 result

The corrected harness started the Watcher once and observed report comment
5928347837. No matching Reviewer response arrived within 720 seconds because the
Reviewer event task had not yet been configured. The Watcher stopped once with the
probe at `WAITING_RESPONSE`; Codex continuation count is zero. The human created and
ran the Reviewer task only after this stop, so revision 002 cannot apply a later
response. No retry or repair is permitted under this authority.

The evidence-summary helper also matched the literal response example embedded in
the report body. The production Watcher did not apply that text; retain this as a
trace-helper limitation. RG-04 remains incomplete and `NO_RELEASE` remains.

## Attempt 003 authority

広瀬剛 authorized `AUTH-G8-RG04-REVIEW-PATH-RETRY-20261001-002` after confirming
that the GitHub event-triggered Reviewer task was created and run. Attempt 003 uses
new report ID `G8-RG04-REVIEW-PATH-PROBE-20261001-003` and create-only runtime
directory `state/rg04-review-path-validation-20261001-003/`.

The evidence helper excludes the report comment itself from response candidates.
All other one-report, one-Watcher, one-`NO_REPORT` continuation and no-product-effect
boundaries remain unchanged. Failure stops without another repair. `NO_RELEASE`
remains.

## Attempt 003 result

Attempt 003 passed the bounded current reviewer-path round trip. Report comment
5928954706 received exactly correlated response comment 5928970236. The isolated
Watcher applied it once, launched one continuation, recorded exit code 0 and
`NO_REPORT`, cleared pending/outstanding state, and stopped. The original Watcher
registry stayed byte-identical and no scoped product or release effect occurred.

Post-stop process and service-registration checks found zero matches. Scheduled-task
enumeration was unavailable due a CIM access error; no registration operation exists
in the launcher or harness. Retain this host-observability limitation. The result
supports RG-04's bounded happy-path evidence only, not continuous operation or
release. `NO_RELEASE` remains.

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
