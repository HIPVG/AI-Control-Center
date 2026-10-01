# G7 Day 6 real-mode retry authority — 2026-10-01

## Direct human decision

- Decision ID: `AUTH-G7-DAY6-REAL-MODE-RETRY-20261001-001`
- Human authority holder: 広瀬剛
- Exact instruction: `` `AUTH-G7-DAY6-REAL-MODE-RETRY-20261001-001`として、Grantのmax_attemptsを製品RunIntentに合わせて2とし、実モデル実行は1回に制限したまま、新しい隔離worktreeでDay 6 Goを追加1回許可します。その他の条件は前回と同じです ``
- Source class: `RECORDED_DIRECT_CONVERSATION`
- Channel: current Codex Work chat
- Message identifier: `UNKNOWN`
- Exact received time: `UNKNOWN`

## Authorized effect and limits

- Action class: `VALIDATION`
- Target: one replacement Day 6 real-model product validation.
- Product build: `3e82626faebab8e9722939b92267deb51075d93b`.
- LocalLLM-Lab baseline: `e33b0a410fb8647711f02ae4e6e0b66472e6eff0`.
- Environment: a new clean product worktree; retain the previously blocked run.
- Grant/RunIntent limit: `max_attempts: 2` for exact admission matching.
- Actual Codex/model execution limit: one, enforced by the existing Day engineering
  adapter's `max_codex_attempts=1` boundary.
- Runtime: local override `codex.mode: real` only for this validation.
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
RunRecord, Day state, evidence, telemetry and bounded worktree result that actually
occur. Evaluate A02. Evaluate A03 and A04-current only if the authorized path reaches
them naturally; do not inject a failure or add another execution merely to exercise
them.

Stop on completion, failure, an additional authority/repair need, the additional-Go
or one-model limit, the zero-cost limit, or the ACTIVE_WORK limit. Do not operate
Watcher, start G8, merge, modify `main`, alter credentials, or claim product
acceptance.
