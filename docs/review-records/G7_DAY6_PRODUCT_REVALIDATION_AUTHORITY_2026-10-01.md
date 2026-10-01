# G7 Day 6 product revalidation authority — 2026-10-01

## Direct human decision

- Decision ID: `AUTH-G7-DAY6-PRODUCT-REVALIDATION-20261001-001`
- Human authority holder: 広瀬剛
- Exact instruction: `` `AUTH-G7-DAY6-PRODUCT-REVALIDATION-20261001-001`として、固定製品build `656711367ed837ddbb75e6df65234a955e44900d`、既存の承認済みclean LocalLLM-Lab基線、新しい隔離worktree、およびControl Center管理領域 `C:\AI-Control-Center\state\codex-sqlite` を使用し、Day 6の限定製品再検証を許可します。許可範囲は、サービス起動1回、ブラウザーGo 1回、実モデル実行最大1回、ACTIVE_WORK 30分、費用0円です。同一runについて、Evidenceのrun／criterion束縛、終端RunRecord、attempt・token・budget・費用可用性telemetry、API／画面読戻し、Goアクセスログおよび原証拠hashを保持してください。追加Go、再試行、実装修正、Watcher操作、認証変更、G8、製品受入は許可しません。失敗時は状態と証拠を保持して停止してください。同種のcross-component composition不足が再発した場合は小修正を開始せず、G4／G5の統合設計とゲート検証方法の見直しへ戻してください。 ``
- Source class: `RECORDED_DIRECT_CONVERSATION`
- Channel: current Codex Work chat
- Message identifier: `UNKNOWN`
- Exact received time: `UNKNOWN`

## Authorized effect and limits

- Action class: `VALIDATION`
- Product build: `656711367ed837ddbb75e6df65234a955e44900d`.
- LocalLLM-Lab baseline: `e33b0a410fb8647711f02ae4e6e0b66472e6eff0` (the previously approved clean baseline).
- Environment: new isolated product and LocalLLM-Lab worktrees.
- Required runtime binding: `CODEX_SQLITE_HOME=C:\AI-Control-Center\state\codex-sqlite`.
- Service starts: one.
- Browser Go requests: one.
- Actual Codex/model executions: at most one.
- Window: 30 minutes of ACTIVE_WORK.
- Cost limit: 0 JPY.
- Reviewer Bus/Watcher: disabled for this validation; no Watcher operation.
- Required retained evidence: same-run Evidence run/criterion binding, terminal RunRecord, attempt/token/budget/cost-availability telemetry, API and UI readback, Go access log, and raw-evidence hashes.

## Stop boundary

Stop after the single authorized run reaches a terminal or blocked state and its
evidence is preserved. Do not retry, issue another Go, modify implementation, operate
Watcher, alter credentials, begin G8, or claim product acceptance. If another
cross-component composition gap is observed, return the work to G4/G5 integration
design and gate-method review rather than starting a small implementation repair.
