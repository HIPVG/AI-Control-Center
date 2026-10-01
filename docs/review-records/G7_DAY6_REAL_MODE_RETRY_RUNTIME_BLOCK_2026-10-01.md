# G7 Day 6 real-mode retry runtime block — 2026-10-01

## Result

The single additional Go authorized by
`AUTH-G7-DAY6-REAL-MODE-RETRY-20261001-001` was used in a new isolated product
worktree on build `3e82626faebab8e9722939b92267deb51075d93b`.

- Run ID: `run-dbfa4263c3fd47709057548288a9468d`
- Go requests: exactly one
- Admission: `ADMISSIBLE`
- Final durable state: `EXTERNAL_ACTION_REQUIRED`
- Surface blocker: `OPENAI_CREDENTIALS_MISSING`
- Actual runner failure: `CODEX_SQLITE_HOME_NOT_FOUND`
- Codex attempt entries: one
- Codex subprocess/thread/turn started: no
- Input, cached input, gross input and output tokens: zero
- Cost: 0 JPY
- LocalLLM-Lab baseline changes: none
- Day output/source changes: none

The Grant used `max_attempts: 2` and exactly matched the immutable RunIntent.
The prerequisite observation also matched, so the previous admission mismatch was
resolved. The failure occurred later, at the actual Codex runner boundary, before a
subprocess or model request began.

## Root cause and classification

`RealCodexRunner.resolve_codex_sqlite_home()` requires an existing
`CODEX_SQLITE_HOME`, or otherwise falls back to the product worktree's
`state/codex-sqlite`. The fresh detached validation worktree had neither an explicit
environment setting nor that local directory. The runner therefore returned
`CODEX_SQLITE_HOME_NOT_FOUND` without starting Codex.

The repository already has a Control Center-managed isolated runtime directory at
`C:\AI-Control-Center\state\codex-sqlite`. It is distinct from the desktop Codex
state database. This path existed before the validation; it was not supplied to the
isolated service process. This is a validation setup omission, not a product-source
or credential finding. The generic product mapping surfaced it as
`OPENAI_CREDENTIALS_MISSING`, but no credential check or change was performed.

## Stop and return boundary

The service and browser tab were stopped. The failed state and isolated engineering
worktree were retained. No retry, Watcher action, credential operation, failure
injection, G8 action or product-acceptance claim was made.

The current authorization is exhausted because its one additional Go was used.
Before any further product Go, a new authority must explicitly permit a new isolated
run and the service startup must bind
`CODEX_SQLITE_HOME=C:\AI-Control-Center\state\codex-sqlite`. Startup verification
must establish that this exact existing directory is selected before the UI is
used. The one-model-execution and zero-cost limits must remain unchanged.

## Evidence

Raw Grant, prerequisite, preflight fact, RunRecord history/current, Day state and
complete service logs are fixed under
`docs/review-evidence/G7-DAY6-REAL-MODE-RETRY-20261001-001/`, with byte lengths and
SHA-256 values in its manifest.
