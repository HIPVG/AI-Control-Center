# G7 product E2E revision 005 rejection and raw-evidence correction — 2026-10-01

## Review identity

- Rejected pack: `G7-PRODUCT-E2E-20260930-005`
- Rejected reviewed commit: `2ec8cabf55266bd74b95a1ad5902e2c86a811fa1`
- Reviewer result: `REJECT`
- Accepted part of the review: stopping at `REAL_MODE_REQUIRED` is a correct,
  separate authority boundary.
- Rejection reason: the reviewed commit described the persisted RunRecord, API
  readback and one-Go access log but did not contain their raw bytes, so the hashes
  and same-run claim were not independently checkable.

## Minimum correction applied

No service restart, Go, real mode, model, Watcher, G8, product acceptance or source
change occurred. The preserved validation worktree was used only as the source of
existing data.

The following raw artifacts are fixed under
`docs/review-evidence/G7-PRODUCT-E2E-20260930-006/`:

- `run-preflight-history.json`: original immutable `PREFLIGHT` RunRecord version;
- `run-current.json`: original current `EXTERNAL_ACTION_REQUIRED` RunRecord;
- `control-center.json`: original persisted Day snapshot and audit state;
- `preflight-fact.json`: original exact Grant/prerequisite resolution;
- `service-access.log`: original complete Uvicorn access log containing the sole Go;
- `service-stderr.log`: original service stderr;
- `day-status-response.json`: read-only Day API readback from the preserved state;
- `runs-response.json`: read-only run API readback from the preserved state;
- `manifest.json`: byte lengths, SHA-256 values, acquisition classification and
  asserted correlation.

The API response files were acquired on 2026-10-01 with GET-only TestClient calls
against the preserved post-run state. They are explicitly not claimed as original
wire captures from 2026-09-30. The original persisted files and access logs were
copied byte-for-byte.

## Independent reconciliation

A second PowerShell-based check, independent of the capture helper, verified every
manifest SHA-256 and asserted:

- run ID in current and history:
  `run-7ea73560dbac4d27aebaad042022d61a`;
- history state: `PREFLIGHT`;
- current RunRecord: `EXTERNAL_ACTION_REQUIRED / REAL_MODE_REQUIRED`;
- Day API state: `EXTERNAL_ACTION_REQUIRED`;
- run API state: `EXTERNAL_ACTION_REQUIRED / REAL_MODE_REQUIRED`;
- exact access-log occurrences of successful
  `POST /api/local-llm/day/go`: `1`.

The evidence directory is scoped as `-text` in `.gitattributes`. A final independent
check hashed each committed Git blob obtained with `git show` and confirmed that all
eight manifest entries match the published bytes exactly (`GIT_BLOB_HASHES_PASS`).

This correction changes only evidence availability. The revision 005 product result
and its real-runtime stop boundary are unchanged.

`ARTIFACT_QUALITY_CHECK: PASS`
