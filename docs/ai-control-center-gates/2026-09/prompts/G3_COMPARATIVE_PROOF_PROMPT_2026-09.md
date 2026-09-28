# G3 比較実証プロンプト — AI-Control-Center

文書 ID: `G3-ACC-PROMPT-20260925-001`  
作成日: 2026-09-25 (JST)  
ACTION_CLASS: `VALIDATION`

## 依頼

AI-Control-Center の G3 として、G2 で承認済みの二ケース比較を開始する。
対象は製品の制御・証拠・停止の実証であり、LocalLLM-Lab の研究結果の優劣を
評価しない。成果物は `docs/G3_AI_CONTROL_CENTER_COMPARATIVE_PROOF_2026-09.md`
とし、実施事項と簡潔なメモだけを記録する。

## 権限と固定条件

- 人間の責任者・最終受入者: 広瀬剛。2026-09-25 の「G3へ進みましょう」を
  G3開始の明示指示として扱う。
- 計画・実装: Codex。レビュー・検証: ChatGPT。ChatGPT は必要時だけ監視・要約を
  補助し、状態遷移・最終受入・人間判断を代行しない。
- C-01 は既終了の Day 1 を再実行しない参照事例である。source revision、契約又は
  runbook版、Evidence IDとvalidator結果、時刻、保存先が全て検証可能なときだけ
  `EVALUABLE` とする。欠ける場合は `NOT_EVALUABLE` と記録し、補完・推測・再実行を
  しない。
- C-06 は Day 6 の参照なし新規実証候補である。開始時の LocalLLM-Lab revision、
  Day 6契約/runbook hash、許可対象パス、run ID、時間、試行、費用、token出所を
  記録する。隔離された旧Day6状態は参照に採用しない。
- 各ケースは ACTIVE_WORK 30分以内、最大2試行、追加の有償操作0円。token上限は
  設けず、取得できた実測値だけを記録する。費用が必要と判明した時点で事前停止する。
- 画面操作は行わず、結果はこのチャットへ返す。G3比較の期限は本開始から3時間。

## 実施順序

1. 現行 `AGENTS.md`、`docs/WORKING_RULES.md`、`docs/CURRENT_WORK.md`、
   `docs/G2_AI_CONTROL_CENTER_REQUIREMENTS_DRAFT_2026-09.md`、Day 1–14 runbook、
   関連履歴、永続状態、Git状態を読む。
2. C-01の候補を読み取り専用で照合する。履歴完了表示や状態ファイルだけでは採用せず、
   上記の来歴要件を一つの reference record に結び付ける。証明できない要素を明示する。
3. C-06について、Day6が `TRUSTED_NOT_EXECUTED` であること、現在の契約・対象パス・
   Git状態・reviewer-bus・費用境界を確認する。現時点で実行可能か、外部／人間権限で
   停止すべきかを分類する。
4. この初回G3成果物は**事前判定まで**とする。Day6のコード変更、テスト、モデル起動、
   外部送達、Git変更は、事前判定と必要なレビュー応答の後にだけ開始する。
5. 完了又は判断境界では、現行方針の `PROGRESS_UPDATE` / `DECISION_REQUEST` /
   `COMPLETION_REPORT` を用いる。レビュー送受信は Review Bridge PR #1 とWatcherで
   行い、ChatGPT composerや人間のコピー＆ペーストを通常経路にしない。

## 不合格・停止条件

- C-01の来歴または条件互換性が未検証なら、比較基準として採用しない。
- Day6以外のDayの開始、未承認パスへの書込み、条件変更、費用発生、同一失敗の無変更
  再試行、モデル品質の「修復」は禁止する。
- report ID不一致、重複応答、認証不足、必要な外部権限不足は成功扱いにしない。
- `COMPLETE`、exit 0、静的画面、AI自己報告だけを受入証拠にしない。

## 出力に必須の項目

1. G3目的と今回の停止境界
2. C-01 reference record と `EVALUABLE` / `NOT_EVALUABLE` の根拠
3. C-06 preflight record と実行可否・停止理由
4. 固定条件、実行ID、試行・token・費用・手動中継・介入理由の記録方式
5. C-01/C-06の比較可能な項目と比較しない項目
6. 次の最小アクションと、その前に必要なレビュー又は人間判断

