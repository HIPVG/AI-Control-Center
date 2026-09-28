# G5成果物作成プロンプト v2

> 前提: `docs/G4_AI_CONTROL_CENTER_FUNCTIONAL_CONTROL_DESIGN_v2_2026-09.md` が人間承認済みの機能設計正本である。出力はG5の実装計画だけであり、G6実装、テスト実行、サービス操作、Day選択／Go、モデル実行、外部配送、費用発生、Git変更を許可しない。

AI-Control-CenterのG5（実装計画・作業カード・検証計画）を作成又は更新してください。G4 v2に定義された機能、役割、状態、制御、例外、復旧、M01/M04/M05を変更せず、独立して実施・検証・停止できる最小カードへ分解してください。新しい機能設計をG5で補わないでください。

作成前に、最新の人間／レビューメッセージ、`docs/WORKING_RULES.md`、`docs/CURRENT_WORK.md`、指定runbook、G0〜G4 v2、persisted state、Git状態を読み、利用した文書の版又はSHA-256を記録してください。規範本文を優先し、標準の非規範テンプレートは既存成果物へ必要十分な情報だけを統合してください。

G5文書には、少なくとも次を含めてください。

1. 人間許可の境界。G5は計画だけであり、G6カード選択と製品利用者のDay Goは別権限であること。
2. G0 P01〜P08、G1の条件付き再利用・未接続、G2 A01〜A06/NFR、G3 M01/M04/M05、G4 v2の機能責務／例外を、カード又は明示的`INPUT_BLOCKED`へ対応付ける表。
3. 主経路を先行する順序。少なくとも、RunIntent/RunControl、DayAdmission/PREFLIGHT、Day 1〜14 catalog、選択／Go UI、typed Evidence、許可内修正／同一Day再検査、Review Control、Review continuationの受信中／適用中／結果／後続配送の観測、telemetry、read-only API、dashboard、実actorレビュー検証、選択Day受入ゲートを、責務別のカードとして扱うこと。
4. 各カードに、`work ID`、担当、入力版／hash、目的、対象パス／API／データ、非目的、前提、許可操作と最大回数、禁止操作、費用上限、期待結果／受領証跡、検証、停止／判断要求、後始末、次状態を記載すること。
5. fixture、実actor検証、選択Dayの製品E2Eを混同しないテスト計画。Review continuationについては`RECEIVED_PENDING_APPLY`、`APPLYING`、`APPLIED`、`VERIFIED`、`CONTINUATION_FAILED`、`DELIVERY_FAILED`、継続envelope、後続report/commentの証跡を区別すること。終了コード、保存状態、AI自己報告を単独の合格証拠にしないこと。
6. M01が実actorの一意送達・一意継続で失敗した場合だけM05停止→G3再評価→M04検討へ戻ること。M04を先回りして実装しないこと。
7. G5の出口と、レビュー受理前はG6／Day／製品受入へ進まない境界。

各カードは一責任境界にしてください。プラットフォーム、UI、エージェントを一枚で同時導入しないでください。通常の既存レビューバスを人間のコピペへ戻さず、新認証、新配送先、費用、範囲外権限だけを人間判断にしてください。Day未選択又は製品Go未承認なら、対象Dayを推測せず、選択Day E2Eを`INPUT_BLOCKED`として保持してください。既存のdirty作業をreset、clean、移動又は取込みしないでください。
