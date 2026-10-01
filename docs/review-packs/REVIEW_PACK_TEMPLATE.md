# Review Pack: <PACK_ID>

## Identity

- `PACK_ID`: <一意なID>
- `GATE_TYPE`: `DESIGN | AUTHORITY | STAGE_ENTRY | COMPLETION | SECURITY | OTHER`
- `REVIEWED_BRANCH`: <branch>
- `REVIEWED_COMMIT`: <40桁SHA>
- `CREATED_AT`: <UTC ISO-8601>
- `PREPARED_BY`: `Codex Control Tower`

## Decision requested

<外部 Reviewer に求める判断を一文で書く。>

## Fixed review scope

- 対象パス: <固定コミット上のパス>
- 対象外: <明示的に除外する作業>
- 既存の権限・制約: <根拠パス又は人間指示>

## What changed or is proposed

<変更又は提案を、事実と推論を分けて簡潔に書く。>

## Evidence

| Claim | Evidence artifact | Result | Limitation |
| --- | --- | --- | --- |
| <主張> | <固定パス、コマンド結果、hash等> | <OBSERVED/REPORTED> | <限界> |

## Validation performed

- <実行した検証と結果>
- <実施していない検証と理由>

## Quality and residual gaps

- `ARTIFACT_QUALITY_CHECK`: `PASS | FAIL | NOT_APPLICABLE`
- 未解決事項: <なければ none>
- E2E 状態: `OBSERVED | NOT_OBSERVED | NOT_APPLICABLE`

## Minimum permitted next action

<承認時に許される最小の次の一手。>

## Why no broader action is requested

<対象外の実装、再設計、追加検証を求めない理由。>

