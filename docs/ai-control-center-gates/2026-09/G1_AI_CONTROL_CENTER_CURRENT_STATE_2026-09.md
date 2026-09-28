# G1 — AI-Control-Center 現状・再利用・差異記録

調査 ID: `G1-ACC-20260925-001`  
調査日: 2026-09-25 (JST)  
ACTION_CLASS: `DIAGNOSIS`  
状態: 読み取り調査済み。人間および必要な ChatGPT レビューの確認待ち。

## 1. 範囲、権限、読み方

本記録は、広瀬剛が承認した G0 の G1 境界と、2026-09-25 の「反映し、実施してください」という指示に基づく。目的は AI-Control-Center を作るために、既存資産の再利用可否と主経路の欠落を確定することである。G1 文書そのものを目的にはしない。また LocalLLM-Lab の Day を実行していない。

今回行ったのは、文書・コード・設定・保存状態・Git・限定的なプロセス／ポート情報の読み取りと、本成果物および履歴の保存だけである。実行しなかった操作は、テスト、アプリ・モデル・watcher の起動又は停止、Day の選択・Go・Smoke・Repair、外部投稿・API 呼出、課金、Git の add/commit/fetch/pull/push、状態初期化、未追跡資産の削除・移動である。

事実状態は次のように読む。

| 表記 | 意味 |
| --- | --- |
| `OBSERVED` | 今回、現在のローカル読み取りで直接確認した。 |
| `REPORTED` | 保存状態又は履歴にある報告。現在稼働・受入の証拠ではない。 |
| `INFERRED` | コード又は設定からの限定的な設計上の推論。実動の証拠ではない。 |
| `UNKNOWN` | 今回の安全な読み取りでは確認できず、推測で補わない。 |

読み取った優先入力は、最新の人間指示、`AGENTS.md`、`docs/WORKING_RULES.md`、`docs/CURRENT_WORK.md`、`C:/LocalLLM-Lab/docs/runbooks/work-plan-day1-14.md`、`docs/ENGINEERING_WORK_HISTORY.md`、G0／目的／再始動計画、Day Runner 仕様、構造基準、関連コード・設定・保存状態である。`docs/ARCHITECTURE.md` は Day 1–14 の遷移仕様としては superseded と明記されているため、ここでは構造上の参考に限った。Day Runner の正本は `docs/DAY_RUNNER_EXECUTION_SPEC.md` とした。

## 2. 基線と現状記録

| 領域 | 記録 | 事実状態 | 根拠 |
| --- | --- | --- | --- |
| 対象 | `C:\AI-Control-Center`、Windows-first のローカル制御面。Python / FastAPI / JSON 状態を前提とする。 | `OBSERVED` | `AGENTS.md`、`backend/app.py`、`docs/WORKING_RULES.md` |
| Git 基線 | 枝 `agent/autonomous-multitask-orchestration`、HEAD `7eda9c6b5c303409557971e7b4eec65fef25f75e`。origin は `HIPVG/AI-Control-Center`。ローカル追跡情報では `main` に対し ahead 17 / behind 5。同期はしていない。 | `OBSERVED` | 2026-09-25 のローカル Git 読み取り |
| 作業ツリー | 既存変更として `docs/ENGINEERING_WORK_HISTORY.md` の変更、および今回の目的・G0・G1文書／プロンプトを含む未追跡ファイルがある。旧 `.pytest-*` と状態ディレクトリの一部は status 読み取りで access denied 警告を返した。 | `OBSERVED` | 同上。既存資産は保全し、権限回復や削除はしない。 |
| サービス入口 | `scripts/start.ps1` は Python 3.12 を確認し、`backend.app:app` を `127.0.0.1:8000` で Uvicorn 起動する。`scripts/start_dev.ps1` は reload 起動用。 | `OBSERVED` | `scripts/start.ps1`、`scripts/start_dev.ps1` |
| 現在の稼働観測 | 2026-09-25 の限定した Python/Uvicorn プロセス照会と 8000/8001/8080 の listener 照会では一致を観測しなかった。これは全サービス停止の断定ではない。 | `OBSERVED` | 読み取り照会。起動・停止は未実施。 |
| 制御状態 | `state/control-center.json` は `local_llm_day_runner` を保持する。保存値は selected Day 4、`COMPLETE`、更新日時 2026-09-23 15:31:41 UTC。 | `REPORTED` | `state/control-center.json` |
| 実行準備性 | 同保存状態内に過去の runtime readiness 情報があるが、現在のモデル・資格情報・接続を証明しない。 | `REPORTED` / `UNKNOWN` | `state/control-center.json`。起動・実行は未実施。 |
| reviewer watcher | `state/reviewer-bus-watcher.json` は `running` / `available` の保存値と 2026-09-24 の poll 履歴を持つ。現在の watcher プロセス又は外部到達性は未確認。 | `REPORTED` / `UNKNOWN` | 保存状態、今回のプロセス照会 |
| 設定 | `config/projects.yaml` は `local_llm_lab` を `C:\LocalLLM-Lab` に対応付ける。Day program は `config/local_llm_day_program.yaml`、予算上限は `config/budget.yaml` にある。 | `OBSERVED` | 設定ファイル、`backend/orchestrator/engine.py` |
| トークン | `/api/token-usage` と engine の token usage 集計・予算判定は存在する。構成値は上限であり、今回の実使用量ではない。 | `OBSERVED` | `backend/app.py:60-63`、`backend/orchestrator/engine.py`、`config/budget.yaml` |

### 2.1 2026-09-26 標準適用の読取再確認

広瀬剛の「現行標準をG0〜G4へ適用する」明示指示に基づき、標準6.2・6.3のうち今回の文書再確認に
必要な読取だけを`DIAGNOSIS`として行った。これは非破壊でも検証的な再確認であり、
「検証なし」とは表現しない。書込試験・実行・権限修復は行っていない。

| 主体・資源 | 読取結果 | 事実状態 | 判断への影響 |
| --- | --- | --- | --- |
| Codex実行主体 | `azuread\広瀬剛`。workspace所有者は`AzureAD\広瀬剛` | `OBSERVED` | 文書編集の現在主体を識別できる。将来の子プロセス書込許可は別途実測が必要 |
| `state`保存領域 | 所有者は`HONEYBEE0001\CodexSandboxOffline` | `OBSERVED` | workspace所有者と異なる。書込・拒否の振る舞いを推測しない |
| live watcher/API | 起動設定のport `8000`と過去の監視port `8765`の両方でlistenerを観測できず、両方の`/api/reviewer-bus/status`は接続拒否 | `OBSERVED` | 保存済み`running: true`を現行稼働として扱わない。起動・修復は別権限 |
| watcher保存状態 | 最終応答`5829889939`、`running: true`の保存値 | `REPORTED` | G4レビュー応答の来歴には使えるが、live稼働の証拠には使わない |

`CONDITIONAL_REUSE`等は資産の再利用分類であり、標準1.6の作業状態ではない。現在のlive watcher到達性は
`UNKNOWN`ではなく、上記読取時点では`BLOCKED`として扱い、原因は未確認のままにする。

## 3. 主体・資源対応

| 主体 | 担当／操作 | 読取根拠 | 到達性・限界 |
| --- | --- | --- | --- |
| 広瀬剛 | 責任者・利用者・最終受入。目的、範囲、費用、権限、未解決事象の継続／縮小／停止を判断する。 | `docs/ai-control-center-gates/2026-09/G0_AI_CONTROL_CENTER_PROJECT_2026-09.md` | `OBSERVED`（承認記録）。システム内の権限実測はしていない。 |
| Codex | 計画・実装。構造化契約と制御本体を分離した範囲内で作業する。 | G0、`backend/orchestrator/engine.py` | `INFERRED`。実ランナー起動、外部認証、書込み権限は今回未検証。 |
| ChatGPT | Codex と独立したレビュー・検証。必要時はダッシュボード役として監視・要約のみを担う。兼務時は相互の独立検証にしない。 | G0、目的文書 | `OBSERVED`（役割定義）。実際のレビュー配送は未検証。 |
| Python 制御 | 状態遷移、Evidence Registry、スコープ、予算、Day API の決定的制御を担う。 | `backend/app.py`、`backend/control/local_llm_day_program.py`、`day_state_machine.py`、`evidence_registry.py`、`scope_guard.py` | `OBSERVED`（コード接続）。実動適合は未検証。 |
| LocalLLM | Day 契約上の研究対象又は限定的な提案役。研究失敗を実装修正と混同しない。 | Day Runner 仕様、`day_action_executor.py` | `INFERRED`。現在の実行可能性は `UNKNOWN`。 |
| reviewer watcher | Review Bridge のコメント取得、継続起動、状態保存を扱う実装。 | `backend/control/reviewer_bus.py`、`state/reviewer-bus-watcher.json` | `OBSERVED`（実装）だが、実運用は `UNKNOWN`。外部送信は未実施。 |

資格情報の具体値、外部アカウントの到達可否、OS ACL の詳細は読まず、`UNKNOWN` とした。未追跡の state、worktree、chat export、過去 browser E2E、`.pytest-*` は来歴確認まで `PRESERVE_ISOLATED` とする。

## 4. A01〜A06 主経路対応

| 条件 | 入口→下流→出口 | 現在の根拠 | 最重要異常系の扱い | 不足と分類 |
| --- | --- | --- | --- | --- |
| A01 Day選択・Go | `frontend/app.js` の Day 読込／選択／Go → `backend/app.py` の `/api/local-llm/days`、`/api/local-llm/day/start` → `ControlCenterEngine.local_llm_day_start` → `LocalLLMDayProgram.start` → 保存 snapshot／画面投影。 | `OBSERVED`（`frontend/app.js:139-208`、`backend/app.py:109-126`、`engine.py:743-753`、`local_llm_day_program.py:338-367`）。 | IDLE 以外、契約不一致、権限要求は controller の状態・分岐で扱う。 | 現在の本番相当の起動・結果・復帰は `UNKNOWN`。`CONDITIONAL_REUSE`。 |
| A02 計画・証拠・判定 | `_execute` → 契約 fingerprint／inventory／Evidence Registry → criteria 評価・gap diagnosis → snapshot。 | `OBSERVED`（`local_llm_day_program.py:713-891`、`evidence_registry.py`）。 | unknown evidence は fail closed、不足証拠は診断・回復へ分解する。 | 実際の全条件での Evidence Registry 適合は未検証。`CONDITIONAL_REUSE`。 |
| A03 許可内の修正・再検証 | gap 分類 → action registry／`DayActionExecutor` → scope・Git・予算保護 → 再収集／再判定。 | `OBSERVED`（`day_action_executor.py`、`scope_guard.py`、`day_git.py`、controller の action 分岐）。 | 研究対象の失敗は repair に混ぜず、範囲外・外部権限は authority 経路へ渡す設計。 | 実行権限、LocalLLM 実環境、repair の通し検証は `UNKNOWN`。`CONDITIONAL_REUSE`。 |
| A04 レビューと停止 | app 起動時 watcher → Review Bridge 状態／イベント → UI status。選択 Day の terminal state で停止し自動次 Day はしない。 | `OBSERVED`（`backend/app.py`、`reviewer_bus.py`、Day Runner 仕様）。 | 重複・不一致 report、送信失敗は watcher の state／fail-closed 分岐で扱う設計。 | 現在の watcher 稼働と外部配送は `UNKNOWN`。保存済み `running` は実証でない。`CONDITIONAL_REUSE`。 |
| A05 実状態ダッシュボード | 1 秒間隔の `/api/local-llm/day/status` と reviewer status → Day、状態、進捗、条件、修正、handoff、result、smoke を render。 | `OBSERVED`（`frontend/app.js:83-112, 114, 192-208`、`LocalLLMDayProgram.view`）。 | server 側 control matrix が可能操作を投影する。画面の request 中表示は server state 単独ではない。 | 同一 run ID の保存状態・証拠との画面照合は通し未検証。可視 UI は token／費用／手動中継回数を表示しない。`CONDITIONAL_REUSE`。 |
| A06 成果・中継・費用の検証 | Day 完了 snapshot／Evidence Registry／token usage API・engine 集計が候補。 | `OBSERVED`（`state/control-center.json` の過去 Day 4、`backend/app.py:60-63`、engine token 集計）。 | 証拠が不足すれば completion を認めず、具体的 gap を診断する。 | 保存 Day 4 は現在成果の証拠ではない。手動中継回数・介入理由の記録資産、UI 上の token／費用・試行数表示は確認できない。`UNMAPPED`（計測表示部分）と `CONDITIONAL_REUSE`（証拠／集計部分）。 |

## 5. 再利用判定

| 資産 | 判定 | 根拠 | 採用条件・扱い |
| --- | --- | --- | --- |
| FastAPI 入口、JSON state store、起動スクリプト | `CONDITIONAL_REUSE` | API・loopback 起動・状態永続化の接続を読取済み。 | 起動・再起動・状態整合を将来の検証で示すまで実動済みとしない。 |
| LocalLLM Day controller、状態機械、Evidence Registry | `CONDITIONAL_REUSE` | 選択 Day、typed evidence、fail-closed のコード経路を読取済み。 | 正本仕様との差分と選択 Day の実証を G3 以降で確認する。 |
| scope / Git / budget guard、Day action executor | `CONDITIONAL_REUSE` | 保護構造と action 分離を読取済み。 | 変更を伴う経路は別途の明示承認と決定的検証が必要。 |
| reviewer bus と watcher 状態 | `CONDITIONAL_REUSE` | 実装と過去状態はある。 | 実際の認証・配送・重複防止を、外部作用を伴う検証として別承認で確認する。 |
| frontend Day dashboard | `CONDITIONAL_REUSE` | A01/A05 の表示・API 利用を読取済み。 | 現状態との UI 照合、A06 メトリクス要求を満たす拡張要否を G2 で定義する。 |
| `state/control-center.json` の Day 4、browser E2E status、履歴の過去成功報告 | `REFERENCE_ONLY` | 過去の保存・報告であり current runtime proof ではない。 | 互換性を検証できる場合だけ retained evidence 候補として扱う。 |
| 未追跡 state、worktree、chat export、`.pytest-*` | `PRESERVE_ISOLATED` | 来歴・所有者・安全な読取範囲が未確定。一部にアクセス警告あり。 | 削除・移動・採用をせず、必要性が生じた時だけ個別に権限を得る。 |
| 手動中継回数／介入理由の記録、token・費用・試行数の A06 向け画面表示 | `UNMAPPED` | 該当の visible frontend 接続を確認できなかった。 | G2 で測定定義、保存単位、表示条件、個人情報・費用の扱いを決める。 |

## 6. 差異・欠落一覧

| 優先度 | 差異／欠落 | A条件 | 事実状態 | 次の行為分類 |
| --- | --- | --- | --- |
| P1 | 現在の実サービス、watcher、外部到達、LocalLLM 実行可能性は証明されていない。保存値を current と誤認できない。 | A01, A03, A04, A05, A06 | `OBSERVED` / `UNKNOWN` | `DIAGNOSIS`、必要なら `AUTHORITY` |
| P1 | A05 の画面状態と同一 run ID の保存状態・証拠を end-to-end で照合した根拠がない。 | A05 | `UNKNOWN` | 将来の `VALIDATION` |
| P1 | A06 が求める手動中継回数・介入理由、費用／token／試行数の一貫した記録・画面表示を確認できない。 | A06 | `OBSERVED`（未接続） / `UNKNOWN` | G2 の `DIAGNOSIS`、将来の `IMPLEMENTATION` / `VALIDATION` |
| P2 | 保存済み Day 4 `COMPLETE` と、CURRENT_WORK が求める人間選択・Go の current boundary が混同され得る。 | A01, A05, A06 | `REPORTED` / `OBSERVED` | `DIAGNOSIS`。保存状態の意味と表示ラベルを G2 で定義する。 |
| P2 | reviewer bus の実装は存在する一方、現在の安全な読取では live transport を確認できない。 | A04 | `OBSERVED` / `UNKNOWN` | 将来の `VALIDATION`。外部作用時は `AUTHORITY`。 |
| P2 | Codex／ChatGPT／人間の役割は G0 で定義済みだが、OS・資格情報・外部アカウントの実権限は未測定。 | A03, A04 | `OBSERVED` / `UNKNOWN` | `AUTHORITY` を伴う限定 `DIAGNOSIS` |
| P3 | `docs/ARCHITECTURE.md` が構造基準である一方、Day Runner 遷移の正本ではない。旧計画・旧画面を正本扱いするドリフトを防ぐ必要がある。 | A01-A06 | `OBSERVED` | G2 の `DIAGNOSIS`（正本・用語・受入対応表） |

不足証拠は、G1の読み取りを止める理由ではない。上表は completion を自己宣言せず、次に何を安全に判断すべきかを示す。ここから実装修正・テスト・外部操作を始めない。

## 7. G1 出口判定案

**提案: 条件付きで G2（要件・受入定義）へ渡せる。**

**承認記録:** 2026-09-25、承認者: **広瀬剛**。対象: 上記の G1 出口判定および G2「目的・要求定義」への移行。この承認は G2 の要求定義作成を許可するが、G3 の実環境調査、製品実装、テスト、Day 実行、アプリ／モデル起動、外部送達、費用発生、Git 操作、状態初期化を許可しない。

理由は、A01〜A06 に対する現行の入口、下流、保存先、主な安全機構、再利用候補、そして「実運用の証拠がない」範囲を特定できたためである。一方、G1 はアプリ実動・外部 transport・モデル起動を検証しておらず、それらを G1 の完了根拠にはしない。G2 が解くべき未決事項は次だけである。

1. 最初の実証 Day の範囲、Day 1〜14 の最終範囲、各々の受入証拠を分離すること。
2. A05/A06 の run ID、証拠、手動中継・介入、token／費用／試行を、どの保存単位・保護条件・画面表示で扱うかを定義すること。
3. 保存済み historical state と current runtime state の表示・API の意味を定義すること。
4. 外部レビュー、資格情報、実ランタイムを検証する前提権限と、失敗時の停止・人間判断境界を定義すること。

この出口判定は、G2、実装、Day 実行、外部検証の開始許可ではない。広瀬剛の確認と必要な ChatGPT レビューが必要である。

## 8. 自己確認

- G0 の読み取り・成果物保存・履歴追記の境界を超えていない。
- A01〜A06 の各行に入口、下流、根拠、異常系、不足、再利用分類を記録した。
- 保存された Day 4／watcher 値を現在の稼働・受入の証拠として扱っていない。
- 再利用候補を採用済み・実動済み・受入済みと記載していない。
- ChatGPT のレビュー／検証兼務の独立性限界、ダッシュボード補助の制約、広瀬剛の最終判断を反映した。
- テスト、起動、Day、外部操作、Git 操作、状態初期化、未追跡資産の処理を実施していない。
