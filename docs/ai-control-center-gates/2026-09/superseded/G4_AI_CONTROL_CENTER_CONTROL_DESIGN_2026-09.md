# G4 — AI-Control-Center 基本設計・制御設計

文書 ID: `G4-ACC-20260925-001`  
状態: `COMPLETE`（2026-09-28に広瀬剛がG4出口を承認。製品受入・G5着手は含まない）  
根拠: `HIPVG/ai_work_operating_standard` `main` `3c1d8c6b8b28128bd4db6f0f01b0b86f19aece1f`、G4  
G3入力: `G3-ACC-20260925-002`（`COMPLETE`）  
実行正本: `docs/DAY_RUNNER_EXECUTION_SPEC.md`  
範囲: M-01の制御設計、M-04の発動設計、M-05の安全停止設計、既存fixtureによる限定予備ウォークスルー。
実装、対象Dayの選択・実行、モデル実行、費用発生は含まない。

## 1. 設計判断と境界

M-01（既存の決定的制御、JSON状態・Evidence、Review Bridge、Watcher、新規継続、Repair Supervisor）を
条件付きの主設計とする。M-04（永続outbox/reconciler）はM-01の対応ID・冪等性・再起動後の状態整合が
実証不能なときだけ発動する。M-05は、権限、費用、基線、同一失敗二回又は候補不成立を、人間判断へ
安全に渡す必須経路である。

この文書はG3で未評価の「人間判断後の同一Day復帰」と「candidate-switch」を成立済みと扱わない。
両者は、実装後へ先送りせず、既存fixture又は実主体による予備検証で確認し、確認不能ならG3へ戻す。
現在のLocalLLM-Lab基線を操作しない。

## 2. 役割・構成要素・信頼境界

| 役割 | 設計責任 | 信頼境界・禁止 |
| --- | --- | --- |
| 利用者入口 | Day選択・Go、状態と停止理由の表示 | Day、パス、コマンド、予算、受入条件をサーバへ注入しない |
| 人間の責任者 | 目的、権限、費用、未解決事象、最終受入の判断 | AI又は終了コードだけで受入しない |
| 実行管理者 | 選択Day、契約、状態遷移、再開先、対応IDを永続化し許可済み遷移だけを起動 | `COMPLETE`を自己申告や作業終了から生成しない |
| 機械的検査 | 契約、範囲、Git基線、予算、試行、重複、証拠を決定的に判定 | 意味判断、権限付与、受入を代行しない |
| 実装・修正担当 | 許可済みテンプレート内の実施又は限定修正 | 範囲拡張、権限昇格、三度目の同一修正をしない |
| レビュー・検証担当 | 報告・証拠・判断記録・再開先を確認する | 実装者の自己申告を無検証で合格にしない |
| 証拠・状態管理者 | immutableなEvidence Record、Gap Diagnosis、Action Attempt、判断記録を対応付ける | 任意の作業結果を受入証拠にしない |
| 監視・配送担当 | 一件のレビュー報告を相関し、期限・未応答・継続を監視する | 応答なしを承認扱いにしない |

実現候補はPython/FastAPI、JSON永続化、Evidence Registry、Review Bridge、Watcher、Codexであるが、
これらは役割そのものではない。UI/API、外部レビュー配送、対象リポジトリ、AIモデルは相互に信頼
しない境界とし、実行管理者と機械的検査者を通る入力だけを採用する。

### 2.3 外部効果の状態とlive前提

標準1.5に従い、外部操作を`INTENDED`→`ATTEMPTED`→`SENT`→`RECEIVED`→`APPLIED`→`VERIFIED`で
区別する。下表は設計上の契約であり、製品E2Eの完了報告ではない。

| 外部効果 | 意図・試行 | 送信・受領・適用の証拠 | `VERIFIED`の条件 | 現在の扱い |
| --- | --- | --- | --- | --- |
| Review Bridge報告 | 一意の`REPORT_ID`を作成し、一件だけoutstandingにする | PRコメントID=`SENT`、一致する`IN_REPLY_TO`を読む=`RECEIVED`、watcherが記録して継続を起動=`APPLIED` | 実際の後続状態を実装者と異なる主体又は改変不能な検査で読み戻す | 過去の往復とfixtureはある。製品経路の`VERIFIED`ではない |
| 利用者のUI/API操作 | 選択済みDayのGo/Resume | API受付、保存snapshot、画面投影を別に記録 | 実UI、同一run IDの保存状態、Evidence Recordを独立に照合 | fixtureのみ。実UIは未実施 |
| watcherのlive監視 | 起動前提をPREFLIGHTで検査 | listener、status API、heartbeatを別に記録 | watcherが期限・応答・継続を設計どおりに扱う実E2E | 2026-09-26の読取で8000・8765ともlistenerなし・API接続拒否。`BLOCKED`、自動起動しない |

外部効果の状態が不明なら`UNKNOWN`に戻し、終了コード0、コメント本文、保存済み`running`だけで
`RECEIVED`又は`VERIFIED`にしない。現在のlive watcher不在はM-01の不可能性を断定せず、実行時の
PREFLIGHTで`EXTERNAL_ACTION_REQUIRED`又は安全停止へ移す入力である。

### 2.1 G3の役割フローからG4状態遷移への精密化

G4はG3のフローを置換しない。G3で固定した役割間の受渡しを、実装時に未定義のまま残さないために
状態・イベント・記録へ細分化する。したがって、状態遷移は実行管理者の内部制御であり、レビュー配送
又はAIの応答がDayの状態を直接変更する経路ではない。

```text
G3の役割フロー（変更しない責任の流れ）
利用者入口 → 実行管理者 → 機械的検査 ─────────────┐
                 ↑             ↓                         │
人間の責任者 ← 判断要求 ← 実装・修正担当 ← Gap診断      │
                 ↓             ↓                         │
レビュー・検証担当 ← 証拠・状態管理者 ← 再検証 ────────┘
       ↑
監視・配送担当（報告の相関・期限監視。状態遷移を代行しない）
```

| G3の役割上の受渡し | G4での状態上の精密化 | 変わらない責任 | 継続性の判定 |
| --- | --- | --- | --- |
| 利用者入口→実行管理者（選択・Go） | `IDLE`→`PREFLIGHT` | 選択済みDayとGo要求を実行管理者が記録する | Day選択を新設・置換しない |
| 実行管理者→機械的検査→証拠・状態管理者 | `PREFLIGHT`→`LOADING_CONTRACT`→`INVENTORY`→`VALIDATING` | 契約、基線、範囲、予算、試行、証拠を決定的に判定する | G3の検査・証拠経路を順序付きにしただけである |
| 検査結果→実装・修正担当→再検証 | `DIAGNOSING_GAP`→収集／Day作業／`CORRECTIVE_WORK`／`REPAIR_SUPERVISOR`→`REVALIDATING` | 許可済みの実施又は限定修正だけを行い、再検証へ返す | 新しい自動修正権限を追加しない |
| 未解決事象→人間の責任者→レビュー・検証担当→実行管理者 | authority状態→判断記録・レビュー確認→同一selected Dayの`PREFLIGHT` | 人間だけが判断し、レビュー・検証担当は再開条件を確認する | G3の同一Day復帰を、解除ではなく再検査として固定する |
| 監視・配送担当↔レビュー・検証担当 | report/reply ID、outstanding、期限の外側制御 | 一件だけを相関し、無応答を承認にしない | 配送は横断的な制御であり、`COMPLETE`等を生成しない |

この表以外の状態遷移は、新しい業務フロー又は役割の追加として扱い、G3へ戻して評価する。特に
M-04候補切替はこの表の通常経路に含めず、M-01不成立時のG3再評価対象である。

### 2.2 役割を担う技術手段、有効性の根拠、限界

「技術手段が存在する」と「役割を果たせる」は別である。下表では、選定M-01の各手段について、
何を担い、どの既存証拠がその範囲を確認したか、及び確認していないことを明示する。`PASS`は行の
限定された役割範囲にだけ適用し、製品全体又は独立した人間レビューの完了を意味しない。

| G3の役割 | M-01の技術手段 | 担う機能と境界 | 有効性の根拠 | 判定・未確認範囲 |
| --- | --- | --- | --- | --- |
| 利用者入口 | FastAPIのローカルAPI | 選択済みDayのstart/resume要求を実行管理者へ渡す。画面UIやDay選択の権限判断は担わない | W-02: `test_production_api_resumes_same_day_after_authority_resolution` | API要求の受理と同一Day復帰は`PASS`。ブラウザ画面の利用性は本G4で未確認であり、実証済みと主張しない |
| 実行管理者 | `LocalLLMDayProgram`とJSON snapshot | selected Day、契約fingerprint、状態履歴、再開先を保持し、許可済み遷移だけを開始する | W-02でauthority解消後も同じselected Dayを保ち、`PREFLIGHT`を再経由することを確認 | この再開制御は`PASS`。対象Dayの実作業を自動的に完遂できることは本ウォークスルーの対象外 |
| 機械的検査・証拠／状態管理 | PydanticのEvidence Record、Evidence Validator、JSON永続化 | 証拠の型・検証・互換性を判定し、空・部分的・未検証の結果を受入に使わせない | W-04: `test_partial_unrelated_empty_and_unverified_evidence_fail_closed` | fail-closed判定は`PASS`。全Evidence typeの網羅的実証ではない |
| 実装・修正担当 | Guarded work/Repair SupervisorとCodexの許可内作業 | 失敗fingerprint、試行上限、検証済み修正だけを扱い、境界超過を判断要求へ渡す | W-03: `test_repair_deadline_escalates_without_waiting` | 上限到達時の停止・エスカレーションは`PASS`。特定の自動修正が成功することは未実証であり、成功を前提にしない |
| レビュー・検証担当 | Review Bridgeの構造化report/replyとChatGPTレビュー | 報告、証拠、判断記録、再開先を確認する。実装者の自己申告を受入根拠にしない | G3 F-01の実主体相関とW-01の一致／不一致／exit 0 fixture | 相関・不受理制御は`PASS`。同一ChatGPTによるレビューと検証は独立確認ではない |
| 監視・配送担当 | `ReviewerBusWatcher`、GitHub PR #1、相関状態 | 一件のoutstanding report、対応ID、配送結果、未応答期限を監視する。Day状態を決めない | W-01: `tests/test_reviewer_bus.py` の一致応答、一致しない応答、payloadなしexit 0 | 一意適用・失敗検知は`PASS`。M-04の再起動横断outbox/reconcilerは未実装で`NOT_EVALUABLE` |
| 人間の責任者 | 判断依頼書、判断ID、review-confirmation、resume API | 目的・権限・費用・解決不能事象を人間が判断し、技術手段は記録と再検査だけを補助する | W-02のauthority解消→同一Day `PREFLIGHT` | 人間判断を機械又はAIが代替しない。判断内容の正しさは技術テストの対象外 |
| M-05安全停止 | typed authority/stop状態、判断依頼書、Repair Episode | 自動継続を止め、根拠・選択肢・再開先を残す | W-02/W-03 | 同一Day復帰と上限停止は限定`PASS`。M-04の代替能力をM-05が持つとは主張しない |

この対応により、M-01は少なくとも「相関した配送」「同一Dayの再検査復帰」「証拠fail-closed」
「修正上限での停止」というG3必須機能について実装前の技術根拠を持つ。一方、M-04の永続outbox/
reconciler、画面UI、特定修正の成功率、全証拠型の網羅性は根拠がないため、G4の採用根拠に混入させない。

## 3. 正本状態とイベント

状態はDay Runner正本の `IDLE`、`PREFLIGHT`、`LOADING_CONTRACT`、`INVENTORY`、`VALIDATING`、
`DIAGNOSING_GAP`、`COLLECTING_EVIDENCE`、`EXECUTING_DAY_WORK`、`CORRECTIVE_WORK`、
`REPAIR_SUPERVISOR`、`REVALIDATING`、`PAUSED`、`STOPPED`、`COMPLETE`、`HUMAN_ACTION_REQUIRED`、
`EXTERNAL_ACTION_REQUIRED`、`FAILED_UNRECOVERABLE` を使う。`RUNNING`及び旧`FAILED`は既存snapshotの
互換表示であり、新しい制御意味を与えない。

| 現状態 | 受理イベント・条件 | 次状態 | 必須記録 |
| --- | --- | --- | --- |
| `IDLE` | `Go(day)`、Dayが構成済み | `PREFLIGHT` | selected Day、Go時刻、要求ID |
| `PREFLIGHT` | 契約・registry・runtime・Git・scope・外部前提が合格 | `LOADING_CONTRACT` | preflight結果、入力fingerprint |
| `PREFLIGHT` | 外部前提欠落 | `EXTERNAL_ACTION_REQUIRED` | blocker、再開条件 |
| `PREFLIGHT` | controller/safety不変条件不成立 | `FAILED_UNRECOVERABLE` | 不変条件、停止根拠 |
| `LOADING_CONTRACT` | 契約・evidence typeが有効 | `INVENTORY` | 契約版、runbook/config fingerprint |
| `LOADING_CONTRACT` | 契約又はregistry不正 | `FAILED_UNRECOVERABLE` | 検査失敗 |
| `INVENTORY` | Git・既存証拠・保護パスを収集 | `VALIDATING` | inventory fingerprint |
| `VALIDATING` | 全criterionがvalidator済み | `COMPLETE` | Evidence Record IDとvalidator結果 |
| `VALIDATING` | 未充足criterionあり | `DIAGNOSING_GAP` | criterion×evidence type |
| `DIAGNOSING_GAP` | 一意な合法classificationを確定 | 対応する実施状態又はauthority状態 | GapDiagnosis、action fingerprint |
| `COLLECTING_EVIDENCE` / `EXECUTING_DAY_WORK` / `CORRECTIVE_WORK` | 結果adapter完了 | `REVALIDATING` | Action Attempt、影響範囲 |
| `REPAIR_SUPERVISOR` | 検証済み修正 | `REVALIDATING` | Repair Episode、検証結果 |
| `REPAIR_SUPERVISOR` | 権限境界又は安全修正なし | authority状態又は`FAILED_UNRECOVERABLE` | 原因、選択肢、停止根拠 |
| `REVALIDATING` | 影響範囲の再inventory・再収集・validator完了 | `VALIDATING` | 更新Evidence Record、比較fingerprint |
| `PAUSED` / `STOPPED` | 明示Resume、契約・安全再確認 | `PREFLIGHT` | Resume理由、再開fingerprint |
| authority状態 | 判断又は外部blockerが解消しレビュー確認済み | `PREFLIGHT` | 判断ID、レビュー結果、同一Day |

未定義イベント、対応ID不一致、重複イベント、未知evidence type、又は同じaction fingerprintの再実行は
拒否し、状態を進めない。`INSUFFICIENT_EVIDENCE`は終端ではなく、必ず一つのGapDiagnosisへ細分化する。

## 4. 正常経路と証拠流

```text
Day選択・Go
  → PREFLIGHT → LOADING_CONTRACT → INVENTORY → VALIDATING
  → [不足なし] COMPLETE
  → [不足あり] DIAGNOSING_GAP
       ├─ 非変更の収集 → COLLECTING_EVIDENCE ─┐
       ├─ 正常Day作業 → EXECUTING_DAY_WORK ──┤
       ├─ 許可済み訂正 → CORRECTIVE_WORK ────┤
       └─ engineering defect → REPAIR_SUPERVISOR ─┘
                                         ↓
                                 REVALIDATING → VALIDATING
```

証拠は `Work → Result Adapter → Evidence Record → Evidence Validator → Evidence Store → Criterion Evaluation`
だけを通る。各Recordは project、Day、contract version、provider/validator版、source revision/fingerprint、
configuration fingerprint、収集時刻、status、validator/compatibility結果を持つ。作業終了、画面表示、
`exit 0`、AI自己報告は単独でcriterionを満たさない。

## 5. 修正・人間判断・同一Day復帰

許可内修正は、分類済み`ENGINEERING_REPAIR`だけに限定する。Repair Supervisorは失敗fingerprint、
対象範囲、根拠、試行、検証をRepair Episodeへ残す。無変更反復は許可せず、同一失敗分類が二回再発、
又は新しい権限・費用・設計判断が必要になった時点でM-05へ移す。

```text
HUMAN_ACTION_REQUIRED
  → 判断依頼書（決めること／自動決定不能理由／選択肢／影響／期限／判断ID）
  → 人間の責任者の判断記録
  → レビュー・検証担当が、判断の版・範囲・証拠・再開先を確認
  → 実行管理者が同一のselected Dayを保持してPREFLIGHTへ戻す
  → 権限・基線・費用・試行・証拠・契約を再検査
  → 合格した合法な次アクションだけを実施
```

この経路は停止状態の単純な解除ではない。レビュー確認がない判断、異なるDayへの自動遷移、
Day選択への不要な巻戻し、又は再検査なしの実施を禁止する。`EXTERNAL_ACTION_REQUIRED`も同じ
`PREFLIGHT`復帰規則を使うが、外部受領証拠をblocker解消の入力として追加する。

## 6. 主要異常、検知、停止・復旧

| 異常 | 決定的検知 | 停止又は復旧 | 終端／再開 |
| --- | --- | --- | --- |
| 権限拒否・認証欠落 | prerequisite/authority検査 | 外部又は人間判断要求。秘密を通常修正で要求しない | 解消証拠後、同一Dayの`PREFLIGHT` |
| 時間超過・無応答 | deadline、heartbeat、watchdog | 実行を`PAUSED`又はauthority状態へ。進捗ありと稼働中を混同しない | Resume後`PREFLIGHT` |
| 空出力・終了コード0 | Result Adapter/validatorが成果物・収集数を検査 | `INSUFFICIENT_EVIDENCE`をGapDiagnosisへ分類 | 収集、合法作業、又は停止 |
| 古い規則・契約差異 | contract/runbook/policy fingerprint差 | 旧判断を無効化し契約読込へ戻す | `PREFLIGHT`→`LOADING_CONTRACT` |
| 重複又は不一致のレビュー応答 | `REPORT_ID`/`IN_REPLY_TO`と一件のoutstandingを照合 | 適用せずprotocol errorとして記録 | 一致応答を待つ |
| 汚れたGit基線 | inventory/preflightのstatus・保護パス検査 | clean/reset/採用せず基線保全の判断要求 | 判断後、同一Dayの`PREFLIGHT` |
| 同一修正二回再発 | failure/action fingerprintとRepair Episode | 三度目の小修正を禁止しM-05へ | 人間判断又は安全終了 |
| controller/safety不変条件破綻 | 機械的検査 | 安全に継続不能として停止 | `FAILED_UNRECOVERABLE` |

## 7. M-04代替とM-05安全停止

M-04は、M-01で再起動後に対応ID、送達記録、状態又は継続の一貫性を実証できない場合だけ設計・実装
対象になる。引き継ぐのはreport/reply ID、outstanding状態、送達結果、判断ID、selected Day、契約・
入力fingerprint、Evidence Record ID、Action Attempt、blockerである。M-04の最小検証は、再起動を
またいでも一件の報告を重複送達・重複適用せず、対応する一件の継続だけを再構築できることとする。

M-04でも対応ID又は冪等性が保証できない場合、M-05へ移る。M-05は判断依頼書、現状態、証拠、
選択肢、影響、再開先を残し、通常経路を手動中継へ戻さない。ChatGPT composer自動化は通常配送の
代替にしない。

## 8. 証拠対応表とG5引継ぎ

| 設計受入条件 | 証拠／検査 | 現在 | G5以後の最小作業 |
| --- | --- | --- | --- |
| M-01の報告・応答相関 | report/reply ID、送達時刻、継続記録 | F-01 `PASS` | 既存経路を回帰検証 |
| 外部前提のfail-closed | typed failure、外部効果なしの記録 | F-02 `PASS` | prerequisite検査を保持 |
| 許可内修正・再検証・停止 | Repair Episode、scope/budget検査、validator結果 | F-04の修正・停止は`PASS` | 同一分類二回境界を回帰検証 |
| 判断後の同一Day復帰 | 判断ID、レビュー確認、同一Day、PREFLIGHT再検査 | W-02で`PASS` | 既存fixtureを回帰検証 |
| M-04候補切替 | 永続outbox/reconciler状態、再起動後の一意継続 | F-05 `NOT_EVALUABLE` | M-01不成立時にG3で実主体E2Eを確認してから、必要ならG5へ引き渡す |
| M-05安全停止 | 判断依頼書、選択肢、再開先、停止状態 | W-02/W-03で限定`PASS` | 既存fixtureを回帰検証 |
| 対象基線保全 | Git audit、判断記録 | 本G4の対象外 | 個別の明示選択とGo後のみ扱う |

G5は、上表でG4予備検証を通過した実装可能な項目だけを独立した作業カードとし、一カードで新しい
基盤、画面、エージェントを同時導入しない。M-04は、G3で実主体の小さなE2Eを確認できるまで
実装候補として採用しない。G4完了はG5の開始又は製品実装の承認を意味しない。

## 9. 成果物品質確認

予備ウォークスルー前の設計確認では、G3の採用条件、代替、安全停止及び未評価を区別した。すべての
主経路と主要異常は復旧又は終端に割り当て、判断後の同一Day再開は`PREFLIGHT`と再検査に固定した。
その設計判断を次節の限定予備ウォークスルーで確認する。

## 10. 限定予備ウォークスルー計画

目的は、選定M-01が各主要段階で既存の技術手法として有効かを、設計図だけでなく既存の安全fixtureで
確認することである。対象は、G3根拠・標準G4の必須経路・未評価項目から選び、機能追加の必要性や
網羅的な回帰試験を理由に広げない。

| ID | 経路・技術手法 | 既存確認手段 | 合格条件 | 停止・判定 |
| --- | --- | --- | --- | --- |
| W-01 | 監視・配送担当の対応ID相関 | `tests/test_reviewer_bus.py` の一致応答、不一致応答、終了コード0不受理 | 一致応答だけが継続を起動し、delivery payloadなしの終了を成功にしない | 外部投稿をせずfixture内で完結。失敗はM-01のG3再調査 |
| W-02 | 人間／外部判断後の同一対象`PREFLIGHT`復帰 | `test_production_api_resumes_same_day_after_authority_resolution` | selected Dayを保持し、`PREFLIGHT`再検査を経由し、blockerを消去する | 対象Day作業を起動しない。失敗はM-01不成立としてG3へ戻す |
| W-03 | 修正上限と安全停止 | `test_repair_deadline_escalates_without_waiting` | 期限・提案上限で修正を止め、合法な停止又は判断へ移す | 三度目の修正やsource変更をしない |
| W-04 | 証拠のfail-closed | `test_partial_unrelated_empty_and_unverified_evidence_fail_closed` | 部分的・空・未検証の証拠がcriterionを満たさない | 失敗は証拠管理設計の差戻し |
| W-05 | M-04候補切替 | 既存実装・fixtureの有無を読取確認 | 実装済みなら再起動後の一意継続を既存fixtureで確認する | 未実装なら`NOT_EVALUABLE`。fixtureや実装を新設せずG3再調査条件として残す |

固定条件: 既存fixtureだけを一回実行、外部送達なし、費用0円、モデル起動なし、対象Dayの選択・実行なし、
ソース変更なし。W-01〜W-04が一つでも不合格なら、G4の`ARTIFACT_QUALITY_CHECK`は`FAIL`とし、
G5へ進めない。W-05が未実装なら、M-04を採用候補に格上げせずG3の未評価として保持する。

## 11. 限定予備ウォークスルー結果

実施日: 2026-09-25  
実行: 既存test nodeのみを一回実行。`py -3.12 -m pytest -q` に、W-01〜W-04の指定nodeを渡した。
結果出力は失敗・エラーなしで終了した。外部配送、モデル、対象Day、実リポジトリ、source変更は使っていない。

| ID | 結果 | 根拠 | 設計への反映 |
| --- | --- | --- | --- |
| W-01 | `PASS` | 一致応答の一意継続、不一致応答のprotocol nack、delivery payloadなしの終了不受理を既存fixtureで確認 | 監視・配送担当は対応IDを満たす応答だけを適用する |
| W-02 | `PASS` | human/externalの両authority条件で、同一selected Dayを保持して`PREFLIGHT`を再経由する既存API fixtureを確認 | 判断後の同一Day復帰はM-01の検証済み経路として扱う |
| W-03 | `PASS` | Repair Supervisorの期限・提案上限到達時のエスカレーションfixtureを確認 | 同一失敗の無制限修正をしない |
| W-04 | `PASS` | 部分的、空、未検証のevidenceがcriterionを満たさないfixtureを確認 | Evidence Record/Validatorを通らない結果を受入に使わない |
| W-05 | `NOT_EVALUABLE` | `backend`、`tests`、`config`に永続outbox/reconciler又はcandidate-switch実装・fixtureはない | M-04を採用しない。M-01不成立時にG3へ戻し、実主体での小さなE2E又は不可能性を確認する |

### 再判定

M-01は、報告相関、判断後の同一Day復帰、修正停止、証拠fail-closedについて、設計と既存fixtureの
予備ウォークスルーが一致したため、条件付き主候補として維持する。M-04は未実装・未実証であり、
通常経路にも自動代替にも採用しない。M-01が不成立になった場合だけG3へ戻してM-04の可否を確認し、
それまではM-05へ安全に停止する。

`ARTIFACT_QUALITY_CHECK: PASS`は、W-01〜W-04の設計上必要な予備検証と、W-05を未実証のまま
合格扱いにしない記録整合を表す。製品E2E又は`VERIFIED`を表すものではない。

## 12. G4出口の人間承認

2026-09-28、広瀬剛は「G4について承認します」と明示した。これにより、本書と
`G4_STANDARD_DESIGN_REVIEW_2026-09.md`が対象とするG4の文書・設計出口は`COMPLETE`とする。
この承認は、製品受入、G5の着手、Dayの選択／Go、モデル実行、追加のサービス修復、費用発生、
Git変更を許可しない。G5を開始するには、対象・目的・有効範囲を別途明示する必要がある。
