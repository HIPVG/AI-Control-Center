# Day 7–14 運用手順書

## 1. 目的と適用範囲

この手順書は、AI Control Centerを使ってLocalLLM-LabのDay 7〜14を一日ずつ実施し、
その過程でControl Centerを改善するための通常運用を定める。

対象は開発用の正本ワークスペース `C:\AI-Control-Center` である。限定ローカルリリース済みの
`AI-Control-Center-Day6-Bounded-RC1` はDay 6実証用の固定成果物であり、Day 7〜14の開発・
検証には使わない。固定RC1のファイルを更新してはならない。

この文書は操作手順であり、それ自体は次を許可しない。

- Dayの選択またはGo
- real mode、モデル実行、費用発生
- 認証変更、外部公開、配布
- Gitの破壊操作
- 人間専有の製品判断

各Dayの実行前に、対象Day、基線、回数・時間・費用上限を含む広瀬剛の明示的な権限を記録する。

## 2. 構成と責任

通常経路は次のとおりである。

```text
広瀬剛
  └─ ブラウザーUI（Day選択、Go、状態確認、必要時の停止）
       └─ AI Control Center / FastAPI（127.0.0.1:8000）
            ├─ Day実行・Evidence・状態・telemetry
            └─ Reviewer Bus Watcher（同じサービス内で起動、約120秒間隔）
                 └─ GitHub Review Bridge PR #1
                      └─ ChatGPT Reviewer Task（GitHubイベントで起動）
                           └─ 完全一致する返信
                                └─ WatcherがCodexを一度だけ継続
```

| 役割 | 担当 | 主な責任 |
|---|---|---|
| 利用者・運用責任者・例外判断 | 広瀬剛 | Day権限、上限超過、新規認証・費用・製品判断 |
| 計画・実装・記録 | Codex | 現行規則とDay契約に従う作業、証拠、報告 |
| レビュー・検証 | ChatGPT Reviewer Task | 報告の評価、最小十分な次指示、完了判定 |
| 搬送・継続起動 | Reviewer Bus Watcher | PR取得、完全一致相関、重複防止、Codex継続 |

WatcherとReviewer Taskは別物である。Watcherはローカルサービスに含まれ、Reviewer Taskは
GitHubイベントで起動する。Windowsの定期タスクや時刻ベースのChatGPT監視は通常運用に使わない。

## 3. 一度だけ行うReviewer Task設定

### 3.1 GitHub側の固定値

- Repository: `HIPVG/AI-Control-Center-Review-Bridge`
- Pull request: `#1`
- Trigger: PR #1へ追加されたトップレベルConversationコメント
- 対象条件: 行頭に `REPORT_TYPE:` を持つ新規コメント
- 正本プロンプト: PR #1の現在のhead branchにある
  `poc/reviewer-task-prompt.md`

2026-10-02確認時のPR headは
`poc/review-loop-report-types-20260924` / `4a06e00c93f70e564cbbce9092e04490d84dbae9`
である。この値をTaskへ固定せず、毎回現在のPR headを確認する。

### 3.2 Taskの種類

GitHubコメントを契機とするイベントTaskとして作成し、有効化する。定期実行、時刻ベースの監視、
ChatGPT composerへの自動入力は設定しない。

### 3.3 Taskのプロンプト欄

Taskのプロンプト欄には、長い運用規則を複製せず、次のブートストラップだけを設定する。
実際の判断規則はリポジトリ上の正本を毎回全文取得する。

```text
あなたはAI Control CenterのReviewer Taskです。

HIPVG/AI-Control-Center-Review-BridgeのPR #1に新しいトップレベルConversationコメントが追加されたGitHubイベントでのみ動作してください。時刻ベースの監視や自発的なポーリングはしません。

起動のたびに、PR #1の現在のhead branchを確認し、同branchのpoc/reviewer-task-prompt.mdを全文読み、その最新版だけをReviewer動作の正本として厳守してください。必要に応じて、報告が指定するPOLICY_COMMITのHIPVG/AI-Control-Center/docs/WORKING_RULES.md、docs/CURRENT_WORK.md、固定成果物と証拠を読みます。読めない資料を読了扱いにしません。

処理対象は、今回のイベントを発生させた正式なトップレベルコメントのうち、行頭にREPORT_IDとREPORT_TYPE: PROGRESS_UPDATE、DECISION_REQUEST、COMPLETION_REPORTのいずれかを持つものだけです。既存のIN_REPLY_TOを確認し、同じREPORT_IDへ二重返信しません。対象外または処理済みならPRへ投稿しません。

返信が必要な場合は、保存プロンプトで指定されたtransportと形式に従い、対象REPORT_IDへ一度だけ応答し、投稿またはファイル作成後に読戻し確認を行ってください。通常のレビューは既存権限内で進め、人間判断か実際の障害が必要な場合だけWorkチャットへ通知してください。人間を通常のコピー・貼付中継役にしません。

最終応答では、対象REPORT_ID（なければ対象なし）、処理結果、次に待つもの、PR書込み時は読戻し確認の有無を一文で示してください。
```

### 3.4 設定確認

Task設定後は次を確認する。

1. Taskが有効である。
2. 接続先が上記Repository / PR #1である。
3. 起動条件が新規トップレベルコメントである。
4. プロンプトが現在のPR headから正本を読む構成である。
5. スケジュール監視が設定されていない。

通常起動のたびに試験コメントを投稿する必要はない。実配送試験は、固有のREPORT_ID、無作用の
期待結果、回数上限、停止条件を持つ明示的な検証権限がある場合だけ行う。

## 4. 起動前チェック

### 4.1 Day権限

次を一つの権限記録として確定する。

- 対象Day（7〜14の一つ）
- Control Centerの対象commit
- LocalLLM-Labの承認済み基線・対象commit
- ACTIVE_WORK上限、Go回数、モデル試行回数、token・費用上限
- 使用モード（既定は`mock`。`real`は別の明示権限）
- 許可する外部操作、認証、Reviewer経路
- 失敗時の停止点と証拠保持

選択だけでは権限は付与されず、過去Dayの権限を次のDayへ流用しない。

### 4.2 ワークスペース

PowerShellで次を確認する。

```powershell
Set-Location C:\AI-Control-Center
git status --short
git branch --show-current
git rev-parse HEAD
```

既存の変更や未追跡ファイルは利用者の作業として保持する。自動削除、reset、checkoutによる
巻戻しを行わない。Dayの入場条件がclean基線を要求する場合は、既存作業を保存した新しい隔離
worktreeを使い、対象パスとcommitを権限記録へ固定する。

### 4.3 実行環境

```powershell
python --version
gh auth status
Get-Command codex
Get-Command gh
```

- Pythonは3.12系を使う。
- `gh`と`codex`の両方が解決できなければWatcherは利用不可となる。
- 認証変更が必要なら、その場で止めて広瀬剛の判断を求める。
- デスクトップCodexの状態DBを流用しない。Watcherは
  `C:\AI-Control-Center\state\codex-sqlite` を`CODEX_SQLITE_HOME`として自動設定する。

### 4.4 設定

trackedの`config/runtime.yaml`を通常運用の都合で書き換えない。ローカル差分が必要な場合は
ignoredの`config/runtime.local.yaml`を使う。`real`、有料API、有料モデル、外部サービスは
対応する明示権限がある場合だけ設定する。

## 5. Control CenterとWatcherの起動

### 5.1 通常起動

Day 7〜14の運用では、再読み込みを伴わない通常ランチャーを使う。

```powershell
Set-Location C:\AI-Control-Center
& .\scripts\start.ps1 -Port 8000
```

このPowerShellウィンドウを開いたままにする。サービスは`127.0.0.1:8000`だけで待受け、
FastAPIの起動時にReviewer Bus Watcherも同じプロセス内で開始する。Watcherだけを別に起動する
通常手順はない。

開発中に自動再読み込みが本当に必要な場合だけ、実行中Dayがない安全な境界で次を使う。

```powershell
& .\scripts\start_dev.ps1 -Port 8000
```

自動再読み込みはプロセス再生成を伴うため、Day実行・Reviewer応答適用中には使わない。

### 5.2 Watcher無効化フラグ

起動元のPowerShellで`AI_CONTROL_CENTER_DISABLE_REVIEWER_BUS=1`が設定されていると、
Watcherは`DISABLED_BY_ENV`で停止する。過去の一時停止設定を解除してよい権限がある場合だけ、
起動前にそのPowerShellプロセスから削除する。

```powershell
Remove-Item Env:AI_CONTROL_CENTER_DISABLE_REVIEWER_BUS -ErrorAction SilentlyContinue
```

ユーザー環境変数やシステム環境変数を永続変更しない。

### 5.3 起動確認

別のPowerShellで次を実行する。

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/operation/health |
    ConvertTo-Json -Depth 10

Invoke-RestMethod http://127.0.0.1:8000/api/reviewer-bus/status |
    ConvertTo-Json -Depth 20
```

Watcherの正常条件は次のとおりである。

- `running: true`
- `available: true`
- `poll_seconds: 120`
- `last_poll_at`が約2回分の間隔より古くない
- `last_error`が空

起動直後は最初の取得まで待つ。`running=true`だけで配送成功やCodex継続成功とは判定しない。

## 6. UIの操作

ブラウザーで `http://127.0.0.1:8000` を開く。

### 6.1 操作前に見る場所

1. **Reviewer Bus**が「Watcher稼働中」である。
2. **Run status**に前回runの状態、run ID、Day、blocker、次の操作が表示される。
3. 未完了のレビュー待ち、人間判断待ち、継続失敗がない。
4. Day一覧で対象Dayの契約、必要Evidence、入場条件を確認する。

表示が「取得時刻が古い」「Watcherエラー」「Watcher停止」「Watcher利用不可」の場合はGoしない。

### 6.2 Day選択

Day selectorで権限記録と同じDayを一つ選ぶ。選択だけではリクエストもDay実行も発生しない。
対象Day、目的、必要Evidence、現在の不足を読み合わせる。

Day 7〜14の目的は、正本runbook
`C:\LocalLLM-Lab\docs\runbooks\work-plan-day1-14.md` と
`config/local_llm_day_program.yaml`の現在版で確認する。UI表示だけで契約を変更しない。

### 6.3 Smoke

Smokeは選択Dayの設定・前提を限定確認する補助手段であり、Day完了証拠ではない。権限範囲に
含まれる場合だけ一回実施し、結果とEvidenceを確認する。失敗をGoで上書きしない。

### 6.4 Go

1. 対象Dayと上限をもう一度照合する。
2. **Go**を一回だけ押す。
3. 生成されたrun IDを記録する。
4. Run statusのadmission、state、blocker、Evidence、attempt、token、費用を追跡する。
5. ボタン連打やブラウザー再送をしない。

Goは選択Dayだけを送信する。Git、契約、権限、外部前提、上限はserver側が判定し、不明なら
fail-closedで停止する。`PREFLIGHT`は完了ではない。

### 6.5 状態ごとの扱い

| 表示状態 | 運用上の扱い |
|---|---|
| `PREFLIGHT` / 実行中状態 | 同じrunを観測する。追加Goしない |
| `EXTERNAL_ACTION_REQUIRED` | 外部前提または認証等を特定し、人間判断まで停止 |
| `HUMAN_ACTION_REQUIRED` | 判断対象・効果・制限を一件にまとめて広瀬剛へ提示 |
| `REVALIDATING` | 許可済みの限定再検証を待つ。新しい修正を足さない |
| `COMPLETE` | Evidence、telemetry、Reviewer受理を照合。次Dayを自動開始しない |
| `FAILED_UNRECOVERABLE` / `FAILED` | 状態と証拠を保持し、原因分類後に停止 |
| `STOPPED` | 停止理由と同一runの再開条件を確認 |

**Resume**は同一runの許可済み復帰先が表示されている場合だけ使う。**修復＆GO**は、限定修復の
scope・回数・時間が権限記録にあり、現在runがその復帰条件を満たす場合だけ使う。画面の
**Git Push**が無効な間は手動Pushの代替許可ではない。

## 7. Reviewer経路の通常動作

1. Codexが固有の`REPORT_ID`を持つ報告をPR #1へ一件公開する。
2. Codexは安全なcheckpointで現在turnを終了し、PRを自分でポーリングしない。
3. GitHubイベントでReviewer Taskが起動し、現在の正本プロンプトに従って一度だけ返信する。
4. Watcherが約120秒ごとにPRを取得する。
5. `IN_REPLY_TO`が未完了reportと完全一致する返信だけを適用する。
6. Watcherは管理領域の`CODEX_SQLITE_HOME`を使い、新しいbounded Codex turnを一度だけ開始する。
7. UIのReviewer Bus欄で受付、応答、適用、継続結果を確認する。

人間は通常のコピー・貼付中継を行わない。新しいコメントが古い未完了reportを取消すこともない。
複数reportはREPORT_IDごとに独立して相関し、Codex継続は直列化される。

報告公開から10分を超えて完全一致返信がない場合は、追加報告や手動適用を始めず、Taskの有効状態、
イベント対象、PR head、対象REPORT_IDを確認する。transport障害として証拠を保持する。

## 8. Day 7〜14の反復手順

各Dayを次の順序で一つずつ扱う。

1. 前Dayの完了記録とReviewer受理を確認する。
2. 次Dayの契約と必要Evidenceを読む。
3. 広瀬剛が対象Dayと実行上限を明示的に許可する。
4. Codexが権限記録、基線、実行計画を固定し、必要なレビューを得る。
5. 本手順の起動前チェックを行う。
6. Control Center / Watcher / Reviewer Taskの三者が利用可能であることを確認する。
7. UIで対象Dayを選択し、許可回数内でGoする。
8. 同一run IDの状態、Evidence、telemetry、レビューを保存する。
9. 修正が必要なら原因を分類し、既存権限内の限定修正か人間判断かを分ける。
10. Day完了時は`ARTIFACT_QUALITY_CHECK: PASS`を含む完了報告をレビューへ送る。
11. Reviewer受理後も、広瀬剛の次Day権限までは停止する。
12. そのDayで見つかったControl Centerの改善点は、Day成果と混ぜず、設計・fixture・製品再検証を分けて記録する。

同種のcross-component不具合が繰り返される場合は小修正を連続させず、G4/G5相当の統合設計と
ゲート方法を見直す。

## 9. 停止と終了

### 9.1 Dayの停止

実行中Dayを止める必要がある場合はUIの**Stop**を一回押し、同一runの停止状態と理由を読み戻す。
ブラウザーを閉じるだけではDay停止の証拠にならない。

### 9.2 Control CenterとWatcherの停止

Day処理とReviewer継続が動いていない安全な境界で、起動に使ったPowerShellウィンドウへ
`Ctrl+C`を一回入力する。FastAPI shutdownとともにWatcherも停止する。

停止後、別PowerShellで次を確認する。

```powershell
Test-NetConnection 127.0.0.1 -Port 8000
```

`TcpTestSucceeded: False`を確認する。対象PIDを確認せずにprocessを一括終了しない。通常運用では
WatcherやControl CenterをWindows Scheduled Taskへ登録しない。

## 10. 障害時の切分け

| 症状 | 最初の確認 | 対応 |
|---|---|---|
| UIを開けない | 起動PowerShell、port 8000 | 起動失敗ログを保持し、重複起動や別listenerを確認 |
| `Watcher停止` / `DISABLED_BY_ENV` | 起動shellの環境変数 | 意図的停止か確認。権限がある場合だけ一時変数を外して再起動 |
| `Watcher利用不可` | `Get-Command gh`, `Get-Command codex` | 不足を記録。インストールや認証変更は別判断 |
| GitHub取得エラー | `gh auth status`、network、`last_error` | 同じ操作を無変更で繰り返さない。認証変更前に停止 |
| Reviewerが反応しない | Task有効、trigger、PR head、REPORT_ID | 10分でtransport障害として記録。人間中継へ切替えない |
| 返信済みだが適用されない | `IN_REPLY_TO`、registry state、重複・不一致 | 古い返信を別reportへ適用しない。失効理由を保持 |
| Codex継続失敗 | exit code、envelope、後続効果 | exit 0だけを成功にしない。Watcher状態を手編集しない |
| UIの状態が古い | `/api/local-llm/runs`とstatus API | 再読込し、永続RunRecordとAPIを優先。追加Goしない |
| 費用が`UNKNOWN` | telemetryのsource/reason | 0円へ読み替えず停止条件と照合 |

`state/reviewer-bus-watcher.json`やRunRecordを手作業で削除・上書きして復旧しない。修正は再現可能な
ロジックとfixtureを通し、実運用再起動・配送・製品再検証を別々の証拠として扱う。

## 11. 開始・終了チェックリスト

### 開始

- [ ] 対象Dayと権限記録が一致している
- [ ] `docs/WORKING_RULES.md`、`docs/CURRENT_WORK.md`、runbookを再読した
- [ ] Control CenterとLocalLLM-Labのcommit・Git状態を記録した
- [ ] Python 3.12、`gh`、`codex`が利用可能である
- [ ] Reviewer Taskが有効で、PR headの正本プロンプトを読む
- [ ] Watcherが`running=true`、`available=true`、エラーなしである
- [ ] UIの対象Day、run、blocker、上限を確認した
- [ ] Go回数・モデル試行・費用上限を再確認した

### 終了

- [ ] 同一run IDの最終状態を読み戻した
- [ ] Evidence、telemetry、ログ、hash、Reviewer相関を保持した
- [ ] 失敗・未知値・未評価項目を成功へ昇格していない
- [ ] 完了報告のReviewer結果を記録した
- [ ] 次Dayを自動開始していない
- [ ] Dayを停止し、その後にControl Center / Watcherを停止した
- [ ] port 8000が非listenであることを確認した
- [ ] 未コミットの利用者作業を保持した

## 12. 正本参照先

- `AGENTS.md`
- `docs/WORKING_RULES.md`
- `docs/CURRENT_WORK.md`
- `docs/DAY_RUNNER_EXECUTION_SPEC.md`
- `docs/ARCHITECTURE.md`
- `C:\LocalLLM-Lab\docs\runbooks\work-plan-day1-14.md`
- `config/local_llm_day_program.yaml`
- `scripts/start.ps1`
- `backend/control/reviewer_bus.py`
- Review Bridge PR #1 current head: `poc/reviewer-task-prompt.md`

相違がある場合は、最新の人間指示、`docs/WORKING_RULES.md`、`docs/CURRENT_WORK.md`、対象Dayの
正本runbookの順で権限と現在作業を確定し、矛盾を隠さず停止する。
