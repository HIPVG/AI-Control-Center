# G7 — AI-Control-Center 検証計画

- 状態: `ACCEPTED`; verification result review pending
- 作成日: 2026-09-29
- 実装基線: `a30ed2303a85ff00ebbb5b0721bea4fe5c66ad0f`
- G6受理記録: `docs/review-records/G6_STAGE_COMPLETION_ACCEPTANCE_2026-09-29.md`
- 開始権限: `AUTH-G7-START-20260929-001`
- 運用正本: `docs/WORKING_RULES.md` commit
  `60c0fe7dcf8935fad4c6d3818256a94e95965501`
- 標準: `C:/AI-Operation-Standards/01-ai_work_operating_standard_integrated_v1_0_2026-09.md`
  commit `13065155999b799fdd2766630696d523fc53beaf`
- 参考テンプレート: T36/T37の必要欄を本書と結果記録へ統合し、別帳票は増やさない。

## 1. 目的と判定境界

G7の目的は、G6で実装された機能がG2のA01〜A06とG4/G5の契約を満たすか、
かつG6の試験が見せかけの合格になっていないかを、実装時とは分けた検証として
確認することである。終了コード、件数、既存パックの受理だけを合格根拠にしない。

本計画は次を区別する。

- `fixture`: 決定的なモデル、状態、API、DOMの機械検査。
- `actual actor`: 実際のReviewer/Watcher経路の固定証拠。
- `product E2E`: 実サービス、実ブラウザー、選択Day、実測telemetryを含む製品経路。

G7は未評価を隠さない。必要条件がない項目は`NOT_EVALUABLE`又は
`INPUT_BLOCKED`とし、fixture成功をproduct E2E成功へ拡張しない。G8、Day開始、
製品受入は本計画の結果から自動で開始しない。

## 2. 役割、独立性、上限

| 役割 | 担当 | G7での権限・制約 |
|---|---|---|
| 検証実行・証拠作成 | CODEX | 固定計画の読取検査と試験実行。G7中に製品コード又は受入期待値を修正しない。 |
| レビュー／検証 | ChatGPT | 計画と結果を固定commitから照合する。レビューと検証の兼務であり、両者間の独立性は主張しない。実装担当CODEXとは別主体。 |
| 機械検査 | 固定済みpytest/Node試験、Git差分・hash照合 | 計画受理後は、失敗を通すために検査又は期待値を変更しない。 |
| 決定・受入責任者 | 広瀬剛 | 新権限、製品方針、G7出口、G8／製品受入を判断する。 |

共通上限は、各カードの対象コマンドを最大2回、30分のACTIVE_WORK、費用0円とする。
Reviewer待ちはACTIVE_WORKから除く。tokenは実測可能なときだけ出所付きで記録し、
不明を0にしない。失敗時は原因を分類するが、G7内で実装又は試験を修正しない。
修正が必要ならG6又はG4へ差し戻し、新しい固定commitと再検証計画を作る。

## 3. 検証カード

### GV-00 — 基線・試験完全性の固定

- 対象: G6受理行列、実装基線、現在HEAD、変更ファイル、対象試験、除外、期待失敗、
  mock/stub、試験変更履歴。
- 実施: G6の各受理commitが基線へ到達することを確認し、基線との差分と試験の
  来歴を読み戻す。G6でREJECTされた旧パックを成功に数えない。
- 合格: A01〜A06の各主張が少なくとも一つの検証カード又は明示した未評価へ対応し、
  実装担当がG7開始後に受入期待値を変更していない。
- 証拠: commit/path/hash、差分一覧、除外・mock/stub一覧、対応表。
- 停止: 基線、試験来歴又は要求対応が一意でなければ後続試験を実行しない。

次の完全性項目を、GV-01の実行前に個別判定する。`PASS`にできない場合は
`NOT_APPLICABLE`へ丸めず、下表の条件どおり`NOT_EVALUABLE`又は`FAIL`にする。

| 完全性項目 | 確認方法と保存証拠 | `NOT_APPLICABLE`／`NOT_EVALUABLE`／`FAIL`の条件 |
|---|---|---|
| 固定入力と本番生成経路 | 各fixtureについて、入力を作る関数、製品entrypoint、validator／state遷移までの呼出経路をコード参照で対応付ける。製品entrypointと同じ関数列を通るものだけ、その境界の経路証拠とする。 | 固定入力が製品adapterを迂回する場合、そのfixtureは下位contractだけの証拠であり製品経路は`NOT_EVALUABLE`。同じ経路と主張しながら相違があれば`FAIL`。対象に本番生成経路が存在しない純粋モデル単体試験だけ`NOT_APPLICABLE`。 |
| 判定器への答えの漏洩・特定事例固定化 | fixture、期待値、validator、production入力、prompt／context（存在する場合）の差分を読み、期待する最終判定又はcase固有の正答がproduction入力へ埋め込まれていないことを確認する。異なる有効値と拒否値を使うassertion、型・ID・状態条件による判定を証拠化する。 | AI／promptを使わない決定的検査のprompt漏洩だけは`NOT_APPLICABLE`だが、期待値固定化の確認は省略しない。生成入力又は判定対象に正答が漏れている、あるいは一般条件でなく一事例だけを認識するなら`FAIL`。production入力を確認できなければ`NOT_EVALUABLE`。 |
| 出力・token・実行時間の保持 | 各固定コマンドについて、完全なcommand、開始・終了時刻、wall duration、exit code、stdout/stderr、warning、失敗caseを結果記録へ保存する。tokenは計測主体・出所・値を分離する。 | モデルを呼ばないGV-01ではtokenだけ`NOT_APPLICABLE (no model invocation)`と記録し、0とは記録しない。出力又は時間を採取できなければ当該結果は`NOT_EVALUABLE`。失敗を省略又は成功へ書換えた場合は`FAIL`。 |
| 切断・失敗の保持 | review continuation、delivery failure、期限切れ、無効envelope等の固定caseについて、原因、途中状態、終端状態、時刻、後続効果不在をassertionと保存出力から照合する。新しい実配送や切断は起こさない。 | 固定caseがない境界は`NOT_EVALUABLE`。既存の模擬切断はfixture証拠としてのみ表示する。失敗後に成功状態へ丸める、又は失敗出力・理由が失われる場合は`FAIL`。実外部切断の再現は現在のGV-00/GV-01では`NOT_APPLICABLE`ではなく`NOT_EVALUABLE`。 |

GV-00結果には各行の判定、対象path／test名、根拠、証拠所在を残す。これらの確認を
完了できないこと自体は試験実行の成功へ変換せず、影響するGV-01又はGV-02を停止する。

### GV-01 — 決定的な焦点・関連回帰・失敗注入

- 対象要求: A01〜A06。ただしproduct E2Eを除くcontract/fixture境界。
- 固定Python集合:
  `test_run_contract.py`, `test_day_admission.py`, `test_day_catalog.py`,
  `test_day_go.py`, `test_evidence_completion.py`, `test_repair_recovery.py`,
  `test_review_control.py`, `test_review_continuation.py`,
  `test_human_decision.py`, `test_run_telemetry.py`, `test_run_read_model.py`,
  `test_api.py`, `test_reviewer_bus.py`。
- 固定UI集合: `node tests/run_status_ui.test.js`。
- 重点失敗: 不一致run/Day、範囲・時間・試行上限超過、無効Evidence、二回修正後、
  不一致・重複・期限切れreview、確認ID欠落、unknown telemetry、current/history混同。
- 合格: 全対象caseが期待状態と副作用不在までassertされ、warning・除外・未実行が
  結果記録に残る。件数だけでは合格にしない。
- 停止: 失敗又はharness不成立はそのまま記録し、試験／実装を修正せず差戻す。

### GV-02 — 外部境界、実UI、actual actor

- A04 actual actor: VC-11の固定traceをhash、report/reply/decision ID、commit、時系列、
  `APPLIED`と後続効果で独立に読み戻す。過去条件の証拠として扱い、現在稼働の証明に
  置換しない。新規配送、Watcher再起動、実Codex継続は行わない。
- A01/A05実UI: 実サービスと実ブラウザーで、未選択、選択のみ、Go→PREFLIGHT、
  current/history、停止・判断待ち、unknown/source表示を保存stateと同一run IDで
  読み戻す必要がある。
- A06実測: 実runの介入、relay、試行、token、費用を同一run IDで照合する必要がある。
- 現在状態: A04の過去actual actor読戻しは実施可能。実UIと実runは、サービス／
  ブラウザー操作、対象Day・環境、Goの許可、上限、live認証が固定されるまで
  `INPUT_BLOCKED`。fixtureで代用しない。
- 停止: 新しい外部効果、認証、Day開始又は費用が必要になった時点で人間判断へ渡す。

### GV-03 — 証拠対応・G7出口判定

- A01〜A06ごとに`PASS / FAIL / NOT_EVALUABLE / INPUT_BLOCKED`、証拠、条件、
  残課題、G8への影響を記録する。
- `PASS`は対応するfixture又はactual actor境界に限定する。Must要求のproduct E2Eが
  未評価なら、G7全体を無条件合格にしない。
- 出口候補は`PASS / CONDITIONAL_PASS / RETURN`。ChatGPTの結果レビューと
  `ARTIFACT_QUALITY_CHECK: PASS`後に、広瀬剛がG7出口を判断する。
- G7 CloseはG8開始、Day/Go、製品受入、サービス稼働許可を含まない。

## 4. 要求―検証対応

| 要求 | GV-00 | GV-01 | GV-02 | 現時点のproduct境界 |
|---|---|---|---|---|
| A01 選択DayのGoと状態 | 基線・契約 | 選択無副作用、Go→PREFLIGHT fixture | 実UI・同一run読戻し | `INPUT_BLOCKED` |
| A02 計画・証拠・判定 | Evidence来歴 | 型、validator、不足・不一致拒否 | 実Day Evidence | `INPUT_BLOCKED` |
| A03 修正・再検証 | guard来歴 | scope/budget/二回停止/復帰 | 実修正成功 | `NOT_EVALUABLE` |
| A04 レビュー・停止・復旧 | 相関来歴 | 重複・不一致・期限・継続fixture | VC-11固定actual actor読戻し | 過去一経路のみ評価可能 |
| A05 実状態dashboard | API/DOM来歴 | state projection fixture | 実UIと保存state照合 | `INPUT_BLOCKED` |
| A06 成果・中継・費用 | telemetry来歴 | unknown/source/上限/実測分離 | 実run実測 | `INPUT_BLOCKED` |

## 5. 禁止、停止、復旧

- G7中に製品コード、受入期待値、既存証拠を修正しない。
- dirty workをreset、clean、restore、移動、包括stageしない。
- service/Watcher再起動、新規review配送、Day選択・Go、モデル、認証変更、費用、
  破壊操作を本計画の自己承認で開始しない。
- 同一試験の2回失敗、基線不一致、試験完全性の欠落、必要権限不足では停止する。
- 実装不具合はG6、要求・制御設計の不備はG4、権限・製品判断は広瀬剛へ戻す。
- 再開は差戻し先の新しい固定commit、更新した期待条件、又は必要な人間権限を得てから。

## 6. 成果物とレビュー要求

成果物は本計画、カード別の実行記録、A01〜A06証拠対応表、G7結果パックである。
計画レビューでは、検証範囲、固定試験、実境界の未評価分類、独立性表示、停止・差戻しが
G0〜G6と標準G7に整合するかを判断する。計画が受理されるまでGV-01以降の試験は
実行しない。

`ARTIFACT_QUALITY_CHECK: SELF_CHECK_PASS`。これは計画内容の自己点検であり、
G7検証結果又は工程受入ではない。

## 7. 計画レビュー履歴

- `G7-VERIFICATION-PLAN-20260929-001` / reviewed commit
  `142c97c1c5cb6012dd6aa79c0aaa98ede5fdc142`: `REJECT`。GV-00に、本番生成経路、
  答えの漏洩、出力・token・実行時間・切断・失敗の保持について、確認方法と
  適用不能／未評価条件が不足していた。
- 本改訂はその完全性判定だけを追加する。実装、固定試験集合、実E2E範囲、権限、
  上限は変更しない。計画再受理まで試験を開始しない。
- `G7-VERIFICATION-PLAN-20260929-002` / reviewed commit
  `3b267223d507aefe113df671a9331be5c1fc0a13`: `ACCEPT`。GV-00の完全性判定、
  fixture／actual actor／product E2Eの境界、固定試験、停止・差戻しを計画として
  受理した。これは検証結果の合格ではない。
- GV-00/GV-01は `G7-GV00-GV01-COMPLETION-20260929-001`、GV-02は
  `G7-GV02-COMPLETION-20260929-001` で各限定範囲を受理済み。GV-03結果は
  `docs/review-records/G7_STAGE_VERIFICATION_RESULT_2026-09-29.md` に記録する。

