# G8 RG-03 Stop/Rollback Validation Authority

## Authority identity

- **Authority ID:** `AUTH-G8-RG03-STOP-ROLLBACK-20261001-001`
- **Decision maker:** 広瀬剛
- **Source class:** `RECORDED_DIRECT_CONVERSATION`
- **Received through:** current Codex Work chat
- **Message ID / exact received time:** `UNKNOWN`
- **Record date:** 2026-10-01

## Exact human approval

> 許可します。実施してください。

This explicitly approves the complete immediately preceding RG-03 proposal in the
same conversation.

## Authorized validation

- Verify the fixed archive identity, absent target root and free port 8000.
- Extract once to
  `C:\AI-Control-Center\state\release-candidates\AI-Control-Center-Day6-Bounded-RC1`.
- Verify inventory, `mock` mode and loopback launcher settings.
- Start the packaged service once on `127.0.0.1:8000`.
- Perform no more than two read-only HTTP checks.
- Stop the exact launched candidate process tree once and confirm its process and
  listener are absent.
- Preserve archive, extraction, state, logs, timestamps, PID/listener/HTTP and hash
  evidence without automatic deletion.
- Define rollback as no candidate process/listener/autostart, unchanged existing
  environment and original, with the inactive candidate root retained as evidence.
- Record and publish the RG-03 result and review pack.

## Limits and exclusions

- ACTIVE_WORK: 20 minutes maximum.
- Extraction: one maximum.
- Service start: one maximum.
- Controlled stop: one maximum.
- Read-only HTTP checks: two maximum.
- Cost: 0 JPY.
- Existing target/listener causes `INPUT_BLOCKED`; do not overwrite, delete or stop it.
- No source implementation, browser, Day/Go, model, real mode, Watcher, credential,
  external exposure, distribution, RG-04, RG-06 or release action.
- Failure is preserved and stops without retry or repair.
