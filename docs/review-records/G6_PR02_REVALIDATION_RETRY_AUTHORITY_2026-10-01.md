# G6 PR-02 revalidation retry authority — 2026-10-01

- Decision ID: `AUTH-G6-PR02-REVALIDATION-RETRY-20261001-001`
- Decider: 広瀬剛
- Channel: Codex Work chat
- Source class: `RECORDED_DIRECT_CONVERSATION`
- Message ID/time: `UNKNOWN`
- Cost limit: `0 JPY`
- Additional active-work limit: `10 minutes`

Exact authority text:

> `AUTH-G6-PR02-REVALIDATION-RETRY-20261001-001`として、完了済みrunの完全一致再適用でEvidenceとDay snapshotを変更せず、競合入力を拒否するPR-02限定修正、非変更assertionの追加、および既存の焦点コマンド追加1回を、追加ACTIVE_WORK 10分・費用0円で許可します。PR-03、実サービス、Day／Go、モデル、Watcher、G7／G8は許可しません。

This authority permits one bounded PR-02 repair and exactly one additional execution
of the already recorded focused command. It does not authorize PR-03 or product work.
