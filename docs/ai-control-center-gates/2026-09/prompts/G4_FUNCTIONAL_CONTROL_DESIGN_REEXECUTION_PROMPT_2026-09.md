# G4再実施プロンプト — 機能・制御設計

AI-Control-CenterのG4を再実施してください。G4の目的は、G0の製品目的とG2要求を満たす機能経路を実装前に固定することです。G5の作業順やファイル編集を決めること、G6の実装、Day実行、外部送達を行うことではありません。

必ずG0のP01〜P08、G1の再利用条件・未証明事項、G2のA01〜A06/NFR、G3の役割・M01/M04/M05、旧G4のfixture根拠と未実証範囲、現行`WORKING_RULES.md`と`CURRENT_WORK.md`を読みます。旧G4を削除せず、変更理由と影響を明記した新しい改訂設計として保存します。

以下を設計文書に含めてください。

1. Day 1〜14のadmission、利用者のDay選択、Go、Run Intent、PREFLIGHT、同一run IDの意味。
2. 計画、Evidence Record/validator、criterion完了、許可内修正、再検証、人間判断、matching reviewer確認、同一Day PREFLIGHT復帰の経路。
3. Review ControlをDay stateとは別にし、`SENT/RECEIVED/APPLIED/VERIFIED`、一件のoutstanding、重複・期限・再起動の扱いを定義すること。
4. run単位の手動中継回数、介入理由、試行・上限、token・費用と出所、current/historicalの表示責務。
5. 権限拒否、dirty Git、時間・費用・試行上限、空出力、exit 0、古い規則、重複イベント、同一失敗二回、Watcher不在を含む停止・復旧設計。
6. M01を主経路、M04を実actor不成立時だけのG3再評価候補、M05を安全停止とする発動規則。
7. 要求ごとの設計経路、既存fixture根拠、未実証事項、G5以後の検証対象。

UI、AI提案、Watcher、過去保存状態に実行・完了・権限決定を委ねないでください。通常レビューを人間のコピペ経路へ戻さず、新認証・新配送先・費用・範囲外権限だけを人間判断にします。実証済みと未実証を混同せず、G4では新テストを実行しません。G5には、受理済みG4設計を実装単位へ分解することだけを引き渡してください。
