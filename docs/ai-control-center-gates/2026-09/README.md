# AI-Control-Center G0〜G5 文書基線（2026-09）

このディレクトリは、AI-Control-Center 製品を対象にした G0〜G5 の成果物を、
レビュー可能な一つの Git 基線として公開するためのパッケージである。
レビュー対象は本ブランチ上の**固定コミット**であり、ローカルの未コミット状態、
Review Bridge のコメント本文、製品実装の完了を意味しない。

## レビュー対象と読み順

レビュー時は、まずリポジトリ根の `docs/WORKING_RULES.md` と
`docs/CURRENT_WORK.md` を読み、次に以下の「現行正本」を番号順に読む。

| 工程 | 現行正本 | 補助・根拠 | 現在の境界 |
| --- | --- | --- | --- |
| G0 | `G0_AI_CONTROL_CENTER_PROJECT_2026-09.md` | `PROJECT_PURPOSE_2026-09.md`、`PROJECT_RESTART_PLAN_2026-09.md` | 製品目的、役割、統治の人間承認済み基線 |
| G1 | `G1_AI_CONTROL_CENTER_CURRENT_STATE_2026-09.md` | — | 読み取り調査・再利用判定。稼働や製品受入の証明ではない |
| G2 | `G2_AI_CONTROL_CENTER_REQUIREMENTS_DRAFT_2026-09.md` | `G2_REQUIREMENTS_TRACEABILITY_2026-09.md` | 要求・受入条件と将来証拠の対応 |
| G3 | `G3_AI_CONTROL_CENTER_FEASIBILITY_2026-09.md` | `STANDARD_G3_REVISION_SUGGESTIONS_2026-09.md` | 役割、候補、代替、停止条件の選定。G4以前の詳細設計はしない |
| G4 | `G4_AI_CONTROL_CENTER_FUNCTIONAL_CONTROL_DESIGN_v2_2026-09.md` | `G4_STANDARD_DESIGN_REVIEW_2026-09.md`、`G4_WALKTHROUGH_EXECUTION_PLAN_2026-09.md` | 機能・制御設計と観測補遺。製品E2Eや受入を主張しない |
| G5 | `G5_AI_CONTROL_CENTER_IMPLEMENTATION_PLAN_v2_2026-09.md` | `prompts/G5_IMPLEMENTATION_PLAN_PROMPT_v2_2026-09.md` | 実装前の最小作業カード。Reviewer確認待ちであり、G6・Day作業は未承認 |

横断して読む記録は、`G0_G4_STANDARD_APPLICATION_2026-09.md`、
`G0_G4_STANDARD_APPLICATION_REPORT_CORRECTION_2026-09.md`、および
`G0_G4_EVALUATION_KIT_2026-09.md` である。前二者は標準適用・報告訂正の記録、
後者は外部評価の読み方であり、個別工程の正本を置き換えない。

## プロンプトと履歴

`prompts/` には各成果物を作成・再実施したプロンプトを保存する。これらは来歴と
再現可能性のための入力であり、書かれた実行指示が現在の権限を自動的に発生させない。

`superseded/` には、目的訂正又は後続版によって正本から外れた成果物を保存する。
削除せず比較・監査には使えるが、現行の要求、設計、実装計画、実行許可の根拠には
使用しない。

## レビューと更新の運用

1. レビュワーは Review Bridge の依頼本文ではなく、指定されたブランチ名・コミットSHA・本ディレクトリ内の対象ファイルを読む。
2. レビュー報告には `REVIEWED_BRANCH`、`REVIEWED_COMMIT`、対象パス、成果物SHA-256を記録する。`IN_REPLY_TO` と単一の未解決 `REPORT_ID` の規則は `docs/WORKING_RULES.md` に従う。
3. 以後の未コミット成果物は、既存の作業や実行ログと混ぜず、目的別の `agent/*` ブランチで明示的にコミットする。`main` は人間が明示承認するまで読み取り専用である。
4. レビュー済み基線を変更する場合は、新しいコミットを固定し、変更対象のG・変更理由・前版との差分をレビュワーへ示す。古い成果物や証拠を削除して置換しない。

## この公開の非目的

本パッケージの commit/push は、製品実装、G6開始、Day選択・Go、モデル実行、
サービス操作、認証変更、費用発生、又は製品受入を許可・実施・証明しない。
