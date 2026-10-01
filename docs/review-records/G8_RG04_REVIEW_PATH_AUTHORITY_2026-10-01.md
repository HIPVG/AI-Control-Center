# G8 RG-04 Review-Path Validation Authority

- **Authority ID:** `AUTH-G8-RG04-REVIEW-PATH-VALIDATION-20261001-001`
- **Source class:** `RECORDED_DIRECT_CONVERSATION`
- **Human authority:** 広瀬剛
- **Message ID / exact receipt time:** `UNKNOWN`
- **Candidate:** `AI-Control-Center-Day6-Bounded-RC1`
- **Release state:** `NO_RELEASE`

## Exact instruction

> `AUTH-G8-RG04-REVIEW-PATH-VALIDATION-20261001-001`として、固定候補
> `AI-Control-Center-Day6-Bounded-RC1` のRG-04 Reviewer経路を限定検証することを
> 許可します。
>
> 検証対象は、現行のGitHub Review Bridge PR #1、Control Center管理下の
> Reviewer Bus Watcher、および管理領域の`CODEX_SQLITE_HOME`です。
>
> 許可する作業は次の範囲に限定します。
>
> - 一意のREPORT_IDを持つ無作用の検証報告を1件作成・送信する
> - Reviewerからの完全一致返信を取得する
> - Watcherがその返信だけを一度処理し、Codex継続を一度だけ開始することを確認する
> - 不一致・重複返信が適用されないことを既存fixtureまたは保存済み証拠で確認する
> - 送信、受信、相関、適用、継続結果および停止状態を機械可読な証拠として保持する
> - 検証終了後にWatcherを停止し、再起動登録がないことを確認する
> - RG-04成果物とレビューパックを公開ブランチへPushする
>
> 上限はACTIVE_WORK 20分、検証報告1件、Watcher起動1回・停止1回、費用0円とします。
> 既存認証のみを利用し、認証変更は行いません。
>
> Day／Go、モデル実行、製品状態変更、追加のサービス公開、成果物配布、RG-06、
> リリース判断、実装修正は許可しません。不具合が見つかった場合は状態と証拠を保持し、
> 修正を開始せず停止してください。完了後も`NO_RELEASE`を維持してください。

## Applied interpretation

The validation uses the fixed candidate's exact production Watcher and application
blobs, which match the current branch. Because the existing project Watcher registry
contains historical unfinished entries, the probe uses a create-only isolated
registry under managed project state. It does not erase, overwrite or reinterpret
the existing registry. The continuation still runs in `C:\AI-Control-Center` and the
production Watcher still binds it to
`C:\AI-Control-Center\state\codex-sqlite`.

The single live report is a no-effect correlation probe. Any unexpected request to
write a follow-up report is blocked by the validation harness and recorded as a
failure. No product action is authorized by a matching response.
