# G6 product-run reconciliation implementation authority — 2026-10-01

## Decision

- Decision ID: `AUTH-G6-PRODUCT-RUN-RECONCILIATION-20261001-001`
- Decider: 広瀬剛
- Source class: `RECORDED_DIRECT_CONVERSATION`
- Channel: Codex Work chat
- Message ID and exact receipt time: `UNKNOWN`
- Exact text: `G6 PR-00〜PR-03の実装とfixture検証を、30 ACTIVE_WORK分・各焦点コマンド最大2回・費用0円で許可します。`

## Effect and limits

The accepted plan at `73cfcafd85f285cdc5db6afba5d322d48af7d304` may be
implemented in dependency order from PR-00 through PR-03. The stage has one shared
30 ACTIVE_WORK-minute window, each named focused command may run at most twice, and
cost must remain 0 JPY. Card review remains a dependency boundary; acceptance of one
card permits selection of the next card inside this already-authorized stage.

This authority does not permit another Go, real Day/model execution, service/browser
operation, Watcher operation, credential change, G8, `main` modification, destructive
Git action or product acceptance.
