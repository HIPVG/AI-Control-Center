# G3 — AI-Control-Center 比較実証・事前判定記録

文書 ID: `G3-ACC-20260925-001`  
G3開始記録: 2026-09-25T15:54:17+09:00  
比較期限: 2026-09-25T18:54:17+09:00  
ACTION_CLASS: `VALIDATION`  
状態: `SAFE_CHECKPOINT_REVIEW_PENDING`

## 1. 目的と今回の境界

G2で定めた二ケース比較を開始した。目的は研究結果の優劣ではなく、
AI-Control-Center が参照再利用あり／なしで、証拠・制御・停止を混同せず扱えるかを
確認することである。今回の成果物は C-01 の参照適格性と C-06 の開始前判定までである。
Day6のコード変更、テスト、モデル起動、外部送達、Git変更は実施していない。

| 固定条件 | 値 |
| --- | --- |
| 対象 | C-01: Day1既終了参照候補、C-06: Day6参照なし新規実証候補 |
| 上限 | 1ケース当たり ACTIVE_WORK 30分、最大2試行、追加の有償操作0円 |
| token / 費用 | token上限なし・実測のみ。今回のモデル呼出し0、有償操作0円 |
| 画面操作 | なし。結果はこのチャットへ返す |
| 手動AI中継 | 0回。レビューはReview Bridge PR #1 / Watcher経路 |

## 2. C-01 — Day1既終了参照候補

### 確認できた事項

- AI-Control-Center の履歴にはDay1の `DAY_COMPLETE` があり、直近の記録は
  2026-09-23T13:52:52+09:00、条件IDは
  `d1-repository_relationship`、`d1-preservation_audit`、
  `d1-documentation_consistency`、`d1-regression_baseline` である。
- LocalLLM-Lab には基準・引継ぎ文書が残る。現在の runbook SHA-256 は
  `F1B6B5A96D70C2B84CBDE3C1D378613B004A8E49233338584E54730DA10347D5`。

### 判定: `NOT_EVALUABLE`

G2で必須とした一実行単位の source revision、当時のDay1契約／runbook版、Evidence IDと
validator結果、実行時刻、保存先を、同一の検証済み reference record として結び付ける
一次資料は確認できなかった。履歴の完了表示・保存state・一般的な引継ぎ文書だけを
受入証拠にすることは禁止されているため、Day1を比較基準には採用しない。再実行や
推測による補完は行わない。

## 3. C-06 — Day6参照なし新規実証候補

### 現在の固定情報

| 項目 | 観測値 |
| --- | --- |
| LocalLLM-Lab branch / revision | `main` / `e33b0a410fb8647711f02ae4e6e0b66472e6eff0` |
| Day6 catalog | `TRUSTED_NOT_EXECUTED`、`day-06-temporal-state-design` |
| Day6目的 | planned / actual / forecast / snapshot timeを決定的に分離し、欠落time factをfail closedにする |
| 許可候補パス | `schemas/temporal-state.json`、`scripts/eval/temporal_state.py`、`tests/test_temporal_state.py`、`docs/architecture/temporal-state.md` |
| Day Runner specification SHA-256 | `69ACC407C9B4F2CDFA5A672CA51B54F16FD92EEBBEEAC3E8E8F3E08E96F1981B` |
| 現行Control Center保存状態 | Day4 `COMPLETE`、更新日時 2026-09-23T15:31:41+09:00。Day6のcurrent runtime証拠ではない |
| reviewer-bus | `running: true`、`available: true`、未処理のoutstanding reportなし |

### 判定: `GIT_BASELINE_UNRECONCILED` — Day6未開始

LocalLLM-Labの現在ブランチには、`.gitignore`、三つのbenchmark設定の変更と、
`conftest.py`、`pytest.ini`、finalizeスクリプト／テストの未追跡ファイルがある。
これらは既存の利用者作業であり、削除・reset・clean・取り込みをしてはならない。
Day6の許可候補パスとも一致しない変更を含むため、現時点でDay6を選択・Goすることは
安全な比較実証の開始にならない。過去の隔離Day6状態も参照に採用しない。

## 4. 比較可能な範囲

| 比較項目 | C-01 | C-06 |
| --- | --- | --- |
| 参照再利用 | 来歴不十分のため不採用 | 参照なし。新規証拠が必要 |
| 研究結果品質 | 比較しない | 比較しない |
| 製品の正しい動作 | 不足来歴を`NOT_EVALUABLE`へ停止 | 未整理Git状態を検出し、Day6を開始しない |
| 手動中継・費用 | 0回／0円 | 0回／0円 |

この時点で比較できるのは「根拠不足を成功にせず停止できる」という制御だけであり、
Day6の実施・自動修復・復旧までを実証したとは主張しない。

## 5. 次の最小アクション

ChatGPT reviewer に、C-01の`NOT_EVALUABLE`とC-06の保全停止がG2要求に適合するかを
レビュー依頼する。承認後も、Day6開始にはLocalLLM-Labの既存変更を保全したまま
実行基線をどのように確定するかの明示的な判断又は安全な既存手順が必要である。
費用発生、条件変更、既存作業の破棄を伴う方法へは進まない。

