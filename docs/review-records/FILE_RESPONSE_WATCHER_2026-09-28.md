# File response reader: design and verification record

Authority: human in this Codex chat requested design and implementation of file
response reading by the existing Watcher. This does not authorize the separate
WC02 host source-write/reload handoff. Implementation baseline: 4ac5550.

## Before implementation

Current source: backend/control/reviewer_bus.py uses gh issue comments, JSON
report_registry, one cycle lock, pending-response revalidation, then bounded
Codex exec and envelope validation. backend/app.py constructs the watcher at
startup. Persisted state reports polling and no pending continuation; this is
not proof of the in-memory source revision. No hot reload is evidenced, so
this delivery is source plus isolated tests, not a claim of live deployment.
Existing desktop apply_patch and GitHub read/write worked during the PoC;
this does not establish the separate sandboxed WC02 actor's write capability.
Unrelated runtime.yaml and history changes must be preserved.

Actors: Codex publishes an immutable request file and trigger comment; Reviewer
writes a response file on the fixed Review Bridge PR branch; Watcher reads via
existing gh authentication and validates, persists and dispatches; Codex applies
the full reply within recorded authority. Human retains genuine scope decisions.
No new service, credentials, model API or host write/reload mechanism is added.

Contract: explicit RESPONSE_TRANSPORT: github_file on a NEW report selects files.
Legacy comments and FILE_REVIEW_REQUEST PoCs are not silently migrated. Pin
REQUEST_COMMIT (40 hex), REQUEST_PATH=poc/file-review-requests/<REPORT_ID>.md and
RESPONSE_PATH=poc/file-review-responses/<REPORT_ID>.md. Safe IDs contain only
letters, digits, underscore and hyphen. Fetch the same-repository PR head SHA
on branch poc/review-loop-report-types-20260924, then read contents at that SHA;
request contents are read at REQUEST_COMMIT. No checkout or executable file is
loaded. Bound text size, reject non-file objects and validate Git blob hashes.

Compare notification/request control fields and response IN_REPLY_TO,
REQUEST_COMMIT, REQUEST_PATH, RESPONSE_KIND=GIT_FILE, unique RESULT and NEXT_ACTION.
Persist transport and request binding on first sight; changed bindings fail closed.
File mode never consumes a comment reply. Store response source, head, path and
blob separately from comment IDs. Re-fetch before retry; missing, changed or
mismatched pending content is invalidated with retained evidence and no execution.
Successful apply is deduplicated across restart by the existing report registry.
File confirmation IDs use their explicit file identity, not fabricated comment IDs.

Happy path: notify -> bind request -> read file at PR head -> exact validation ->
RESPONSE_RECEIVED -> APPLYING -> existing envelope handling -> APPLIED. An optional
ACK goes directly to ACKNOWLEDGED without Codex. One continuation runs per cycle.
Failure: absent response waits; network/permission/malformed data record a per-report
error; changed pending file is quarantined; wrong binding/result never starts Codex
or posts. CONTINUATION_FAILED is not APPLIED. Existing confirmation/HUMAN_REQUIRED
rules continue to apply. Errors on one file request need not block another request.
After uncertain process interruption exactly-once external effects are not claimed;
this change preserves existing continuation semantics, not a transactional executor.

Rollback: keep comment mode for new reports; retain file history and outstanding
bindings. Do not reinterpret a pending file report as a comment report. Deployment
requires an explicitly verified reload of the existing process; not performed by
this source/test change. Terminal evidence: focused fixture state transitions and
legacy regression, plus separately identified read-only real GitHub adapter probe.

## Implementation evidence

Implemented reader in backend/control/reviewer_files.py and integrated it with
ReviewerBusWatcher. Pending file identity is checked both against persisted request
state and freshly fetched contents. Invalidated pending state is quarantined;
file provenance never masquerades as a numeric comment ID. Existing registrations
retain their persisted mode; old PoCs are not silently promoted into execution
requests. A registry written by the old watcher without a transport field derives
the mode once from the explicit RESPONSE_TRANSPORT marker at upgrade; this allows
review requests published before deployment to be consumed after loading the reader.

Focused command: `python -m pytest tests/test_reviewer_files.py
tests/test_reviewer_bus.py tests/test_reviewer_confirmation.py -q -p no:cacheprovider`.
Result: 51 passed. Tests assert APPLIED once across restart, ACK with zero Codex
calls, field/hash/type/size failures with zero calls, missing reply waiting,
pending deletion/edit/mismatch quarantine, network error preserving pending,
unchanged failed pending retry, corrupted pending IDs not executing another reply,
independent comment handling, legacy PoC nonmigration and confirmation resolution.
One fixture initially treated a historical first-load request as active; adjusted
the scenario to register F1 before publishing C1, preserving the no-replay rule.

Read-only production reader probe fetched PoC003 at PR head
b9f2629cae7d6647779d67d87aaf522d5dcec259 and verified blob
e77ecb153e92e5f6d9883ccdcb698b08e2227661, size and UTF-8 body. This used only
GitHub GETs, not run_once, state writes or Codex. PoC003 predates opt-in and is
not eligible for automatic migration. Live Watcher reload/continuation remains
NOT_VERIFIED. No WC02 patch or host handoff implementation was performed.

## New request template

Commit the following control fields plus review evidence as an immutable request
file. The trigger carries the same fields and adds REQUEST_COMMIT with that SHA.
The Reviewer commits its reply on the existing PR branch; the Watcher reads it.

```
REPORT_ID: <new safe ID>
REPORT_TYPE: PROGRESS_UPDATE
RESPONSE_REQUIRED: yes
RESPONSE_TRANSPORT: github_file
REQUEST_PATH: poc/file-review-requests/<new safe ID>.md
RESPONSE_PATH: poc/file-review-responses/<new safe ID>.md
```

Echo REVIEWED_COMMIT and all confirmation/authority control fields identically
between the request and notification when present. The response format is
IN_REPLY_TO, RESULT, REQUEST_COMMIT, REQUEST_PATH, RESPONSE_KIND: GIT_FILE and
NEXT_ACTION; authority confirmations additionally echo existing binding fields.
Request creation stays with the publisher; the reader does not synthesize an
immutable request from a mutable comment. New continuations must not claim file
mode without first publishing such a request; their default remains comment mode.
