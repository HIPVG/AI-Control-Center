# G6 PR-00 validation retry authority — 2026-10-01

## Decision

- Decision ID: `AUTH-G6-PR00-VALIDATION-RETRY-20261001-001`
- Decider: 広瀬剛
- Source class: `RECORDED_DIRECT_CONVERSATION`
- Channel: Codex Work chat
- Message ID and exact receipt time: `UNKNOWN`
- Exact text: `AUTH-G6-PR00-VALIDATION-RETRY-20261001-001として、修正後の python -m pytest -q tests/test_run_execution_composition.py を追加1回、費用0円で実行することを許可します。`

## Effect and limits

This authorizes exactly one additional execution of:

`python -m pytest -q tests/test_run_execution_composition.py`

The authority applies only to the staged PR-00 Evidence source-binding repair after
review rejection. Cost remains 0 JPY. It does not authorize a second retry, PR-01,
service/browser, Day/Go, model, Watcher, credentials, G7/G8 or product acceptance.
