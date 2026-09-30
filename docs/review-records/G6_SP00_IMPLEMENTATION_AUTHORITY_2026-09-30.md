# G6 SP-00 implementation authority — 2026-09-30

## Decision identity

- `DECISION_ID`: `AUTH-G6-SP00-IMPLEMENTATION-20260930-001`
- Decider: 広瀬剛
- Source class: `RECORDED_DIRECT_CONVERSATION`
- Channel: current Codex Work chat
- Message ID: `UNKNOWN`
- Received time: `UNKNOWN`
- Accepted plan: `G6-SAME-RUN-STATE-PROJECTION-PLAN-20260930-002`
- Plan commit: `c6b81eb779350f9f2ed1be47bcc6da1a23c3aa0b`

## Exact human text

> SP-00の実装とfixture検証を、30 ACTIVE_WORK分・各焦点コマンド最大2回・費用0円で許可します。受理記録もGitHubへpushしてください。

## Authorized effect and limits

- Implement only SP-00's post-save asynchronous Day-worker settlement notification
  and production wiring to the existing guarded same-run projection.
- Add and execute only the focused deterministic fixtures required by the accepted
  plan.
- Work window: 30 minutes of `ACTIVE_WORK`.
- Each named focused command: at most two executions.
- Cost: 0 JPY.
- Publish the already-created plan acceptance record to the existing public branch.

Not authorized: service/browser operation, actual Go/Day, real-mode or configuration
change, model execution, Watcher, credentials, spending, G7 product rerun, G8,
product acceptance, destructive Git or unrelated refactoring.
