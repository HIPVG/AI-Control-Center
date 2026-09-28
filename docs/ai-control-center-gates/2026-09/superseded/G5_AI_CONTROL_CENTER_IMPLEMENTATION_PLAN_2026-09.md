# G5 実装計画・作業カード・テスト計画

- 文書ID: `G5-ACC-PLAN-20260928-002`
- 状態: `SUPERSEDED_BY_G5_V2`
- 作成日: 2026-09-28（目的適合レビューを反映して改訂）
- 作成者: CODEX（計画・実装担当）
- 最終判断者: 広瀬剛
- レビュー／検証: ChatGPT（同一主体である場合、独立検証とは表示しない）
- 行為分類: `DIAGNOSIS`（実装前の計画化）

## 1. G5の境界

G5は、承認済みG4設計を、個別に実施・検証・停止できる実装カードとテスト計画に落とす工程である。本書はG4 v2前の計画案として保全する。G4 v2の人間承認後に、機能設計の正本をG4 v2とする新しいG5 v2計画へ置き換えられた。本書からG6の実装、Day選択／Go、モデル実行、実機Day検証、費用発生、追加サービス修復、Git変更を許可しない。

本製品の目的は、利用者が一つのDayを画面で選びGoした後、計画・実施・証拠判定・許可内の修正・レビュー・同じDayへの再開をつなぎ、証拠付きの結果又は停止理由を示すことである。G5は可観測性だけを先行させず、この主経路を先に証明可能な単位へ分解する。開発上のG6開始指示と、完成後の製品利用者が画面で行うGoは別の権限境界である。

## 2. 入力固定と共通保護

| 入力 | SHA-256又は基線 | 用途 |
| --- | --- | --- |
| G0成果物・目的文書 | G0で記録した基線 | P01〜P08、役割、停止・復旧、製品と工程の分離 |
| G1現状記録 | G1で記録した基線 | 再利用候補、current/historical分離、未接続項目、dirty Git保全 |
| G2要求 | `E2C85FF52F80D2DC9B54E101D823B2B639A0EFF8A5885144B43214FEC893B99E` | A01〜A06、NFR-01〜06 |
| G2トレーサビリティ | `AD8DF5F21743ED9DFEA5D9D2D1660636A3E24BBDADC27650F35D724E983B79D5` | 未実証行を一カード又は具体的リスクへ限定 |
| G3実現性 | `B260705BBD504F57D8DBB480168D586FC9CA16EE0CB48B5B709ECDF2A8B18BE8` | M01主候補、M04発動条件、M05安全停止 |
| G4制御設計 | `A7B21580D8110171D22F00222E4926E21601A5930BFC54AEB4D02000D4FA6AAC` | 役割→技術→根拠、W01〜W05、未実証範囲 |
| G4設計レビュー | `C5C6174637796DDD386C7B06A2618D980843F9D9A08FEB3E2D9F22D93E46AC1D` | G4出口と製品未受入の境界 |
| 運用規則・現行作業 | `62500493D49EA54259C395E1B147CD1DE6560E7FE2995F1321941894514B5F9B` / `B27FD51DCD920BAAD54B9BD3525998EAC16FA5FFD0A9451D87230B2783E071B2` | 実施・報告・停止、Day未選択 |

標準の参照基線は `HIPVG/ai_work_operating_standard` の `13065155999b799fdd2766630696d523fc53beaf`（v0.5）。テンプレート選択器は非規範であり、既存の本計画に必要な情報だけを統合する。

全カードは次を継承する。G6で広瀬剛が**一枚だけ**指定し、開始時に最新の人間指示、入力ハッシュ、Git状態、対象パス、費用0円、実行上限、既存未追跡資産を確認する。失敗時は次カードへ進まず、`IMPLEMENTATION`、`VALIDATION`、`DIAGNOSIS`、`AUTHORITY`のいずれか一つへ分類する。既存のdirty状態をreset、clean、移動、取込しない。fixture、実actor E2E、選択Dayの実環境結果を互いに代用しない。

## 3. G0〜G4への網羅対応と実施順序

| 根拠・未決 | この計画での扱い |
| --- | --- |
| G0 P01: 手動伝言を減らす | WC-05の通常レビューバスとWC-06の`manual_relay_count`で、通常経路の0回を測定可能にする。 |
| G0 P02/P03: 一DayのGo、未達条件からの作業・証拠 | WC-01（画面入口）、WC-02（同一run preflight）、WC-03（criterion/evidence）へ分離。 |
| G0 P04/P05: LocalLLM提案を無審査実行せず、許可内修正・再検証 | WC-04で提案→scope/Git/budget guard→再検証を扱い、上限後はM05へ戻す。 |
| G0 P06: 状況・停止・次の動き | WC-07（read-only API）とWC-08（画面）でcurrent/historicalを区別。 |
| G0 P07: 既存資産を使い過剰基盤化しない | M01を再利用。M04はWC-05でM01の実actor失敗が確認された場合だけG3へ差し戻す。 |
| G0 P08: 有用性を損なわず費用・試行を扱う | WC-02でGo前上限、WC-06〜08で実測値・出所・未知値を扱う。 |
| G0/G2: Day 1〜14を一括実行せず安全に扱う | WC-09で各Dayの契約・証拠・scope・preflight入力を実行なしに受入点検し、欠けるDayはGo不能として残す。 |
| G1: 条件付き再利用、liveと保存状態を混同しない | WC-01〜08は既存資産の限定検証／最小補修に限定し、run IDと時点で分ける。 |
| G1: live service／Watcher／外部認証の未証明 | WC-02は実行主体・runtime前提をfail-closedにし、WC-05だけが実actorのWatcher・配送状態を確認する。保存値だけで稼働としない。 |
| G2: A01〜A06、NFR-02/03が未実証 | A01=WC-01/02、A02=WC-03、A03=WC-04、A04/NFR-03=WC-05、A06=WC-06、A05/A06=WC-07/08、Day範囲安全性=WC-09、実受入=WC-10。 |
| G3: M01条件付き、M04未評価、M05必須 | WC-05はM01だけを確認し、失敗時はM04を自動実装せずM05停止→G3再評価。 |
| G4: W01〜04は限定fixture、UI・修正成功・全Evidence型・M04は未実証 | fixture PASSを再利用しつつ、各未実証範囲を対応カードへ明記。WC-10以外で製品E2Eを主張しない。 |
| G0 M6: AI自己申告では受入しない | 各WCの決定的受領証跡、ChatGPTのレビュー、WC-10の実環境証拠を分け、同一ChatGPTの兼務を独立確認と表示しない。 |

実施順は、**利用者入口と安全なGo → 証拠判定 → 修正・復帰 → レビュー継続 → 実施指標 → API/画面 → 選択Day受入**とする。

| 順位 | カード | 対応 | 実施可能化条件 |
| --- | --- | --- | --- |
| 1 | G5-WC-01 | A01: UI選択・Goの命令契約 | G6一枚指定 |
| 2 | G5-WC-02 | A01/NFR-02/03: server preflight・同一run | WC-01の契約確認 |
| 3 | G5-WC-03 | A02: typed evidenceとcriterion判定 | WC-02のrun境界確認 |
| 4 | G5-WC-04 | A03/P04/P05: bounded repair→revalidation | WC-03の判定境界確認 |
| 5 | G5-WC-05 | A04/NFR-03: 通常レビュー配送・同一Day継続 | 外部配送を伴うカードのG6指定 |
| 6 | G5-WC-06 | A06/P01/P08: runテレメトリ契約 | WC-02のrun ID契約 |
| 7 | G5-WC-07 | A05/A06: read-only API投影 | WC-06の契約検証済み |
| 8 | G5-WC-08 | A05/A06: ダッシュボード表示 | WC-07のAPI検証済み |
| 9 | G5-WC-09 | Day 1〜14: 契約・preflight入場管理 | WC-02/03の境界確認 |
| 10 | G5-WC-10 | A01〜A06: 選択Dayの受入E2E | Day番号と製品利用Goの明示 |

## 4. 作業カード

### G5-WC-01 — UIのDay選択・Go命令契約

| 項目 | 内容 |
| --- | --- |
| 担当／入力版 | CODEX。第2節入力と最新の`frontend/index.html`、`frontend/app.js`。 |
| 目的 | 選択Dayだけがselect/start要求となり、ロード・履歴表示・推奨表示・別DayでGoが暗黙発火しないことを定義・検証する。 |
| 対象／非目的 | 対象はfrontendとUI契約テスト。backend状態変更、Day実行、新UI基盤、複数Day操作は対象外。 |
| 前提／許可操作 | G6一枚指定。対象フロントエンドとtest fixtureを最大2回編集・実行、費用0円。 |
| 禁止 | 実Day start、ネットワーク追加、React/Node導入、画面以外の範囲拡大。 |
| 結果／検証 | selectとGoのDay一致、起動時POSTなし、Go後に同一run IDを読む契約をDOM/fetch stubで記録する。 |
| 停止・後始末・次状態 | API契約変更が必要なら停止してWC-02へ判断を戻す。fixture以外を保存しない。`WC-01_VALIDATED`又は`WC-01_STOPPED`。 |

### G5-WC-02 — server preflight・同一run境界

| 項目 | 内容 |
| --- | --- |
| 担当／入力版 | CODEX。WC-01受領記録、`backend/app.py`、`backend/orchestrator/engine.py`、`backend/control/local_llm_day_program.py`、`backend/control/day_git.py`。 |
| 目的 | Goを選択Day・契約fingerprint・run ID・current/historical時点を固定したPREFLIGHTへ接続し、対象パス、Git基線、時間、試行、費用、外部効果、実行主体の有効権限が未許可又は未確認ならDay作業前に拒否する。 |
| 対象／非目的 | server側のguard/preflightと決定的テスト。Day仕事、モデル、LocalLLM-Lab変更、予算増額、永続基盤変更は対象外。 |
| 前提／許可操作 | G6一枚指定。対象コード／既存テストの限定編集・実行を各2回、費用0円。dirty Git又は`SMOKE_RECONCILIATION_REQUIRED`はGit-first停止。 |
| 禁止 | dirty作業のreset/clean、未選択Dayの補完、上限の推測、Day start、外部送信。 |
| 結果／検証 | 未選択・不一致Day・dirty基線・上限未設定・historicalのみ・実行主体の権限未確認をfail-closedにし、許可済みfixtureでは一意run IDとPREFLIGHTだけを記録する。 |
| 停止・後始末・次状態 | guardが対象外の権限や状態移行を要するなら`AUTHORITY`へ停止。実runは作らない。`WC-02_VALIDATED`又は`WC-02_STOPPED`。 |

### G5-WC-03 — criterion/evidenceの完了判定境界

| 項目 | 内容 |
| --- | --- |
| 担当／入力版 | CODEX。WC-02受領記録、`backend/models/local_llm_day.py`、`backend/control/evidence_registry.py`、`backend/control/local_llm_day_program.py`、既存テスト。 |
| 目的 | criterionは同一run・同一契約に紐づく型付き・validator済みEvidenceだけで満たされ、exit 0、静的表示、自己申告、過去保存値でCOMPLETEにならないことを検証する。 |
| 対象／非目的 | Evidence Record、validator、互換性、gap診断。全Evidence型、実Day成果生成、画面変更は対象外。 |
| 前提／許可操作 | G6一枚指定。対象契約・fixture・テストを各2回まで、費用0円。 |
| 禁止 | 過去Day証拠の補完、criterion緩和、証拠削除、Day/モデル起動。 |
| 結果／検証 | 完全・部分・空・未検証・run/契約不一致のvalidator結果と、完了拒否又はgap記録。 |
| 停止・後始末・次状態 | 選択Day固有adapterが必要なら`INPUT_BLOCKED`にし、一般契約を推測で拡張しない。fixtureのみ保全。`WC-03_VALIDATED`、`INPUT_BLOCKED`又は`WC-03_STOPPED`。 |

### G5-WC-04 — 許可内修正から再検証への復帰

| 項目 | 内容 |
| --- | --- |
| 担当／入力版 | CODEX。WC-03受領記録、`backend/control/local_llm_day_program.py`、`backend/control/day_action_executor.py`、`backend/control/scope_guard.py`、`backend/control/day_git.py`、既存テスト。 |
| 目的 | LocalLLM提案を非権威入力とし、許可修正だけがscope/Git/budget/retry検査を通過して再検証へ戻り、同一失敗二回又は上限到達時はM05の人間判断へ停止することを確認する。 |
| 対象／非目的 | bounded repair、Repair Episode、revalidation、authority packet。実Day修正、LocalLLM呼出し、範囲外ファイル、修正成功率の一般化は対象外。 |
| 前提／許可操作 | G6一枚指定。決定的fixtureと対象テストを各2回、費用0円。 |
| 禁止 | 無審査提案適用、三度目の同一小修正、実リポジトリ変更、失敗結果の隠蔽。 |
| 結果／検証 | 許可fixture修正→revalidation、拒否→停止、同一失敗二回→人間判断→matching reviewer確認→同じselected DayのPREFLIGHT再検査、の各経路を区別して記録。停止だけのW03を修正成功の証明にしない。 |
| 停止・後始末・次状態 | reviewer確認なしの人間判断は再開権限にしない。実修正に選択Dayの別権限が必要なら停止。fixture以外を残さない。`WC-04_VALIDATED`、`INPUT_BLOCKED`又は`WC-04_STOPPED`。 |

### G5-WC-05 — 通常レビューバスと再起動横断の一意継続

| 項目 | 内容 |
| --- | --- |
| 担当／入力版 | CODEXが手順・実装、ChatGPTがレビュー／検証。`backend/control/reviewer_bus.py`、`tests/test_reviewer_bus.py`、Review Bridge PR #1、Watcher状態。 |
| 目的 | 通常報告を人間のコピペなしに`SENT`→`RECEIVED`→`APPLIED`→`VERIFIED`へ進め、同一`REPORT_ID`だけを一度適用し、再起動後も重複外部効果を生まないことを実actorで確認する。 |
| 対象／非目的 | M01の既存レビューバス、Watcher、相関・期限・再開記録。M04新設、composer利用、複数outstanding、Day状態の直接変更は対象外。 |
| 前提／許可操作 | G6で本カードを指定、outstanding=0、既存認証・費用0円・通常Review Bridge経路が使えること。一件reportと最大一回の安全な再開確認。通常報告は既存規則に従い追加の人間伝言承認を要しない。新認証・新配送先・費用・相関不能だけは人間判断。 |
| 禁止 | 認証迂回、無制限再試行、応答なしを承認扱い、M04先行導入。 |
| 結果／検証 | report/reply ID、PRコメントID、時刻、Watcher検知・適用、再起動後の重複なし。相関不一致・二重配送はfail-closed。 |
| 停止・後始末・次状態 | M01実actor失敗時はM05停止しM04を実装せずG3再評価へ戻す。outstanding reportを残さない。`WC-05_VALIDATED`、`G3_REEVALUATION_REQUIRED`又は`WC-05_STOPPED`。 |

### G5-WC-06 — runテレメトリ契約

| 項目 | 内容 |
| --- | --- |
| 担当／入力版 | CODEX。WC-02受領記録、`backend/models/local_llm_day.py`、`backend/control/local_llm_day_program.py`、状態永続化境界。 |
| 目的 | 一runに`manual_relay_count`、理由必須の`manual_interventions`、試行数、許可上限と実測値、token・費用と出所、収集時点、current/historical種別を保存する。未知値をゼロ・成功・完了に変換しない。 |
| 対象／非目的 | run-scoped Pydantic/JSON契約と既存テスト。課金基盤、token推定、UI、実Dayの事実補完、全状態移行は対象外。 |
| 前提／許可操作 | G6一枚指定。対象契約と既存テストを各2回まで、費用0円。 |
| 禁止 | `manual_relay_count=0`の推測、既存run書換え、Day/モデル実行、外部送信。 |
| 結果／検証 | JSON往復、run混在拒否、理由なし介入拒否、未知値保持、上限値と実測値・出所の区別。 |
| 停止・後始末・次状態 | 保存互換性又は権威出所を定められなければ人間判断へ停止。実run状態は変更しない。`WC-06_VALIDATED`又は`WC-06_STOPPED`。 |

### G5-WC-07 — current/historicalを分ける読み取りAPI

| 項目 | 内容 |
| --- | --- |
| 担当／入力版 | CODEX。WC-06受領記録、`backend/app.py`、既存engineの読み取り境界、APIテスト。 |
| 目的 | 同一run IDのcurrent状態、historical状態、停止理由、次行為、WC-06値と出所をread-only APIで返す。 |
| 対象／非目的 | API投影とテスト。書込みAPI、Dayのselect/start/resume、認証方式、Watcher仕様変更は対象外。 |
| 前提／許可操作 | `WC-06_VALIDATED`とG6一枚指定。対象API・テストを各2回、費用0円。 |
| 禁止 | historicalをcurrentと偽装、保存値だけで稼働と表示、外部通信、M04導入。 |
| 結果／検証 | 空・未選択・保存済み・不整合・未知値で、run ID・時点・出所を欠かさず書込みなしに返すAPI証跡。 |
| 停止・後始末・次状態 | 読み取り境界を越える状態変更が必要なら停止。サーバー実行状態を残さない。`WC-07_VALIDATED`又は`WC-07_STOPPED`。 |

### G5-WC-08 — 現在状態を優先するダッシュボード

| 項目 | 内容 |
| --- | --- |
| 担当／入力版 | CODEX。WC-07受領記録、`frontend/index.html`、`frontend/app.js`、UI確認手順。 |
| 目的 | Day、run ID、未達criterion、current/historical、次行為、待機・判断待ち・停止、手動中継・介入・試行・token・費用と出所を誤認なく表示する。 |
| 対象／非目的 | UI表示とDOM/API-stub確認。Go権限、backend契約、新フレームワーク、別Day一括表示は対象外。 |
| 前提／許可操作 | `WC-07_VALIDATED`とG6一枚指定。frontendと静的確認を各2回、費用0円。 |
| 禁止 | Go暗黙発火、未知値のゼロ表示、歴史値の現在化、React/Node導入、実Day開始。 |
| 結果／検証 | 未選択、PREFLIGHT、停止、判断待ち、介入あり、値不明、履歴ありの各表示をAPI応答と画面証跡で照合する。 |
| 停止・後始末・次状態 | APIが必要な意味を供給しない場合はWC-07へ戻して停止。fixture以外を残さない。`WC-08_VALIDATED`又は`WC-08_STOPPED`。 |

### G5-WC-09 — Day 1〜14の契約・preflight入場管理

| 項目 | 内容 |
| --- | --- |
| 担当／入力版 | CODEX。WC-02/03受領記録、`config/local_llm_day_program.yaml`、各Day contract/runbook、`backend/control/local_llm_day_program.py`、既存テスト。 |
| 目的 | Day 1〜14について、選択可能な各Dayが契約版、required Evidence、許可scope、上限、PREFLIGHT入力を持つことを点検し、欠けるDayを自動実行も受入可能とも表示しない。 |
| 対象／非目的 | Day catalog/contract/read-only admission test。Dayの仕事、モデル、全Day一括Go、既存Day結果の再評価、LocalLLM-Lab変更は対象外。 |
| 前提／許可操作 | G6一枚指定。設定・契約・fixtureの限定読取／テストを各2回、費用0円。 |
| 禁止 | Day選択・Go、契約欠落の推測補完、全Dayの一括実行、既存証拠の書換え。 |
| 結果／検証 | 各Dayの`ADMISSIBLE`又は具体的な`BLOCKED`理由、契約／Evidence／scope/preflight入力の対応表を受領証跡とする。`ADMISSIBLE`は実行済み又は受入済みを意味しない。 |
| 停止・後始末・次状態 | Day固有入力が不明なら当該Dayだけ`INPUT_BLOCKED`にする。別Dayへ代替して実行しない。変更なし。`WC-09_VALIDATED`又は`WC-09_STOPPED`。 |

### G5-WC-10 — 選択Dayの製品受入E2E

| 項目 | 内容 |
| --- | --- |
| 担当／入力版 | 広瀬剛が製品利用としてDay番号とGoを明示、CODEXが実施、ChatGPTがレビュー／検証。選択Dayのrunbook・契約・WC-01〜09受領記録。 |
| 目的 | 一つの選択DayについてA01〜A06を一連で照合し、安全、実施、自動修復、人間判断要請、証拠、停止、復旧、手動中継0回の測定を製品受入根拠にする。 |
| 対象／非目的 | 選択Dayの契約、既存制御、証拠、レビュー、テレメトリ、画面。別Day自動開始、複数Day並列、モデル品質一般化、未承認修正、費用発生は対象外。 |
| 前提／許可操作 | Day番号、製品利用Go、受入環境、時間・試行・費用上限、必要な認証を広瀬剛が明示。一Day・その上限内のみ。 |
| 禁止 | 開発G6指示を製品Goとみなすこと、選択外Day、暗黙再試行、証拠なし完了、停止後の自動再開。 |
| 結果／検証 | UI操作、run ID、PREFLIGHT、criterion/Evidence、修正又は停止、review ID状態、介入理由、token/cost出所、最終表示を同一runで照合。fixture・過去Day・exit 0だけでは受入にしない。 |
| 停止・後始末・次状態 | 同一失敗二回、認証／費用／範囲外、証拠不足ではM05の人間判断へ停止し、同一Dayの安全な復帰先を提示。次Dayへ遷移しない。現状`INPUT_BLOCKED`。 |

## 5. テスト計画と合格判定

| カード | 検証層 | 合格証拠 | 製品E2Eとの関係 |
| --- | --- | --- | --- |
| WC-01 | UI stub/DOM | 選択Day一致、暗黙POSTなし、同一run読取契約 | UI部品確認のみ |
| WC-02 | server fixture | PREFLIGHT、run ID、上限・Git拒否 | Day仕事を起動しない |
| WC-03 | validator fixture | typed Evidence以外でCOMPLETE拒否 | 全Evidence型・実Day証明ではない |
| WC-04 | guarded repair fixture | repair→revalidation、拒否→停止、二回→判断 | 実修正成功率を主張しない |
| WC-05 | fixture + 実actor一回 | ID相関、再起動後の一意継続 | M01不成立ならG3へ戻す |
| WC-06 | model/JSON | relay/介入/上限/実測/出所の保持 | 実値はWC-09で測定 |
| WC-07 | API | current/historical・未知値・read-only | UI受入ではない |
| WC-08 | UI/API stub | 状態別表示とAPI照合 | 実Day受入ではない |
| WC-09 | catalog/contract fixture | Day別の入場可否と`BLOCKED`理由 | Day実行・製品受入ではない |
| WC-10 | 選択Day実環境 | A01〜A06の同一run証拠 | 製品受入の唯一の統合証拠 |

いずれも失敗時はfail-closedとし、次カード・次Dayへ進まない。テスト件数、終了コード、保存状態、AI自己報告は単独の合格根拠にしない。

## 6. M04発動規則とG5出口

M04（durable outbox/reconciler）は、WC-05でM01が実actorの同一report ID、再起動横断の一意継続を満たせないと確認された場合だけ、M05で停止した後にG3へ戻して再評価する。M04を「念のため」実装するカードは置かない。

G5の出口は、A01〜A06/NFRとG0 P01〜P08、G1の再利用・未接続、G3の候補／代替／安全停止、G4の限定PASS／未実証が、各々一つ以上の独立カード又は明示的`INPUT_BLOCKED`へ対応し、各カードが入力・目的・対象・非目的・前提・許可上限・禁止・受領証跡・検証・停止・後始末・次状態を持つこととする。WC-09はDay 1〜14の安全な入場管理、WC-10は一つの明示選択Dayの製品受入であり、どちらも全Day一括実行を許可しない。

本書の自己確認は `ARTIFACT_QUALITY_CHECK: SELF_CHECK_PASS`。ChatGPTレビューの受理前にG5完了、G6許可、Day実行、製品受入を主張しない。
