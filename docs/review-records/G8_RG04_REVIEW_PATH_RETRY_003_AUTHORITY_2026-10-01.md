# G8 RG-04 Review-Path Retry 003 Authority

- **Decision ID:** `AUTH-G8-RG04-REVIEW-PATH-RETRY-20261001-002`
- **Human instruction:** 「許可します。実施してください。」
- **Source:** `RECORDED_DIRECT_CONVERSATION`
- **Message ID / exact receipt time:** `UNKNOWN`
- **Release state:** `NO_RELEASE`

## Authorized effect

Authorize one new RG-04 attempt now that the human confirms the GitHub event-triggered
Reviewer task has been created and run. Use report ID
`G8-RG04-REVIEW-PATH-PROBE-20261001-003` and create-only runtime directory
`state/rg04-review-path-validation-20261001-003/`.

The attempt is limited to one no-effect report, one Watcher start and stop, one exact
Reviewer response, and one Codex continuation whose only valid output is
`NO_REPORT`. The evidence helper must exclude the report comment itself from response
summaries. Existing credentials and the managed `CODEX_SQLITE_HOME` are used; cost
is 0 JPY.

Product source, the existing Watcher registry, Day/Go, model execution, product
state, other services, credentials, RG-06, distribution and release are excluded.
On failure, preserve evidence and stop without another repair or retry.
