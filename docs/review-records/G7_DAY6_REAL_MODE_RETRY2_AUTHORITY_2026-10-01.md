# G7 Day 6 real-mode retry 2 authority — 2026-10-01

## Direct human decision

- Decision ID: `AUTH-G7-DAY6-REAL-MODE-RETRY-20261001-002`
- Human authority holder: 広瀬剛
- Exact instruction: `` `AUTH-G7-DAY6-REAL-MODE-RETRY-20261001-002`として、既存のControl Center管理領域 `C:\AI-Control-Center\state\codex-sqlite` を `CODEX_SQLITE_HOME` に明示設定・起動前確認したうえで、新しい隔離worktreeによるDay 6 Goを追加1回許可します。実モデル実行は1回、費用0円、その他の条件は前回と同じです。 ``
- Source class: `RECORDED_DIRECT_CONVERSATION`
- Channel: current Codex Work chat
- Message identifier: `UNKNOWN`
- Exact received time: `UNKNOWN`

## Authorized effect and limits

- Action class: `VALIDATION`
- Target: one replacement Day 6 real-model product validation.
- Product build: `3e82626faebab8e9722939b92267deb51075d93b`.
- LocalLLM-Lab baseline: `e33b0a410fb8647711f02ae4e6e0b66472e6eff0`.
- Environment: a new clean product worktree; retain both previous blocked runs.
- Grant/RunIntent limit: `max_attempts: 2` for exact admission matching.
- Actual Codex/model execution limit: one.
- Runtime: local override `codex.mode: real` only for this validation.
- Required runtime binding: `CODEX_SQLITE_HOME=C:\AI-Control-Center\state\codex-sqlite`.
- Pre-Go requirement: verify the service process received that exact existing directory.
- Existing routing: standard profile, `gpt-5.6-terra`, medium reasoning.
- Window: 30 minutes of ACTIVE_WORK.
- Additional Go limit: one.
- Token limit: unspecified; existing deterministic budget controls remain active.
- Cost limit: 0 JPY.
- Allowed writes: Day 6 output scope in an isolated LocalLLM-Lab engineering
  worktree, plus validation state and evidence in the new product worktree.
- Reviewer Bus remains disabled. No Watcher restart or credential change.

## Observation and stop boundary

Observe the real-model Day 6 product path and preserve the RunIntent, admission,
RunRecord, Day state, Evidence, telemetry and bounded worktree result that actually
occur. Evaluate A02. Evaluate A03 and A04-current only if the authorized path reaches
them naturally; do not inject a failure or add another execution merely to exercise
them.

Stop on completion, failure, an additional authority/repair need, the additional-Go
or one-model limit, the zero-cost limit, or the ACTIVE_WORK limit. Do not operate
Watcher, start G8, merge, modify `main`, alter credentials, or claim product
acceptance.
