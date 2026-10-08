# 8879 Day 10 Go authority application — 2026-10-08

## Scope mapping

- **Purpose:** 固定条件のlocal end-to-end実処理から、LLM call数、input/output token、時間、VRAM、CPU、RAM、失敗率を保存し、cold/warmと反復分布の未確認範囲を明記する。
- **Non-purpose:** 単回結果から安定性を断定しない。Day 9を修復せず、Day 11以降を開始しない。測定値や失敗を補完・推測しない。
- **Registered contract:** `v2026-09-22-v2-evidence-contract`
- **Registration fingerprint:** `9e82ddadf765a42207282d5c07d6c461d55fd713406bfe9ec946dc8d375cac83`
- **Completion criteria:**
  - `call_and_token_metrics`: call数、prompt/input token、output tokenを記録する。
  - `runtime_resources`: elapsed time、VRAM、CPU、RAMを記録する。
  - `failure_and_configuration`: failure rate、model/runtime構成、固定test条件を記録する。
  - `stability_limits`: cold/warmと反復分布の限界を、単回から確実性を主張せず記録する。
- **Required evidence:** `performance_artifact`, `condition_record`, `limitation_record`。
- **Registered action:** `D10_PERFORMANCE_RUN`; `RESEARCH_RUN`; `RESULTS_ONLY`; required operation `RESEARCH_EXECUTION`; role `IMPLEMENTER`。
- **Allowed output scope:** `results/day-runner/day-10/`のみ。
- **Registered inputs:** `config/run-profiles.json`, `config/model-matrix.json`, existing telemetry runner、および正本runbook/architecture。固定条件を実行中に変更しない。
- **Limits:** 1,800秒、3 attempts、20,000 tokens、500 JPY。欠測値は`UNKNOWN`のまま保持する。
- **State and Git:** 実行主体は8879 product operator、OS利用者は現在のWindows利用者、対象は隔離Lab `state/product-operator-normal-v1/local-llm-lab`、結果保存先は許可されたresults path。元`C:\LocalLLM-Lab`、過去run、隔離base branch/index/worktree、credential、remoteは変更しない。
- **Stop boundary:** 画面案が上記results path、操作、役割、上限から変わる場合、固定条件の変更、資格情報・外部送信・追加費用・source変更・破壊的Gitを要求する場合はGo前に停止する。単回、失敗、欠測を合格へ書き換えない。

## Non-effecting Smoke

Control TowerのDay 9終端負結果受理後、Day 10を選択しSmokeを一回実施した。新run、測定、推論、モデル処理は開始していない。受入済み基線は確認済み、completion configurationは`READY`で、Day 9 COMPLETE前提阻害はない。表示された阻害は`EXECUTION_ACTION_NOT_AUTHORIZED`, `CONSUMPTION_UNKNOWN_ATTEMPTS`, `EFFECTIVE_PERMISSION_UNKNOWN`。未許可操作は`D10_PERFORMANCE_RUN: WRITE_SCOPE_NOT_ALLOWED`だった。

画面の権限案はproject default profile v13へ`results/day-runner/day-10/`だけを追加する`EXPANSION`で、operation classes、assigned roles、各上限は不変だった。Control Tower回答が準備だけを許可したため、初回案は取消し、保存していない。

## Applied human authority

直接人間権限`AUTH-OPERATOR-8879-DAY3-14-CONTINUE-20261008-001`は、画面に示された対象・操作・上限・費用を確認した上で、Day 3からDay 14の通常権限確認、別枠承認、各Day一回のGoを許可している。今回の案は登録scopeと既存上限に完全一致するため、この権限をDay 10へ適用する。再表示した案が同一の場合だけ保存し、別枠を同じ上限で確認して一回のGoを開始する。

`ACTION_CLASS: AUTHORITY`
