# AI-Control-Center G0〜G4 外部評価キット

評価キット ID: `ACC-G0-G4-EVAL-KIT-20260926-001`  
対象状態: `READY_FOR_DOCUMENT_REVIEW`  
作成目的: 別Workが、G0〜G4の**文書基線**を製品実装と混同せずに評価できるようにする。

## 1. 評価の前提

- 対象製品は、利用者が一つのLocalLLM-Lab Dayを選択してGoしたとき、AI-Control-Centerが安全・実施・修正／エスカレーション・証拠・停止・復旧を制御するWindows-firstのローカル運用面である。
- 評価対象はG0〜G4の計画・調査・要求・選定・制御設計の文書である。コードの品質、サービス稼働、Day実行、G5実装、モデル実行を評価又は開始しない。
- 現在の基線はローカル作業ツリー上の未コミット文書を含む。Git commitだけを根拠に「存在しない」と結論づけない。
- G0〜G4の文書基線とG4設計出口は受理済みである。ただし製品受入、G5、Day作業、サービス修復は未承認である。
- 現行の実サービス／watcherは動作証拠ではない。保存済み状態とlive listener不在の不一致は`BLOCKED`として記録されている。

## 2. 評価対象の正本と順番

以下を上から順に読む。パスはこのリポジトリのルート `C:\AI-Control-Center` からの相対パスである。

| 順番 | 文書 | 評価で担う役割 |
| --- | --- | --- |
| 1 | `docs/WORKING_RULES.md` | 運用上の優先順位、レビュー、証拠、停止境界 |
| 2 | `docs/CURRENT_WORK.md` | 現在の製品／Day作業の停止境界 |
| 3 | `docs/ai-control-center-gates/2026-09/PROJECT_PURPOSE_2026-09.md` | 製品目的と利用者価値 |
| 4 | `docs/ai-control-center-gates/2026-09/G0_AI_CONTROL_CENTER_PROJECT_2026-09.md` | 統治、役割、範囲、前提 |
| 5 | `docs/ai-control-center-gates/2026-09/G1_AI_CONTROL_CENTER_CURRENT_STATE_2026-09.md` | 現状、再利用資産、証拠の限界 |
| 6 | `docs/ai-control-center-gates/2026-09/G2_AI_CONTROL_CENTER_REQUIREMENTS_DRAFT_2026-09.md` | 目的・機能・非機能・受入要求 |
| 7 | `docs/ai-control-center-gates/2026-09/G2_REQUIREMENTS_TRACEABILITY_2026-09.md` | 要求→設計→将来証拠の追跡 |
| 8 | `docs/ai-control-center-gates/2026-09/G3_AI_CONTROL_CENTER_FEASIBILITY_2026-09.md` | 役割構成、候補、選定・代替・安全停止 |
| 9 | `docs/ai-control-center-gates/2026-09/G4_AI_CONTROL_CENTER_FUNCTIONAL_CONTROL_DESIGN_v2_2026-09.md` | 役割から制御・状態・証拠への具体化 |
| 10 | `docs/ai-control-center-gates/2026-09/G4_WALKTHROUGH_EXECUTION_PLAN_2026-09.md` | 選定手段の限定ウォークスルーと未実証範囲 |
| 11 | `docs/ai-control-center-gates/2026-09/G4_STANDARD_DESIGN_REVIEW_2026-09.md` | G4草案のレビュー記録と人間判断境界 |
| 12 | `docs/ai-control-center-gates/2026-09/G0_G4_STANDARD_APPLICATION_2026-09.md` | 現行運用標準への適用、テンプレート統合方針 |
| 13 | `docs/ai-control-center-gates/2026-09/G0_G4_STANDARD_APPLICATION_REPORT_CORRECTION_2026-09.md` | 時間・再確認・外部効果状態の訂正記録 |

補助資料（必要な場合だけ）:

- `docs/ENGINEERING_WORK_HISTORY.md` — 経緯の確認用。正本の代替にはしない。
- `docs/ai-control-center-gates/2026-09/prompts/G0_RESTART_ARTIFACT_PROMPT_2026-09.md` から `docs/ai-control-center-gates/2026-09/prompts/G4_CONTROL_DESIGN_PROMPT_2026-09.md` — 各成果物を作成した依頼の境界確認用。
- `C:\LocalLLM-Lab\docs\runbooks\work-plan-day1-14.md` — Dayの参照契約。Dayの実行指示ではない。

## 3. 別Workへ渡す評価依頼文

次の文をそのまま評価依頼に使用できる。

> `C:\AI-Control-Center\docs\G0_G4_EVALUATION_KIT_2026-09.md` の「評価対象の正本と順番」に従い、AI-Control-CenterのG0〜G4文書基線を評価してください。これは文書レビューであり、サービス起動、テスト、Day選択／Go、モデル実行、修復、Git変更、外部投稿を行わないでください。製品目的、要求から設計への追跡、G3の役割と候補比較、G4の役割→技術手段→証拠→停止／復旧の連続性、権限・安全・外部効果状態、未実証事項の表現を確認してください。各指摘には文書パスと見出し、分類、影響、最小の修正案を付けてください。問題がなければ、文書基線としての評価結果と、製品受入又はG5開始を意味しないことを明記してください。

## 4. 評価観点と期待する報告形式

| 観点 | 確認すること |
| --- | --- |
| 目的・スコープ | 「G0成果物を作る」ことではなくAI-Control-Centerを作る目的になっているか。文書基線と製品受入を分離しているか |
| 統治・権限 | 広瀬剛、Codex、ChatGPT、必要時のダッシュボード役の責任・判断境界が一貫しているか。ChatGPTのレビュー／検証兼務を独立確認と偽装していないか |
| 要求と追跡 | G2の安全・実施・自動修復／人間エスカレーション・証拠・停止・復旧が、G3/G4と将来証拠へ追跡できるか |
| G3選定 | 機能構成が個人名や製品名だけでなく役割で定義され、候補・選定基準・代替不能時の安全停止があるか |
| G4継続性 | G3の役割フローをG4状態遷移が置き換えず、役割→技術手段→根拠→未実証範囲がたどれるか |
| 安全・証拠 | fail-closed、同一Dayへの復帰、人間判断要求、レビュー相関、外部効果の状態が矛盾なく扱われるか |
| 事実状態 | `OBSERVED`、`REPORTED`、`UNKNOWN`、`NOT_EVALUABLE`、`BLOCKED`を、実動・製品受入の主張と混同していないか |
| 標準適用 | 運用標準の必要な問いを既存成果物へ統合し、不要な新規帳票を量産していないか |

報告は次の形に限定する。

| ID | 判定 | 分類 | 根拠（文書・見出し） | 影響 | 最小修正案 |
| --- | --- | --- | --- | --- | --- |
| E-01 | `PASS` / `ISSUE` / `NOT_EVALUABLE` | 矛盾 / 根拠不足 / 曖昧さ / 追跡欠落 / 境界逸脱 | パスと見出し | 文書基線への影響だけ | 変更が必要な最小の文書箇所 |

最後に、次の二つを別行で判定する。

1. `DOCUMENT_BASELINE: ACCEPT / ACCEPT_WITH_CHANGES / REJECT`
2. `PRODUCT_ACCEPTANCE_OR_G5_AUTHORIZATION: NOT_EVALUATED`

## 5. 禁止事項と評価の限界

- この評価キットだけでG5を開始、Dayを選択・実行、サービスを修復・起動してはならない。G4出口は広瀬剛の2026-09-28承認で完了済みである。
- 未実証の技術手段を、文書上の設計やfixtureだけで実稼働済みと評価しない。
- 既存の履歴、保存済みwatcher状態、過去Day結果を現在の稼働証拠へ昇格させない。
- 範囲外の旧文書や未追跡資産を全面監査しない。必要な不整合が見つかった時だけ、具体的なパスと理由を指摘する。

## 6. 評価完了の出口

評価は、上記の表と二つの最終判定を返した時点で終了する。指摘があっても、別Workは自動で文書や製品を変更しない。修正の実施は広瀬剛又は担当Workの別指示に従う。
