# G8 RG-02/RG-05/RG-07 Operating-Envelope Authority

## Authority identity

- **Authority ID:** `AUTH-G8-OPERATING-ENVELOPE-20261001-001`
- **Decision maker:** 広瀬剛
- **Source class:** `RECORDED_DIRECT_CONVERSATION`
- **Received through:** current Codex Work chat
- **Message ID / exact received time:** `UNKNOWN`
- **Record date:** 2026-10-01

## Exact human authority

> `AUTH-G8-OPERATING-ENVELOPE-20261001-001`として、RG-02・RG-05・RG-07を対象とする運用境界パックの作成・整合確認・Reviewer提出を許可します。
>
> 対象成果物は、固定済みローカル候補 `AI-Control-Center-Day6-Bounded-RC1`、source commit `656711367ed837ddbb75e6df65234a955e44900d`、archive SHA-256 `6453a213b0a48b827bbbc83ec2bdf1036515e6d857451473402cae3fb79f6714` とします。
>
> 固定する運用条件は次のとおりです。
>
> - 運用環境は広瀬剛が管理するローカルWindowsホストに限定する。
> - 利用者・運用責任者・停止判断者は広瀬剛とする。
> - 接続先は `127.0.0.1` のみとし、外部公開を禁止する。
> - 使用ポートは既定の `8000` とし、変更する場合は別途記録する。
> - 将来の展開先候補を `C:\AI-Control-Center\state\release-candidates\AI-Control-Center-Day6-Bounded-RC1` とする。ただし本権限では展開しない。
> - 実行状態とログは展開先配下の `state` および `logs` に保持する。
> - 原本ZIP、Manifest、受理記録は既存のControl Center管理領域に保持する。
> - 費用上限は0円とする。費用が不明なものを0円と扱わない。
> - 有料API・有料モデル・外部有料サービスの利用を禁止する。
> - 既存認証情報の変更、複製、成果物への収録を禁止する。認証が必要になった場合は停止して別途判断を求める。
> - 製品の既定実行モードは固定成果物の `mock` を維持する。real modeは別権限とする。
> - 証拠、状態、ログ、Manifestおよび受理記録は、候補が明示的に廃止・置換されるまで保持する。自動削除しない。
> - 計画・文書化はCodex、レビュー・検証はChatGPT、運用上限を超える事象の判断は広瀬剛が担当する。
>
> 作業範囲は、上記条件を正本へ記録し、RG-02・RG-05・RG-07との対応を示し、レビューパックを作成して公開ブランチへPushするところまでです。ACTIVE_WORKは15分以内、整合確認コマンドは最大2回、費用は0円とします。
>
> サービス起動、成果物展開、停止・ロールバック実行、Watcher操作、Day／Go、モデル実行、認証変更、外部公開、配布、RG-03、RG-04、RG-06およびリリース判断は許可しません。Reviewer提出後は `NO_RELEASE` のまま停止してください。

## Applied boundary

This authority permits documentation, static source/configuration consistency
inspection, review-pack preparation, commit and push only. It does not grant any
runtime or release effect.
