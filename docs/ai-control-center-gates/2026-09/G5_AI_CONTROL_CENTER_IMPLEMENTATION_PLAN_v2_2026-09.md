# G5 — AI-Control-Center 実装計画・作業カード・検証計画 v2

- 文書ID: `G5-ACC-PLAN-20260928-003`
- 状態: `REVISED_REVIEW_PENDING`（v2.2の承認対象・再確認カードを追加。004の固定commitを保持し、改訂版は別途提出待ち）
- 行為分類: `DIAGNOSIS`（実装前の作業計画化）
- 計画・実装担当: CODEX
- 人間の責任者・最終判断: 広瀬剛
- レビュー／検証: ChatGPT（同一主体の兼務を独立検証とは表示しない）
- 人間承認: 2026-09-28。G4 v2観測補遺および本改訂計画を広瀬剛が承認。広瀬剛はG0〜G5成果物を専用ブランチの固定commitでレビュー可能にする運用設計も指示した。G5のReviewer確認は待機中。
- 最新Reviewer応答: `IN_REPLY_TO: G5-ACC-REVIEW-20260928-003`、`RESULT: REJECT`。G4本文と人間承認の外部追跡可能性が`NOT EVALUABLE`だったためである。本v2.1は固定commit・正本区分・承認source classを追加するが、外部参照のない会話指示を独立検証済みとは主張しない。
- 設計正本: `docs/ai-control-center-gates/2026-09/G4_AI_CONTROL_CENTER_FUNCTIONAL_CONTROL_DESIGN_v2_2026-09.md`
- 旧計画: `docs/ai-control-center-gates/2026-09/superseded/G5_AI_CONTROL_CENTER_IMPLEMENTATION_PLAN_2026-09.md` は承認前設計に基づくため `SUPERSEDED_BY_G5_V2` として保全する。

## 1. G5の目的・許可境界

G5の目的は、G4 v2で固定された機能・制御設計を、単独で実施、検証、停止できる最小の作業単位にすることである。機能を追加で決める工程ではない。各カードはG4の既定経路を実装又は検証へ移すだけであり、要求、役割、状態遷移、代案の発動条件を変更しない。

広瀬剛による2026-09-28の「G4を承認します。G5を開始してください。」は、この計画化までを許可する。G6のコード実装、テスト実行、サービス起動停止、Day選択／Go、モデル実行、外部配送、認証変更、費用発生、Git commit／push、製品受入は許可しない。G6では、人間が一枚のカードを明示選択して初めて、そのカードだけを開始できる。開発指示は製品利用者のGoではない。

## 2. 入力基線と共通保護

| 入力 | SHA-256 | この計画での使い方 |
| --- | --- | --- |
| G0プロジェクト定義 | `E4A2C224B0DCF94B9126917A4EDE366785BE39FFD025645986B5B3129CB11F8F` | P01〜P08、役割、製品目的をカードの網羅基準にする。 |
| G1現状 | `D39E08D5A1FABFD9B4ABEAA3AAE4B82B0505F5F887890F0329FD71FBB7BFB3B9` | 既存資産は条件付き再利用とし、保存値を稼働／受入根拠にしない。 |
| G2要求 | `E2C85FF52F80D2DC9B54E101D823B2B639A0EFF8A5885144B43214FEC893B99E` | A01〜A06、NFR-02/03を受入・証拠境界へ対応付ける。 |
| G3実現性 | `B260705BBD504F57D8DBB480168D586FC9CA16EE0CB48B5B709ECDF2A8B18BE8` | M01を主候補、M04を条件付き再評価、M05を停止とする。 |
| G4 v2機能・制御設計（v2.2補遺を含む） | `0993F29730566B86D476263CF7AA6512C64066B8A087A2C37E166957F6CABE53` | 本計画の唯一の機能設計正本。固定commit・対象path・hash・承認source classによるレビュー入力を追加する。 |
| 初回ReviewArtifactBaseline | `644d9dd579a69130dad3649c4b5160528398ac00` | `docs/ai-control-center-gates/2026-09/README.md`で現行正本・補助・撤回済みを区分した最初の公開commit。レビュー対象はbranch名だけでなく固定commitとする。 |
| 現行運用規則 | `62500493D49EA54259C395E1B147CD1DE6560E7FE2995F1321941894514B5F9B` | 実施、報告、停止、Reviewer Bridgeの規範。 |
| 標準 | `HIPVG/ai_work_operating_standard@13065155999b799fdd2766630696d523fc53beaf` | G5カード必須項目、工程境界を適用する。 |

全カードに共通する保護は次のとおりである。開始時に最新の人間指示、該当入力の再ハッシュ、対象パス、現行Git状態、既存の未追跡資産を確認する。dirty状態をreset、clean、移動又は取込みしない。上限は明示されない限り「対象検証を最大2回、費用0円」であり、tokenは実測できる場合だけ出所付きで記録し、未知値を0にしない。fixture、実actor、製品E2Eを互いの合格証拠に代用しない。

## 3. 網羅性と実施順序

| 順序 | カード | G4 v2との対応 | G0〜G3/G2への対応 |
| --- | --- | --- | --- |
| 1 | WC-00 reviewable artifact baseline | 12節 | G0〜G5の正本、承認、レビュー対象の版固定 |
| 2 | WC-01 Run contract | 4節のRunIntent/RunControl | P02/P03、A01、NFR-03 |
| 3 | WC-02 admission/preflight | 3・5.1・6節 | P02/P07、A01、NFR-02、M05 |
| 4 | WC-03 Day catalog | 3・4・8節 | Day 1〜14の安全な入場、G1の条件付き再利用 |
| 5 | WC-04 selection/Go UI | 5.1節 | P01/P02、A01 |
| 6 | WC-05 Evidence/completion | 3・4・5.2節 | P03/P04、A02 |
| 7 | WC-06 repair/recovery | 5.2・5.3・6節 | P04/P05、A03、M05 |
| 8 | WC-07 review control | 4・5.3・5.4・6節 | P01/P05、A04、NFR-03、M01/M04/M05 |
| 9 | WC-07A continuation observability | 4・5.4・6・12節 | A04、NFR-03、G3 SC-05 |
| 9の後 | WC-07B human decision binding | 13節 | P01/P05、A04、承認対象と適用範囲の分離 |
| 10 | WC-08 telemetry | 4・5.4節 | P06/P08、A06 |
| 11 | WC-09 read API | 3・4・5.4節 | P06、A05、NFR-03 |
| 12 | WC-10 dashboard | 5.4・5.5節 | P01/P06/P08、A05/A06 |
| 13 | VC-11 actor/E2E gate | 8・9・10・12節 | A04の実actor確認と、将来の選択Day受入の明確な`INPUT_BLOCKED`境界 |

この順序は主経路（admission→Go→preflight→Evidence→修正／レビュー→表示）を先に置く。可観測性は主経路の事実を表す後段とし、先行して製品能力を装わない。M04（durable outbox/reconciler）は、WC-07でM01が実actorの一意送達・一意継続を満たせないと確定した場合にだけ、M05で停止してG3へ戻す。予防的なM04実装カードは置かない。

## 4. 作業カード

### WC-00 — レビュー可能な成果物基線

| 項目 | 内容 |
| --- | --- |
| 担当／入力版 | CODEX。G4 v2.1 12節、`docs/WORKING_RULES.md`の単一outstanding規則、G0〜G5の現行正本。 |
| 目的 | G0〜G5のレビュー対象を、専用`agent/*` branch上の一つのimmutable commit、index、対象path、file hash、正本／補助／`SUPERSEDED`区分、承認根拠に固定する。 |
| 対象 | `docs/ai-control-center-gates/<baseline>/`、baseline index、ReviewArtifactBaseline、ReviewAuthorityRecord、Review Bridge報告のcommit binding。 |
| 非目的 | `main`変更、既存文書の削除、Day／モデル実行、製品機能追加、Watcher配送方式変更、承認原指示の捏造。 |
| 前提／許可操作 | 文書更新前に専用branchを作成し、対象ファイルだけをcommit/pushする。提出時はoutstanding reportが0で、reportごとに固定commitを一つだけ指定する。 |
| 禁止／費用 | branch名だけの指定、未commit内容のレビュー、レビュー中commitの差替え、旧`REPORT_ID`の再利用、他者の未関連変更のcommit。費用0円。 |
| 結果・受領証跡／検証 | Git remoteからindexと全必須pathを読め、indexの分類とfile hashがcommit内容に一致し、report/replyが同じcommitを明記すること。direct external referenceを持たない人間指示は`RECORDED_DIRECT_CONVERSATION`と表示する。 |
| 停止・判断／後始末・次状態 | commit、対象path、hash、承認根拠のいずれかを固定できなければ`WC-00_STOPPED`としてG4又は人間判断へ戻す。旧baselineは保全し、新baselineだけを`WC-00_VALIDATED`又は`REVIEW_PENDING`へ進める。 |

### WC-01 — RunIntent・RunControlの契約

| 項目 | 内容 |
| --- | --- |
| 担当／入力版 | CODEX。G4 v2 4節、G2 A01/NFR-03、現行 `backend/models/local_llm_day.py` とJSON永続化境界。 |
| 目的 | 一run・一selected Day・一契約fingerprintを表す`RunIntent`と、current/history/next action/blockerを表す`RunControl`の最小契約を作る。 |
| 対象 | `backend/models/local_llm_day.py`、状態永続化インターフェース、対応するモデルテスト。 |
| 非目的 | UI、Go API、Day作業、Evidence判定、既存履歴の移行、実行状態enumの追加。 |
| 前提／許可操作 | G6で本カードだけを明示選択。既存モデルと対象テストを各最大2回確認し、対象ファイルだけを変更する。 |
| 禁止／費用 | Day／モデル実行、外部送信、既存runの書換え、状態を保存値だけで稼働と表すこと。費用0円。 |
| 結果・受領証跡／検証 | versioned JSONの往復、run ID重複拒否、Day不一致拒否、current/history分離を対象テストで確認する。 |
| 停止・判断／後始末・次状態 | 互換性を壊さず表せない場合は`WC-01_STOPPED`として設計判断へ戻す。実runは作らず、fixtureを除去して`WC-01_VALIDATED`へ。 |

### WC-02 — DayAdmission・PREFLIGHT guard

| 項目 | 内容 |
| --- | --- |
| 担当／入力版 | CODEX。G4 v2 3、5.1、6節、G2 NFR-02、G3 M05。`backend/control/local_llm_day_program.py`、`backend/orchestrator/engine.py`、`backend/control/day_git.py`。 |
| 目的 | Go前にcontract、scope、Git基線、実効権限、時間・試行・費用、外部前提を決定的に判定し、未充足ならDay作業なしで停止する。 |
| 対象 | preflight関数とdeny理由、WC-01契約を使う対象テスト。 |
| 非目的 | UI、Day実行、Git修復、権限取得、予算の推測補完。 |
| 前提／許可操作 | `WC-01_VALIDATED`、G6で本カードを選択。対象fixture／テストを各最大2回。 |
| 禁止／費用 | reset/clean、scope外操作、上限超過、Day起動、認証変更、外部送信。費用0円。 |
| 結果・受領証跡／検証 | 合格は`PREFLIGHT`への遷移だけ、失格は保存されたblockerと停止先だけであることを、dirty Git・権限不明・上限未確定・契約不一致fixtureで示す。 |
| 停止・判断／後始末・次状態 | 判定に非決定的情報が必要なら`HUMAN_ACTION_REQUIRED`又は`EXTERNAL_ACTION_REQUIRED`で停止する。実Dayを残さず、`WC-02_VALIDATED`へ。 |

### WC-03 — Day 1〜14 admission catalog

| 項目 | 内容 |
| --- | --- |
| 担当／入力版 | CODEX。G4 v2 3、4、8節、G1現状。`config/local_llm_day_program.yaml`、Day contract/runbook読取、`backend/control/local_llm_day_program.py`。 |
| 目的 | 各Dayを個別に`ADMISSIBLE`又は具体的理由付き`BLOCKED`として表示可能にし、Go可能性と実行済みを混同しない。 |
| 対象 | read-only catalog/admissionと対応fixture。 |
| 非目的 | Day 1〜14の一括実行、契約欠落の補完、LocalLLM-Lab変更、過去Dayの再受入。 |
| 前提／許可操作 | `WC-02_VALIDATED`、G6で本カードを選択。設定・契約・fixtureを各最大2回読取／検証する。 |
| 禁止／費用 | Day選択／Go、モデル実行、証拠書換え、外部投稿。費用0円。 |
| 結果・受領証跡／検証 | Dayごとのcontract版、required Evidence、scope、preflight入力、admission理由の対応表をfixtureで照合する。 |
| 停止・判断／後始末・次状態 | Day固有情報が欠ければ当該Dayだけ`INPUT_BLOCKED`にして推測しない。変更されたfixture以外を残さず`WC-03_VALIDATED`へ。 |

### WC-04 — 選択・GoのUI/API入口

| 項目 | 内容 |
| --- | --- |
| 担当／入力版 | CODEX。G4 v2 5.1節、WC-01〜03受領記録。`frontend/index.html`、`frontend/app.js`、既存の対象API境界。 |
| 目的 | Day選択は外部効果なし、Goだけが同一run IDのRunIntentを作ってPREFLIGHTへ渡すという入口を実現する。 |
| 対象 | 選択表示、Go要求のpayload、対応するUI/API stubテスト。 |
| 非目的 | Day実行、予算決定、修正、ダッシュボード全面更新、新UI基盤。 |
| 前提／許可操作 | `WC-01_VALIDATED`〜`WC-03_VALIDATED`、G6で本カードを選択。DOM/API stub検証を各最大2回。 |
| 禁止／費用 | 選択時のPOST、暗黙Go、複数Day選択、React/Node導入、実serviceのDay操作。費用0円。 |
| 結果・受領証跡／検証 | 選択だけではrun／外部効果なし、Goはselected Dayと同一run IDでPREFLIGHTだけへ渡ることをstubで確認する。 |
| 停止・判断／後始末・次状態 | APIがWC-01/02の意味を表せないときは実装を広げず停止する。fixtureを残さず`WC-04_VALIDATED`へ。 |

### WC-05 — typed Evidence・完了判定

| 項目 | 内容 |
| --- | --- |
| 担当／入力版 | CODEX。G4 v2 3、4、5.2、6節、G2 A02。Evidence registry/validatorと対象テスト。 |
| 目的 | run ID、criterion、provider/validator版、fingerprint、時刻、validator結果を持つEvidenceだけが完了判定へ入るようにする。 |
| 対象 | Evidence Record、Result Adapter、validator、criterion evaluationの対象境界。 |
| 非目的 | 全Day Evidence型の実収集、exit 0の昇格、AI自己報告、過去証拠の上書き。 |
| 前提／許可操作 | `WC-01_VALIDATED`とG6のカード選択。対象fixture／テストを各最大2回。 |
| 禁止／費用 | Day／モデル実行、外部通信、Evidence欠落時のCOMPLETE、scope外データ収集。費用0円。 |
| 結果・受領証跡／検証 | 型不一致、空出力、exit 0のみ、run不一致ではCOMPLETEを拒否し、validator済みEvidenceでのみcriterionを満たすfixtureを示す。 |
| 停止・判断／後始末・次状態 | 既存Evidence互換性が未決なら`INPUT_BLOCKED`で停止する。実Day記録を作らず`WC-05_VALIDATED`へ。 |

### WC-06 — 許可内修正・再検証・人間判断復帰

| 項目 | 内容 |
| --- | --- |
| 担当／入力版 | CODEX。G4 v2 5.2、5.3、6節、G2 A03、G3 M05。Repair Supervisor/action guardと対象テスト。 |
| 目的 | Gap Diagnosis→scope/Git/budget/retry guard→限定修正→deterministic revalidation、又は同一失敗二回後の人間判断要求→matching review→同一Day PREFLIGHT復帰を実現する。 |
| 対象 | Repair Episode、failure/action fingerprint、guard、再検証状態遷移の対象テスト。 |
| 非目的 | 実Day修正成功の主張、三回目試行、判断なし再開、別Day遷移、範囲外修正。 |
| 前提／許可操作 | `WC-02_VALIDATED`と`WC-05_VALIDATED`、G6のカード選択。guarded fixtureを各最大2回。 |
| 禁止／費用 | LocalLLM提案の無審査実行、Git復元、Day／モデル実行、外部送信。費用0円。 |
| 結果・受領証跡／検証 | scope外拒否、二回後の`HUMAN_ACTION_REQUIRED`、matching review後も同一run・DayのPREFLIGHTから再開するfixtureを確認する。 |
| 停止・判断／後始末・次状態 | 修正権限・費用・基線が不足すればM05停止する。実修正を残さず`WC-06_VALIDATED`又は`WC-06_STOPPED`へ。 |

### WC-07 — Review Control・Watcher連携

| 項目 | 内容 |
| --- | --- |
| 担当／入力版 | CODEX。G4 v2 4、5.3〜5.5、6、7節、G2 A04/NFR-03。`backend/control/reviewer_bus.py`、Watcher連携境界、対象テスト。 |
| 目的 | report ID、outstanding、`SENT/RECEIVED/APPLIED/VERIFIED`、期限、再開相関をDay stateから分離し、一件だけの一致返信だけを適用する。 |
| 対象 | Review Controlデータ／ガード、Watcherへの受渡し、fixture。 |
| 非目的 | ChatGPT composer、複数outstanding、Day state直接更新、M04導入、実際の外部報告配送。 |
| 前提／許可操作 | `WC-01_VALIDATED`、`WC-06_VALIDATED`、G6のカード選択。対象fixtureを各最大2回。 |
| 禁止／費用 | 不一致／期限超過を承認扱い、人間コピーを通常経路にすること、無制限再試行。費用0円。 |
| 結果・受領証跡／検証 | duplicate、wrong `IN_REPLY_TO`、Watcher不在、期限超過でfail-closedになるfixtureを示す。実actor送達はVC-11だけで扱う。 |
| 停止・判断／後始末・次状態 | M01の実actor不成立がVC-11で確定した場合だけM05停止→G3再評価。outstandingを残さず`WC-07_VALIDATED`へ。 |

### WC-07A — Review continuation観測契約

| 項目 | 内容 |
| --- | --- |
| 担当／入力版 | CODEX。G4 v2 4、5.4、6、11節、G2 A04/NFR-03、G3 SC-05。`backend/control/reviewer_bus.py`、`state/reviewer-bus-watcher.json`の状態契約、対象テスト。 |
| 目的 | `RECEIVED_PENDING_APPLY`、`APPLYING`、`APPLIED`、`VERIFIED`、`CONTINUATION_FAILED`、`DELIVERY_FAILED`を、対応ID・時刻・現在行為・継続envelope検証・後続report/comment IDとともに記録し、途中状態と完了を混同させない。 |
| 対象 | Review Control状態モデル、Watcher state schema、read modelへの最小投影、対象fixture。 |
| 非目的 | Day state変更、Watcherの配送方式変更、認証保存方式の変更、トークン記録、M04導入、dashboard意匠変更。 |
| 前提／許可操作 | `WC-07_VALIDATED`とG6での本カード選択。状態fixture／対象テストを各最大2回。実actor投稿はVC-11でのみ扱う。 |
| 禁止／費用 | exit 0だけを`APPLIED`又は`VERIFIED`にすること、秘密値の保存、実行主体が異なる認証可用性を成功扱いすること、Day／モデル実行。費用0円。 |
| 結果・受領証跡／検証 | 一致応答受信、継続実行中、無効envelope、exit 0かつ後続配送なし、後続report検証済みの各fixtureで、状態・時刻・理由・次行為を一意に読めること。 |
| 停止・判断／後始末・次状態 | 実行主体ごとの認証可用性が不一致なら`AUTH_CONTEXT_MISMATCH`で外部配送を止める。秘密値や実reportを残さず、`WC-07A_VALIDATED`又は`WC-07A_STOPPED`へ。 |

### WC-07B — 承認対象・人間返答・Reviewer再確認

| 項目 | 内容 |
| --- | --- |
| 担当／入力版 | CODEX。G4 v2.2 13節、WC-00/07/07A、既存の`backend/control/reviewer_bus.py`、JSON保存境界、対象fixture。 |
| 目的 | Reviewer提案への賛同、Codex成果物受入、G出口、実施許可を区別し、人間返答だけでClose又は次工程開始にならない契約を実現する。 |
| 対象 | HumanDecisionと対象ガード、チャット／PR受信adapter境界、確認報告payloadと送信待ち・重複防止。投稿者だけで人間と断定しない出所記録。 |
| 非目的 | 自然言語の推測による承認、承認原文の創作、UI全面変更、運用規則の無断変更、実Day・実外部投稿。 |
| 前提／許可操作 | WC-00の版固定、`WC-07_VALIDATED`、`WC-07A_VALIDATED`、G6で本カードを明示選択。対象fixtureを最大2回、費用0円。 |
| 禁止／費用 | 単一pendingや直前発言だけでの対象決定、Reviewer未確認のClose、対象外への権限拡張、同時複数outstanding。費用0円。 |
| 結果・受領証跡／検証 | 下記H01〜H08のfixtureで、対象、返答原文、出所、確認報告、一致応答、許された効果、停止理由を照合する。送信前／応答前には適用しない。 |
| 停止・判断／後始末・次状態 | 対象不明は`HUMAN_RESPONSE_UNCLASSIFIED`で対象だけ確認。不一致・期限超過・配送失敗は理由付き待機。fixtureだけを後始末し証跡を保持、`WC-07B_VALIDATED`又は`WC-07B_STOPPED`へ。 |

### WC-08 — run telemetry契約

| 項目 | 内容 |
| --- | --- |
| 担当／入力版 | CODEX。G4 v2 4、5.4節、G2 A06。`backend/models/local_llm_day.py`、JSON永続化境界、対象テスト。 |
| 目的 | `manual_relay_count`、理由付き介入、試行／上限、token・費用・出所・時点を同一runに保存し、未知値を保持する。 |
| 対象 | Run Telemetryモデル、JSON往復、入力検査。 |
| 非目的 | token推定、課金基盤、実Day事実の補完、UI表示。 |
| 前提／許可操作 | `WC-01_VALIDATED`、G6のカード選択。対象テストを最大2回。 |
| 禁止／費用 | `0`の推測、既存runの書換え、外部送信、Day／モデル実行。費用0円。 |
| 結果・受領証跡／検証 | 理由なし介入拒否、run混在拒否、上限と実測・出所の分離、unknown保持をモデルテストで確認する。 |
| 停止・判断／後始末・次状態 | 権威ある出所を定められない値はunknownのまま停止する。実runを作らず`WC-08_VALIDATED`へ。 |

### WC-09 — read-only current/historical API

| 項目 | 内容 |
| --- | --- |
| 担当／入力版 | CODEX。G4 v2 3、4、5.4節、WC-01/05/07/08。`backend/app.py`、read model、APIテスト。 |
| 目的 | run ID、admission、current/history、未達criterion、next action、review、telemetryと出所を、書込みなしで返す。 |
| 対象 | read-only API投影とテスト。 |
| 非目的 | 選択／Go、状態更新、認証方式変更、Watcher仕様変更。 |
| 前提／許可操作 | `WC-05_VALIDATED`、`WC-07A_VALIDATED`、`WC-07B_VALIDATED`、`WC-08_VALIDATED`、G6のカード選択。対象APIテストを最大2回。 |
| 禁止／費用 | historicalをcurrentと表示、保存値だけで稼働と断言、外部通信。費用0円。 |
| 結果・受領証跡／検証 | 未選択、PREFLIGHT、停止、unknown、履歴あり、不整合でrun ID・時刻・出所を欠かさず返すAPI証跡。判断ID、種類、対象commit、効果、人間返答とReviewer確認の別状態も返す。 |
| 停止・判断／後始末・次状態 | 書込みが必要になる設計なら停止してG4へ戻す。serviceを残さず`WC-09_VALIDATED`へ。 |

### WC-10 — Dashboard projection

| 項目 | 内容 |
| --- | --- |
| 担当／入力版 | CODEX。G4 v2 5.4、5.5節、WC-04/08/09。`frontend/index.html`、`frontend/app.js`、UI確認手順。 |
| 目的 | selected Day、run ID、admission、current/history、未達、次行為、停止／判断、review、relay・介入・試行・token・費用と出所を誤認なく表示する。 |
| 対象 | read-only dashboard projectionとDOM/API stub確認。 |
| 非目的 | Go権限、backend契約、新フレームワーク、Day実行、通知自動再試行。 |
| 前提／許可操作 | `WC-04_VALIDATED`、`WC-08_VALIDATED`、`WC-09_VALIDATED`、G6のカード選択。静的／stub確認を最大2回。 |
| 禁止／費用 | Go暗黙発火、unknownのゼロ表示、historicalのcurrent化、React/Node導入。費用0円。 |
| 結果・受領証跡／検証 | 未選択、PREFLIGHT、停止、判断待ち、介入あり、unknown、履歴ありをAPI応答と画面証跡で照合する。「何への承認か」「承認で許すこと」「Reviewer確認待ち」を表示し、人間返答のみを完了表示にしない。 |
| 停止・判断／後始末・次状態 | APIが必要な意味を提供しないならWC-09へ戻して停止する。fixture以外を残さず`WC-10_VALIDATED`へ。 |

### VC-11 — 実actorレビュー検証と選択Day受入ゲート

| 項目 | 内容 |
| --- | --- |
| 担当／入力版 | CODEX、ChatGPTレビュー／検証、広瀬剛は製品利用権限の判断者。G4 v2 8〜10節、WC-01〜10の受領証跡、Review Bridge PR #1。 |
| 目的 | WC-07のfixture根拠と実actor根拠を分け、通常配送の一意送達・一意適用だけを確認する。選択Day製品受入に必要な追加入力を明示する。 |
| 対象 | WC-07B検証済みを前提に、一件の許可済み確認報告（判断ID・出所・対象版付き）とmatching response、Watcherのactor trace。将来の選択Day E2E受入条件表。 |
| 非目的 | Day選択／Go、Day実行、モデル実行、修正、M04実装、複数報告、費用発生。 |
| 前提／許可操作 | G6で本カードを選択し、outstanding=0、既存認証、費用0円、運用規則の配送条件を満たすこと。選択Day E2Eには別途、Day番号、製品Go、環境、時間・試行・費用、認証の人間明示が必要。 |
| 禁止／費用 | 応答なし／ID不一致を受理、人間の通常中継、M01失敗時のM04自動導入、Day開始。費用0円。 |
| 結果・受領証跡／検証 | report/reply ID、コメントID、時刻、Watcherの検知・適用、重複なしを同一相関で確認する。選択Day E2Eはその入力が揃うまで`INPUT_BLOCKED`のままにする。 |
| 停止・判断／後始末・次状態 | M01が実actorで不成立ならM05停止しG3再評価へ戻す。reportを残さず、`VC-11_VALIDATED`、`G3_REEVALUATION_REQUIRED`又は`INPUT_BLOCKED`へ。 |

## 5. テスト計画と証拠の層

| カード | 層 | 合格証拠 | 合格が意味しないこと |
| --- | --- | --- | --- |
| WC-00 | Git公開・読取 | index、固定commit、対象path/hash、正本区分、report/replyの同一commit binding | 人間原指示の独立検証、G5受理、製品実装 |
| WC-01 | model/JSON | run一意性、current/history分離 | UI又はDay実行の成功 |
| WC-02 | deterministic fixture | preflight許可／拒否と停止理由 | 実権限・実Dayの受入 |
| WC-03 | catalog fixture | Dayごとのadmission／blocker | Day 1〜14の実行 |
| WC-04 | UI/API stub | 選択の無副作用、Go→PREFLIGHT | 実Day Go |
| WC-05 | validator fixture | typed Evidenceのみでcriterion達成 | 全Evidence型・実Dayの証明 |
| WC-06 | guarded-repair fixture | 二回上限、停止、同一Day復帰先 | 実修正成功率 |
| WC-07 | reviewer-control fixture | 一件制限、不一致／期限の拒否 | 実actor配送 |
| WC-07A | reviewer continuation fixture | 受信中／適用中／適用済み／失敗、envelope、後続IDの区別 | 実actor配送又は認証の実利用 |
| WC-07B | human decision fixture | H01〜H08、対象別効果、一致応答前のClose拒否 | 実人間の認証、実actor配送、G出口承認 |
| WC-08 | model/JSON | relay／介入／unknown／出所の保存 | 実測値の取得 |
| WC-09 | API | read-only、current/history・時点・出所 | UI受入 |
| WC-10 | UI/API stub | 状態別の誤認しない表示 | 稼働又は製品受入 |
| VC-11 | 実actor一回 | matching ID、継続envelope、後続comment、Watcher trace | 選択Dayの製品E2E |
| 将来の製品受入 | 選択Day実環境 | A01〜A06を同一runで照合 | 他Dayへの一般化 |

失敗したカードは次カードへ進まず、`IMPLEMENTATION`、`VALIDATION`、`DIAGNOSIS`又は`AUTHORITY`に分類する。終了コード、テスト件数、保存状態、AI自己報告を単独の合格根拠にしない。

### 人間判断の検証ケース（計画、未実行）

| ID | 入力・状況 | 期待結果 |
| --- | --- | --- |
| H01 | Reviewer提案とCodex成果物が並ぶ会話へ「承認します」 | 未解決依頼が一件でも対象未確定。質問して保持、Closeなし。 |
| H02 | 対象・効果を明示したD1へ引用／返信選択付きで「承認します」 | D1への返答を記録。Reviewer確認前は適用・Closeなし。 |
| H03 | Reviewer提案の採用を承認し、一致確認応答を受領 | 指定修正のみ許可。成果物受理・G出口・次工程へ拡大しない。 |
| H04 | Codex成果物commit Cを受理 | Cの人間受入を記録。G出口又はG6開始へ読み替えない。 |
| H05 | 同じ返答を再取得／再起動、又は別reportが未解決 | 確認報告の二重作成を防止。既存report中は送信待ち。 |
| H06 | pending IDと応答本文のIN_REPLY_TO不一致、又は判断版・commit変更 | 旧応答を新対象へ適用せず理由付き停止。 |
| H07 | 代理投稿・原文参照不能、拒否、保留、期限超過、配送失敗 | 出所と理由を保存。人間本人投稿／承認済み／Closeへ格上げしない。 |
| H08 | 対象G出口の人間判断と一致Reviewer確認・必要証拠が揃う | 当該G出口だけ完了。次工程やPR close/mergeは別許可がなければ実施しない。 |

G5出口の追加条件: G4 13節の四つの承認対象、曖昧返答の保持、確認報告によるReviewer起動、
一致応答前の適用／Close禁止がWC-07B・WC-09/10・VC-11へ対応すること。

## 6. G5出口と後続境界

G5の出口は、G0 P01〜P08、G1の再利用条件、G2 A01〜A06/NFR、G3 M01/M04/M05、G4 v2の各機能責務と異常経路が、少なくとも一枚のカード又は明示的な`INPUT_BLOCKED`へ対応し、全カードに入力、目的、対象、非目的、前提、許可上限、禁止、費用、受領証跡、検証、停止／判断、後始末、次状態があることである。`WC-00`は、各レビューが固定commit・対象path・hash・正本区分に結び付くこと、及び外部参照不能な人間指示を独立検証済みと主張しないことを保証する。特にA04については、WC-07が相関とガード、WC-07Aが継続中／結果／後続配送の観測、VC-11が実actor証跡を分担する。

本書はその自己点検を満たすため`ARTIFACT_QUALITY_CHECK: SELF_CHECK_PASS`とする。ただしG4 v2観測補遺を反映した現在は`REVISED_REVIEW_PENDING`であり、ChatGPTのレビュー受理までG5完了、G6開始、Day作業、製品受入を宣言しない。G5の受理後も、G6では広瀬剛が一枚を選ぶまで自動着手しない。
