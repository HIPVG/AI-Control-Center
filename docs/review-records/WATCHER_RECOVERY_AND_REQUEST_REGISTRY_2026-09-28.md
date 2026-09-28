# Watcher復旧・仕掛一覧の実施記録

対象: レビュー輸送の復旧と連続依頼の管理。G5 Close、G6、Day実行は対象外。

## 原因と実運用証跡

ポーリングは継続していたが、補助報告AAF1EDDが004の待機対象を置換していた。
004宛て返信5863431829（HUMAN_REQUIRED）を別件として除外していた。
サービス停止中に `py -3.12 -m scripts.recover_reviewer_binding` でPRの対象を
照合し、旧ID・エラー・根拠・受領確認限定の継続範囲を永続履歴へ保存した。
手編集によるstate消去はしていない。

2026-09-28 05:22:11 UTCの実Watcher結果:

- last_applied_response_comment_id: 5863431829
- last_codex_exit_code: 0
- last_continuation_action: HUMAN_REQUIRED
- pending_response_comment_id / outstanding_report_id: null
- last_error: null

これは一致返信の受領・人間判断待ちの処理を証明する。文書受理やG5 Closeは証明しない。

## 連続依頼の契約と検証

人間の追加指示により、REPORT_IDごとの永続report_registryを導入した。
未完了一覧を依頼に添え、個別返信のIN_REPLY_TOで対応付ける。完了・確認済みは
送信一覧から除き、ローカル履歴に残す。返信不要は任意ACKNOWLEDGED確認で閉じ、
Codex継続を起動しない。人間判断待ちは未完了として残る。

tests/test_reviewer_bus.py の15件で、相関不一致抑止、完全一致の一回適用、
復旧状態のファイル保存・再読込、0001/0002返信不要/0003の連続登録、
0003→0001の順不同・遅着返信、確認専用返信の無実行、複数宛先返信の拒否を確認した。
G4/G5の輸送契約と運用規則を対応付け、30件のmanifest hashを照合して不一致0。

Reviewer指示ファイルの追記案はstate/reviewer-task-prompt-update.mdに準備済み。
既存の外部本文と同一で、追記だけであることを読取確認したが、外部ファイル更新は
自動承認審査に拒否された。ユーザーによるこの宛先・内容への明示承認が必要とされた。
外部指示更新と新方式のReviewer実応答は未完了。fixture結果を実配送成功としない。
