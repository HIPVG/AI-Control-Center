# 8879 Day 9 Go authority application — 2026-10-08

## Scope mapping

- **Purpose:** 検証済みPlan Skeletonの後段で、benefits、risks、trade-offsを分離して説明するbounded stageを検証する。
- **Non-purpose:** Plan Skeleton、計画本体、正本状態を変更しない。Day 8の未達を修復せず、Day 10以降を開始しない。
- **Registered contract:** `v2026-09-22-v2-evidence-contract`
- **Registration fingerprint:** `d38625131b6d690ae6d88dba2916fe2dd83e0508ed9ef1f67616eb3cea843d41`
- **Completion criteria:**
  - `post_skeleton_stage`: validated Plan Skeletonの後だけに説明を実行し、benefits、risks、trade-offsを計画から分離する。
  - `immutable_plan`: 説明生成が検証済み計画を変更できない。
  - `bounded_contract`: 出力schemaとparse validationをboundedにしてtestする。
- **Required evidence:** `source_check`, `deterministic_tests`, `nonmutation_test`, `schema_contract`。
- **Registered action:** `D9_EXPLANATION_STAGE`; `ENGINEERING_WORKTREE`; `MANAGED_WORKTREE`; required operation `PROJECT_WRITE`; role `IMPLEMENTER`。
- **Allowed output scope:** `scripts/eval/explanation_stage.py`, `schemas/explanation-stage.json`, `tests/test_explanation_stage.py`。
- **Input boundary:** 登録runbookとarchitecture、および実行時に検証されるPlan Skeleton。LLMに計画本体の所有権を与えない。
- **Limits:** 1,800秒、3 attempts、20,000 tokens、500 JPY。利用量不明は`UNKNOWN`のまま保持する。
- **State and Git:** 実行主体は8879 product operator、OS利用者は現在のWindows利用者、対象は隔離Lab `state/product-operator-normal-v1/local-llm-lab`、生成先はmanaged worktree。元`C:\LocalLLM-Lab`、過去run、隔離base branch/index/worktree、credential、remoteは変更しない。
- **Stop boundary:** 画面案が上記3 path、操作、役割、上限から変わる場合、Plan Skeletonの変更を要求する場合、資格情報・外部送信・追加費用・破壊的Gitを要求する場合はGo前に停止する。保存結果が未達でも合格へ書き換えない。

## Non-effecting Smoke

Day 9を選択しSmokeを一回実施した。新runと対象処理は開始していない。受入済み基線は確認済み、completion configurationは`READY`。表示された阻害は`EXECUTION_ACTION_NOT_AUTHORIZED`, `CONSUMPTION_UNKNOWN_ATTEMPTS`, `EFFECTIVE_PERMISSION_UNKNOWN`で、未許可操作は`D9_EXPLANATION_STAGE: WRITE_SCOPE_NOT_ALLOWED`だった。

画面の権限案はproject default profile v12へ上記3 write pathだけを追加する`EXPANSION`で、操作class、担当role、各上限は不変だった。初回案はControl TowerのDay 8回答が準備だけを許可したため取消し、保存していない。

## Applied human authority

直接人間権限`AUTH-OPERATOR-8879-DAY3-14-CONTINUE-20261008-001`は、画面に示された対象・操作・上限・費用を確認した上で、Day 3からDay 14の通常権限確認、別枠承認、各Day一回のGoを許可している。今回の案は上記登録scopeと既存上限に完全一致するため、この権限をDay 9へ適用する。再表示した案が同一の場合だけ保存し、別枠を同じ上限で確認して一回のGoを開始する。

`ACTION_CLASS: AUTHORITY`
