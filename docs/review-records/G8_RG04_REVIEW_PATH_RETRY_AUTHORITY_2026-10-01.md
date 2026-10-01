# G8 RG-04 Review-Path Retry Authority

- **Authority ID:** `UTH-G8-RG04-REVIEW-PATH-RETRY-20261001-001`
- **Recorded from:** direct human instruction in the current Codex conversation
- **Receipt time/message ID:** `UNKNOWN`
- **Release state:** `NO_RELEASE`

## Authorized action

Repair only the revision 001 validation harness import path by adding the canonical
project root to Python's import path, then run one revision 002 validation attempt.
Use a new create-only state directory and report ID
`G8-RG04-REVIEW-PATH-PROBE-20261001-002`. Permit one Watcher start and stop, one
exactly correlated response, and one Codex continuation whose only valid result is
`NO_REPORT`. Preserve machine-readable evidence and publish the RG-04 outputs.

Limits are the remaining 10 ACTIVE_WORK minutes, 0 JPY, and existing credentials
only. Product source, the existing Watcher registry, Day/Go, model execution,
product state, additional service exposure, credentials, RG-06, distribution and
release remain excluded. On failure, preserve evidence and stop without repair.

The authority ID above is preserved exactly as typed by the human; it is not silently
normalized to an `AUTH-` prefix.
