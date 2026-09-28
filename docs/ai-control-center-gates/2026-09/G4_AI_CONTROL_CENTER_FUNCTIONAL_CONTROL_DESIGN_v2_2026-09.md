# G4 再実施 — AI-Control-Center 機能・制御設計 v2

- 文書ID: `G4-ACC-FUNCTIONAL-DESIGN-20260928-001`
- 状態: `REVISED_REVIEW_PENDING`（承認済みv2基線・観測補遺の来歴は保持。12節の版固定と13節の承認対象・再確認設計は改訂としてレビュー待ち）
- 行為分類: `DIAGNOSIS`
- 設計担当: CODEX
- 人間の責任者・最終判断: 広瀬剛
- レビュー／検証: ChatGPT（兼務時は独立検証と表示しない）
- 旧版: `G4-ACC-20260925-001`。旧版とその2026-09-28承認は保全する。本書は、G5で機能設計を補ってしまった差異をG4へ戻す改訂案である。

## 1. 目的・範囲・境界

目的は、G0の製品目的を満たすために必要な機能経路を実装前に固定することである。すなわち、利用者が一つのLocalLLM-Lab Dayを選択してGoした後、計画・実施・証拠判定・許可内の修正・レビュー・同じDayへの再開をつなぎ、同じrunの証拠付き結果又は停止理由を示す。

本書は、G0〜G3で確定した役割、M01主候補、M04の条件付き代案、M05安全停止を維持する。製品コード、テスト、Day選択／Go、モデル実行、外部投稿、費用発生、Git変更は行わない。旧G5実装計画は`SUPERSEDED_BY_G5_V2`として保全し、本書を正本にG5を再作成する。

## 2. 入力と設計上の決定

| 入力 | 設計への適用 |
| --- | --- |
| G0 P01〜P08 | 通常経路の手動中継削減、一DayだけのGo、証拠、修正、可視化、費用・試行を製品機能として扱う。 |
| G1 | 既存UI/API/Day制御/Evidence/Watcherは`CONDITIONAL_REUSE`。保存値をlive稼働・受入証拠にしない。dirty Gitと実効権限はpreflightでfail-closedにする。 |
| G2 A01〜A06/NFR | A01〜A06を機能責務として定義し、NFR-02のGo前境界とNFR-03のcurrent/historical・重複防止を制御要件にする。 |
| G3 | M01を主経路、M04をM01実actor不成立時だけの再評価候補、M05を必須安全停止とする。人間判断→レビュー確認→同一DayのPREFLIGHT復帰を維持する。 |
| 旧G4 | W01〜W04のfixture根拠は限定範囲だけ再利用する。UI、実修正成功、全Evidence型、実actor再起動横断、M04は未実証のままとする。 |

## 3. 機能構成・責務・信頼境界

| 機能責務 | 所有者 | 入力→出力 | 信頼境界・禁止 |
| --- | --- | --- | --- |
| Day catalog / admission | 機械的検査者 | 構成済みDay契約→`ADMISSIBLE`又は`BLOCKED(reason)` | Day 1〜14を一括実行しない。契約欠落を推測補完しない。 |
| 利用者入口 | UI/API | Day選択、Go、Stop、Resume→明示イベント | 選択だけではrunも外部効果も作らない。UI入力はscope・予算・完了を決めない。 |
| Run lifecycle | 実行管理者 | Go→Run Intent、PREFLIGHT、Day state、再開先 | 一runは一Day・一契約fingerprint。別Day自動遷移なし。 |
| Preflight | 機械的検査者 | Run Intent→許可又はblocker | scope、Git基線、実効権限、時間・試行・費用、外部効果、契約を決定的に検査する。 |
| Evidence / completion | Evidence・状態管理者 | 結果→Evidence Record→validator→criterion判定 | exit 0、画面、AI自己申告、過去保存値だけで完了を作らない。 |
| Repair / revalidation | 実装・修正担当＋機械的検査 | Gap Diagnosis→許可内作業→再検証又はM05 | LocalLLM提案は非権威。scope/Git/budget/retryを通らない変更、同一失敗三回目を禁止。 |
| Review control | 監視・配送担当＋ChatGPT | report/reply ID→`SENT/RECEIVED/APPLIED/VERIFIED` | Day stateを直接変更しない。人間の通常伝言、composer自動化、複数outstandingを通常経路にしない。 |
| Dashboard read model | 読み取りAPI＋UI | Run/Review/Evidence/Telemetry→現在状態表示 | currentとhistorical、値と出所、`UNKNOWN`と0を混同しない。 |
| Human decision | 広瀬剛 | 判断依頼→判断記録→レビュー確認 | 範囲・費用・権限・解決不能をAIが代行しない。確認なしの再開を禁止。 |

## 4. 正本データと状態モデル

既存のDay状態（`IDLE`、`PREFLIGHT`、`LOADING_CONTRACT`、`INVENTORY`、`VALIDATING`、`DIAGNOSING_GAP`、`COLLECTING_EVIDENCE`、`EXECUTING_DAY_WORK`、`CORRECTIVE_WORK`、`REPAIR_SUPERVISOR`、`REVALIDATING`、`PAUSED`、`STOPPED`、`COMPLETE`、`HUMAN_ACTION_REQUIRED`、`EXTERNAL_ACTION_REQUIRED`、`FAILED_UNRECOVERABLE`）を制御状態として用いる。`RUN_INTENT_CREATED`と`DAY_SELECTED`は状態enumを増やさない監査イベント／UI投影である。

| 記録 | 必須内容 | 意味 |
| --- | --- | --- |
| DayAdmission | day、contract/runbook版、required Evidence、許可scope、上限入力、`ADMISSIBLE/BLOCKED`理由 | Dayを安全にGo可能かを示す。実行済み・受入済みではない。 |
| RunIntent | run ID、selected Day、Go時刻、契約/policy/config/Git fingerprint、requested limits | Go直後の同一run監査単位。PREFLIGHT失敗でも停止理由を保持する。 |
| RunControl | current Day state、状態履歴、next action、blocker、resume target | 実行管理者だけが更新する。historical snapshotはcurrent稼働根拠にしない。 |
| Evidence Record | run ID、criterion、provider/validator版、source/config fingerprint、収集時刻、validator/compatibility結果 | criterion達成の唯一の入力。 |
| Repair Episode | failure/action fingerprint、許可scope、試行数、変更・検証、停止／判断理由 | 無変更反復と範囲外修正を防ぐ。 |
| Review Control | REPORT_ID、outstanding、送達／応答／適用時刻、期限、再開許可との相関、受信／適用開始／適用終了時刻、継続envelopeの行為・検証結果、後続report/comment ID | Day stateとは別。応答なし・ID不一致・exit 0だけは承認又は適用ではない。 |
| Run Telemetry | `manual_relay_count`、理由必須の介入、試行／許可上限、token・費用・各出所、時点 | `UNKNOWN`は0や成功へ変換しない。 |

## 5. 機能経路

### 5.1 Day一覧・選択・Go

```text
Day catalog read → DayAdmissionを表示
利用者が一Dayを選択（外部効果なし）
  → Go(day)
  → RunIntentを作成し同一run IDを返す
  → PREFLIGHT
  → [合格] LOADING_CONTRACT → INVENTORY → VALIDATING
  → [不合格] HUMAN_ACTION_REQUIRED / EXTERNAL_ACTION_REQUIRED / STOPPED
```

Goは、未選択Day、`BLOCKED`なDay、dirty Git基線、実効権限未確認、必要上限未確定、契約不一致、必要な外部前提未確認ではDay作業を起動しない。前提が不足するときもRunIntentとblockerは保存し、利用者には「次に必要な判断」を示す。全Dayを一括でGoしない。

### 5.2 計画・証拠・実施

```text
VALIDATING
  ├─ 全criterionがvalidator済み → COMPLETE
  └─ 未充足criterion → DIAGNOSING_GAP
       ├─ 非変更の証拠収集 → COLLECTING_EVIDENCE → REVALIDATING
       ├─ 許可済みDay作業 → EXECUTING_DAY_WORK → REVALIDATING
       ├─ ENGINEERING_REPAIR → REPAIR_SUPERVISOR → REVALIDATING
       └─ 権限・費用・基線・未分類 → HUMAN/EXTERNAL_ACTION_REQUIRED
REVALIDATING → INVENTORY（影響範囲）→ VALIDATING
```

一つの未充足criterionには、Evidence type、入力fingerprint、分類、次アクション、期待状態変化を持つGap Diagnosisを作る。Evidenceは`Result Adapter → Evidence Record → validator → criterion evaluation`を通る。`COMPLETE`は全criterionのvalidator済みEvidenceと、必要なreview controlの条件が満たされた場合だけ生成する。

### 5.3 許可内修正・人間判断・同一Day復帰

```text
Repair proposal（LocalLLMを含む非権威入力）
 → scope/Git/budget/retry検査
 → 許可内なら限定修正 → deterministic verification → REVALIDATING
 → 拒否、同一失敗二回、又は権限・費用・範囲外
 → HUMAN_ACTION_REQUIRED
 → 判断記録 → matching reviewer確認
 → 同じselected Day・同じrun IDのPREFLIGHT
 → 契約、権限、Git、費用、試行、証拠を再検査
```

人間判断は停止解除ではない。matching reviewer確認なし、別Dayへの自動遷移、Day選択前への不要な巻戻し、再検査なしの実施を禁止する。

### 5.4 レビュー・監視・表示

通常のレビュー報告はReview Bridge/Watcherで一件だけ配送する。Review Controlの状態は、`SENT`→`RECEIVED_PENDING_APPLY`→`APPLYING`→`APPLIED`→`VERIFIED`とする。`RECEIVED_PENDING_APPLY`は一致する`IN_REPLY_TO`を保存したが継続を開始又は完了していない状態、`APPLYING`はWatcherが新規Codex継続を起動済みでenvelopeを検査中の状態、`APPLIED`は検証済みenvelopeの行為と後続状態を記録済みの状態である。実際の後続report/comment又は停止／人間判断状態を読み戻せたときだけ`VERIFIED`にする。これはDay stateの遷移権限ではない。10分超の応答待ち、ID不一致、重複、継続期限超過、envelope欠落／不正、又はexit 0かつ配送実体なしは`DELIVERY_FAILED`又は`CONTINUATION_FAILED`としてfail-closedにする。

Watcherは各状態に、対応report/reply/comment ID、時刻、現在行為、継続プロセス結果、envelope検証理由、後続外部効果IDを保存する。Dashboardは、単一の`pending`値だけで「停止」又は「適用済み」と表示せず、上記状態、最終更新時刻、次の自動又は人間行為を表示する。認証はトークンを保存・表示せず、実行主体、認証方式の可否、keyring等の安全な可用性結果だけを`AUTH_CONTEXT_MISMATCH`として記録する。

Dashboardは、selected Day、run ID、admission、current state、historical state、未達criterion、next action、待機／判断待ち／停止、review state、手動中継・介入・試行・token・費用と出所を読み取り専用で示す。通常のレビュー報告は人間のコピペを要しない。新認証、新配送先、費用、範囲外権限だけを人間判断にする。

### 5.5 生存確認・期限・通知

実行管理者は、各runの最終状態更新時刻、現在のstate、active action、期限、次行為をserver-ownedのRunControlへ記録する。Dashboardの定期読取は表示のためであり、稼働・完了の根拠にしない。Watcherの約2分のpollはレビュー応答の配送／取得だけを担当し、Day stateを変更しない。

期限超過、heartbeat欠落、又は応答待ち10分超では、新規作業を開始せず`PAUSED`、`HUMAN_ACTION_REQUIRED`又は`EXTERNAL_ACTION_REQUIRED`へ止める。復帰は同一run・同一DayのPREFLIGHT再検査からのみ可能とする。通常の状態通知はRunControlの差分とreview controlの状態で足り、通知失敗を作業完了や自動再試行の根拠にしない。

## 6. 異常・停止・復旧の設計

| 異常 | 検知 | 停止／復旧 |
| --- | --- | --- |
| 未構成Day、契約／規則の古さ | DayAdmission、fingerprint差 | `BLOCKED`又は`PREFLIGHT`停止。規則読込後も同じDayだけを再検査。 |
| dirty Git、scope外、実効権限不明 | preflightのGit/permission guard | reset/cleanせずM05判断へ。 |
| 時間・試行・費用上限 | server-owned limit check | 新規操作を止め、実測・出所・再開条件を表示。 |
| 空出力、exit 0、部分・未検証Evidence | Result Adapter/validator | `COMPLETE`を拒否しGap Diagnosisへ。 |
| LocalLLM提案が危険又は不十分 | scope/Git/budget/test guard | 提案を拒否し、許可内の別アクション又はM05へ。 |
| 同一失敗二回 | failure/action fingerprint | 三度目を禁止し、人間判断要求。 |
| Review ID不一致、重複、期限超過、Watcher不在 | Review Control、heartbeat、deadline | 適用せず停止。必要なら外部前提の判断要求。 |
| 応答受信後の継続中、継続結果欠落、不正envelope、exit 0のみ | `RECEIVED_PENDING_APPLY`／`APPLYING`、continuation result、後続report/comment読戻し | 途中状態を停止又は適用済みと誤表示しない。検証済みenvelopeと後続状態がなければ`CONTINUATION_FAILED`で停止。 |
| 実行主体ごとの認証可用性差 | 認証前flightの実行主体・keyring可用性（秘密値は記録しない） | `AUTH_CONTEXT_MISMATCH`として外部配送を止める。別の認証保存方式へ無断で切替えない。 |
| 再起動 | persisted Run/Review Controlの一意性検査 | 同一run/reportだけを復元。実証不能ならM05→G3でM04を再評価。 |

## 7. 代替と非採用

M01（FastAPI/Python、JSON、Evidence、Review Bridge/Watcher、Codex、Repair Supervisor）を条件付き主設計とする。M04（durable outbox/reconciler）は、M01が実actorで再起動横断の一意送達・一意継続を満たせない場合だけG3へ戻して最小検証する。M05は必須の証拠付き安全停止であり、M04の代替実装ではない。

通常の手動中継、ChatGPT composer自動化、Day 1〜14の一括実行、新フレームワーク／新インフラ、過去状態をcurrentとする表示は通常経路から除外する。

## 8. 設計受入と後続検証

| 要求 | 設計で固定した経路 | 既存根拠 | 後続の検証対象 |
| --- | --- | --- | --- |
| A01 | DayAdmission→選択→Go→RunIntent→PREFLIGHT | API/fixtureのみ | 実UI、同一run ID、拒否表示 |
| A02 | criterion→Evidence Record→validator→COMPLETE | W04 fixture | Day固有Evidence型と実環境 |
| A03 | Gap→guarded repair→revalidation→M05 | W03の停止fixture | 許可修正の実成功と再検証 |
| A04 | orthogonal Review Control/Watcher | W01、過去相関 | 実actor、再起動横断、期限 |
| A05 | read-only current/historical dashboard | 既存UI読取 | UIとstate/Evidence照合 |
| A06 | Run Telemetryと同一run表示 | 未実装／未実証 | relay/介入/token/cost/試行の実測 |
| Day 1〜14 | DayAdmissionの個別`ADMISSIBLE/BLOCKED` | catalog候補 | 実行なしの契約・scope入場確認 |

本G4の予備検証は、旧G4 W01〜W04の限定fixture根拠を参照するだけで、新たなテストを実行しない。v2で新設した機能の実証はG5の作業カード、G6の一枚ずつの実装、G7の検証、G8の受入で行う。実actor E2E、UI E2E、全Evidence型、実修正成功、M04は`NOT_EVALUABLE`のままである。

### 8.1 G4再実施の確認範囲・除外・打切り

| 対象 | 今回の扱い | 根拠又は打切り |
| --- | --- | --- |
| 正常系 | Day admission→Go→PREFLIGHT→Evidence→修正／review→結果の設計歩行 | 本書5節。実UI／実Dayの操作はしない。 |
| 異常系 | 権限、Git、上限、空出力、古い規則、重複、再起動、同一失敗二回、Watcher不在 | 本書6節。各々に停止又は同一Day復帰を定義。 |
| 既存技術根拠 | W01〜W04のfixture、W05の`NOT_EVALUABLE` | 旧G4に記録済みの限定結果を再利用。再実行・結果の格上げはしない。 |
| 除外 | Day仕事、モデル、実actor配送、実UI、全Evidence型、実修正成功、M04実装 | このG4再実施の人間指示は設計再実施であり、実装／実行許可ではない。 |
| 打切り | 設計に未定義遷移又は復旧／終了のない主要失敗が見つかった時点 | G4を差戻し、G5／G6へ進まない。 |

## 9. G4再実施の出口

本書の出口条件は、A01〜A06、Day 1〜14の安全な入場、M01/M04/M05、正常・異常・人間判断後の復帰、current/historical、Evidence、Review Control、Telemetryに未定義遷移がなく、各失敗に復旧又は終了があることとする。

`ARTIFACT_QUALITY_CHECK: SELF_CHECK_PASS`。これは設計本文の自己点検結果であり、fixture、実actor E2E又は製品受入を意味しない。

## 10. 人間承認と後続境界

2026-09-28に広瀬剛は「G4を承認します。G5を開始してください。」と明示した。この承認により、本書をG4の人間承認済み設計基線として`COMPLETE`にする。同時に許可されたのはG5の計画化だけである。G6実装、テスト実行、Day選択／Go、モデル実行、外部配送、費用発生、Git commit／push、製品受入は含まれない。それぞれは後続工程での別の明示的権限とする。

## 11. 観測補遺 — Review continuationの状態・証跡

2026-09-28のG5 reviewer応答処理で、`pending_response`だけを読んだ観測者が「継続停止」と誤認し得ること、また継続のexit 0だけでは次のreport送付又は指示適用を証明できないことを確認した。広瀬剛の明示指示により、本節はv2基線への限定補遺として追加する。

補遺はReview Controlの観測粒度だけを補う。Dayの状態遷移、G0の目的、M01/M04/M05の選定、G6実装権限、Day Go、費用、認証保存方式を変更しない。実装はG5の`WC-07A`、実actor検証は`VC-11`で扱う。

2026-09-28に広瀬剛は本補遺および対応するG5改訂を承認した。この人間承認は設計・計画基線の承認であり、G6実装、テスト、Day Go、製品受入を許可しない。G5 Reviewer確認は別途待機する。

## 12. v2.1補遺 — レビュー可能な成果物基線

### 12.1 目的と適用範囲

G0〜G5の設計・計画をレビューするとき、PRコメントへの本文貼付だけでは、対象版、後続変更、
正本と撤回版、及び承認根拠を一意に照合できない。したがって、レビュー入力を
`ReviewArtifactBaseline`としてGit上の固定コミットに束ねる。ブランチは作業・公開の経路であり、
レビュー対象そのものではない。レビュー対象は必ず一つのrepository、branch、commit SHA、
対象パス、内容hashの組である。

本補遺はG0〜G5の文書・プロンプト・承認記録をレビュー可能にする運用設計である。Day state、
製品のGo、Evidence判定、Watcherの配送方式、認証保存、G6実装、費用、製品受入を変更しない。

### 12.2 `ReviewArtifactBaseline` の記録と状態

| 記録 | 必須内容 | 禁止・意味 |
| --- | --- | --- |
| ReviewArtifactBaseline | baseline ID、repository、branch、immutable commit SHA、作成時刻、対象G、対象パス、各ファイルSHA-256、正本／補助／`SUPERSEDED`区分、index path | branch名だけ、作業ツリー状態だけ、PR本文だけをレビュー対象にしない。 |
| ReviewAuthorityRecord | authority ID、判断者、判断本文の正確な引用、取得時刻、対象範囲、source class、外部参照の有無 | Codexの要約を人間原指示そのものと偽らない。外部参照がなければ独立検証済みと表示しない。 |
| ReviewRequestBinding | REPORT_ID、baseline ID、reviewed commit、対象パス／hash、提出comment ID、返信comment ID、`IN_REPLY_TO`、結論 | 一件のoutstanding reportに複数commitを混在させない。 |

`ReviewArtifactBaseline`の状態は`DRAFT`→`PUBLISHED`→`FROZEN_FOR_REVIEW`→
`RESPONSE_RECEIVED`→`APPLIED`又は`SUPERSEDED`とする。`FROZEN_FOR_REVIEW`のcommitは
書き換えず、レビュー中に設計・計画を更新した場合は、新commitを別baselineとして
`SUPERSEDES <old baseline>`にする。旧応答は旧commitだけに適用し、新baselineは旧reportの
書換えや再利用で受理させない。

### 12.3 承認根拠の表現と検証限界

人間の直接指示には次のsource classを付ける。

| source class | 条件 | レビュワーの扱い |
| --- | --- | --- |
| `DIRECT_EXTERNALLY_REFERENCED` | 人間が作成した外部参照を、レビュワーが直接読める | 引用、参照先、対象範囲を照合できる。 |
| `RECORDED_DIRECT_CONVERSATION` | Codexが直接受けた人間メッセージを正確に引用してGitへ記録したが、レビュワーが原メッセージへ直接アクセスできない | 承認記録として読めるが、独立に原指示を確認済みとは表示しない。追加の人間参照が必要なら`HUMAN_REQUIRED`とする。 |
| `UNAVAILABLE` | 引用又は出所を保存できない | 承認済みと主張せず、当該境界を越えない。 |

本プロジェクトの既存G4承認「G4を承認します。G5を開始してください。」及び観測補遺承認は、
現時点では`RECORDED_DIRECT_CONVERSATION`としてG4本文に保存する。外部から直接追跡できる
原指示がないことを隠さない。これはG5計画化を超える権限を生じさせない。

### 12.4 レビュー配送・更新の経路

```text
agent/* branchで限定編集
  → required files + index + hashes をcommit
  → push
  → ReviewArtifactBaseline=PUBLISHED
  → reportに baseline ID / branch / immutable commit / paths / hashes を固定
  → FROZEN_FOR_REVIEW（1 outstanding report）
  → matching response
  → APPLIED、又は新commitをSUPERSEDEDとして別REPORT_IDで再提出
```

Review Bridgeには短い参照と相関情報を送る。成果物の全本文を通常の報告に複製しない。
レビュー中に新commitが必要になった場合、既存reportの本文、ID、commitを後から変更しない。
matching responseを読んでoutstandingを解消してから、新しい`REPORT_ID`で新baselineを提出する。
Watcherは`ReviewRequestBinding`のcommit SHAとresponseの`IN_REPLY_TO`を保存し、継続envelopeが
異なるcommitの作業を指す場合は`CONTINUATION_FAILED`として停止する。

### 12.5 初回適用と後続検証

初回の公開基線は、`docs/ai-control-center-gates/2026-09/`のindex、現行正本、補助記録、
プロンプト、`superseded/`を含む。後続のG6以降で実装する必要があるのは、製品データモデルを
増やすことではなく、Review Controlがreportごとの固定commitと対象範囲を読取り表示・照合できる
ことである。その実施・fixture検証はG5の`WC-00`と`WC-07A`に分ける。

`ARTIFACT_QUALITY_CHECK: SELF_CHECK_PASS`は、本補遺が固定commit、正本区分、承認根拠の限界、
report相関、更新時の再提出規則を定義することだけを示す。実actorがcommit bindingを検証した証拠、
人間原指示の外部参照、又は製品受入を示さない。

## 13. v2.2補遺 — 人間の承認対象とReviewer再確認

### 13.1 一つの判断依頼は一つの対象と効果

「Reviewerのコメントに賛成」と「Codexの成果物を受理」は異なる判断である。
一件だけの未解決依頼、直前の発言、投稿順、肯定語だけでは対象を確定しない。
人間に提示する各判断依頼には次の組を固定する。

| 項目 | 内容 |
| --- | --- |
| `DECISION_ID` / revision | 一つの対象と効果を持つ判断依頼ID・版。内容変更時は再提示する。 |
| `SUBJECT_TYPE` / `DECISION_SUBJECT` | 下表の種類と、人間が読める一文の問い。 |
| target | G、baseline ID、対象commit・path、必要ならReviewer comment ID・該当提案箇所。 |
| correlation | 元のREPORT_ID、Reviewer response comment ID、確認報告ID、判断の返信先。 |
| effect / limits | 承認で許される行為、範囲、条件、予算、承認しても開始しない行為。 |
| response destination | このチャット内の対象付き返信、又は指定Review Bridgeコメントへの返信。受信側の担当と転送先を明記する。 |

| SUBJECT_TYPE | 問いの例 | 承認の効果 |
| --- | --- | --- |
| `REVIEWER_RECOMMENDATION` | ReviewerコメントXの指摘Yに沿ってG5を修正してよいか | 指定修正の採用・実施許可。修正結果の受理を兼ねない。 |
| `CODEX_ARTIFACT` | commit CのG5成果物を文書として受理するか | その版の人間受入。工程出口・次工程開始は別。 |
| `GATE_EXIT` | 指定証拠を基にG5出口を承認するか | 対象Gの出口に対する人間判断。必要なReviewer確認は残る。 |
| `EXECUTION_AUTHORITY` | カードWを範囲S・上限Bで開始してよいか | 明示された作業だけの許可。別カード、Day、費用へ波及しない。 |

異なる種類を一つの「承認」ボタンや選択肢に混ぜない。拒否・修正依頼・保留は同じ対象への
回答として扱う。一発言に複数の明示判断がある場合は、原文を保持した上で対象別に記録する。

### 13.2 「承認します」の受信・対象確定

人間には「D-xxx：ReviewerコメントXの修正提案を採用する承認です。成果物の受入やG5終了は
含みません」のように対象と効果を表示する。返信の選択操作又は引用がこの判断依頼のID・版に
結び付くときだけ、短い肯定をその対象への承認として正規化できる。

通常のチャット／PRに単独で書かれた「承認します」で、対象を確定できない場合は
`HUMAN_RESPONSE_UNCLASSIFIED`として原文を保存する。「Reviewerの修正提案の採用ですか、
Codexの成果物の受理ですか」のように不足する対象だけを質問し、回答を元の発言へ関連付ける。
明確な対象付き指示には繰り返し承認を求めない。GitHubへ同じ承認を手動転記することを通常手順にしない。

`HumanDecision`には原文、判断者、受信channel、message/comment ID（取得不能ならUNKNOWN）、
source class、受信時刻、対象DECISION_ID・版、対象commit、判断内容、効果、対象確定の根拠を保存する。
チャットで直接受けた指示は`RECORDED_DIRECT_CONVERSATION`として配送できる。
GitHubの投稿アカウントがHIPVGでも、Codexが代理投稿した引用は人間本人の投稿と断定しない。
発信者の来歴と承認対象の一意性は別々に検査する。

### 13.3 Reviewerが反応する配送とClose条件

```text
Reviewer応答 R1 → 対象・効果を明示した判断依頼 D1
  → 人間返答 → 不明なら HUMAN_RESPONSE_UNCLASSIFIED → 対象だけ確認
  → 確定した返答を HUMAN_DECISION_RECEIVED として記録
  → 新しい確認報告 R2（D1・原文・出所・対象commit・許可範囲）
  → REVIEW_CONFIRMATION_PENDING
  → R2への一致応答を全文確認 → REVIEW_CONFIRMED 又は REJECT/HUMAN_REQUIRED
  → 許可された効果だけ適用 → 読み戻しで検証
```

人間コメント自体がReviewerを起動するとは仮定しない。チャットはCodexが受信し、PR上の人間返信は
将来の受信adapterが取得する。Codex／配送担当は同じ経路に集約し、通常の`REPORT_TYPE:`付き
確認報告をReview Bridge PR #1へ一件送る。Watcherはその一致応答を取得して継続へ渡す。
再起動・二重取得でも同じ人間message/comment ID＋DECISION_ID＋版から二件の報告を作らない。
別reportが未解決なら確認報告を待機させ、既存reportの解消後に送る。

Reviewer応答は確認報告の`IN_REPLY_TO`、DECISION_ID、判断版、対象commit、判断種類・範囲が
一致した場合だけ有効とする。状態ファイルのpending IDと応答本文のIN_REPLY_TOが異なる場合も
不一致であり、本文を書換えたり最新IDへ付け替えたりしない。

人間返答の保存・対象確定・報告送信は、それぞれの受信／配送処理の完了にすぎない。
Reviewerの確認前に承認対象を`APPLIED/VERIFIED`、GをCOMPLETE、判断案件をCLOSEDにしない。
Reviewerが`CONTINUE`した修正提案を適用しても、成果物受理又はG出口完了へ読み替えない。
Closeは同一判断の必要な人間決定とReviewer確認が揃い、種類に応じた効果を適用・確認したときに限る。
PRのclose/merge、次工程開始は個別の実施許可・出口条件が必要である。

拒否・相関不一致・送達失敗・応答期限超過は理由付きの待機又は判断要求に留め、承認の推測や
自動Closeをしない。対象commit変更時は旧判断を新成果物に継承せず、変更後の対象を再提示する。
人間による明示的な手順変更は現行規則の優先順位に従い記録し、Reviewerが受理済みと偽らない。

### 13.4 実現手段と未実装範囲

判断・相関ガードは既存Python/PydanticとJSON永続化境界、配送はReview Bridge、表示は既存read modelを
再利用する。新たな常駐サービスは前提にしない。これは設計案であり、現行Watcherに人間コメントの
識別、判断対象の解釈、再確認報告の重複防止が実装済みとは主張しない。
G5 WC-07Bで契約・ガード・配送adapter境界を実装し、WC-09/10で対象・許可範囲・確認待ちを表示、
VC-11で実actorの再確認を検証する。通常の運用規則そのものの変更はこの補遺だけでは行わない。
