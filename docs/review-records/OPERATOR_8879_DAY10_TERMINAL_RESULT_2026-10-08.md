# 8879 Day 10 terminal result — 2026-10-08

## Scope and identity

- Instance: `state/product-operator-normal-v1`
- Target: isolated `state/product-operator-normal-v1/local-llm-lab`
- Target Git HEAD: `e33b0a410fb8647711f02ae4e6e0b66472e6eff0`
- Day: `10`
- Product run: `run-7058d2d3dfa84565973a7e5e045b8e20`
- Separate Go allocation: `goa-b0b83f5dfb374fbfb9fa53b0d3fdba86`
- Contract: `v2026-09-22-v2-evidence-contract`
- Contract fingerprint: `c0c986db2d217232ea3d7874ef283e16296907eb0f62fe5721029f1e3318f83c`
- Registration fingerprint: `9e82ddadf765a42207282d5c07d6c461d55fd713406bfe9ec946dc8d375cac83`
- Authority profile: v14, fingerprint `9a4ce2c079d0f6679c51fe97f82b24f11a065ccd47d5038bed4aa8eb18d7b5b7`
- Limits: 1,800 active seconds / 3 attempts / 20,000 tokens / 500 JPY

## Actual result

The registered `D10_PERFORMANCE_RUN` was started once. Its research planner
effect was reserved, then the action failed as
`CODEX_RESEARCH_EXECUTION_PLANNER_CODEX_NOT_FOUND`. The saved state is
`EXTERNAL_ACTION_REQUIRED`, 0/4 criteria, 0%, with an empty Evidence store.
There is one failed action attempt, bound to `d10-failure_and_configuration` and
`condition_record`.

No research execution plan or Day 10 result directory was created. Consequently:

- LLM call count and input/output tokens were not measured.
- Elapsed time, VRAM, CPU, and RAM were not measured.
- Failure rate, model runtime configuration, and the executed fixed condition
  were not recorded because no fixed-condition workload ran.
- Cold/warm behavior and repeated-run distributions were not observed.

All four contract criteria remain unsatisfied. The planner's input/output token
usage is unavailable with reason `RESEARCH_PLANNER_USAGE_MISSING_OR_INVALID`.
Missing measurements remain UNKNOWN and are not converted to zero.

## Deterministic condition diagnosis

The isolated Lab does contain a legacy `performance` run profile in
`config/run-profiles.json`: four cases, `qwen3-8b-q4`, temperature 0, three
repeats, seed 42, context 4096, output limit 512, timeout 120 seconds, reasoning
disabled, and telemetry enabled at 0.2-second intervals. This is configuration
evidence only; it is not evidence that Day 10 processing occurred.

The current Day research guard requires a registered JSON configuration with
`research_kind: performance`, an exact `entrypoint`, retry disabled, an enabled
runtime model, frozen input references, and the contract's authoritative source
references. Running the saved Day 10 contract through the deterministic
`research_inventory` returned `candidate_count: 0`. Neither the isolated Lab nor
the protected original Lab has a `results/day-runner/day-10/` artifact. A focused
search found no compatible saved performance run identified by the performance
profile.

Therefore an unchanged retry cannot produce an approved research condition. A
new performance research configuration and entrypoint would change the
evaluated condition and exceed the saved Day 10 output-only scope.

## Resource and preservation evidence

- Saved Day active work: 0.766 seconds.
- Planner tokens, whole-run tokens, and cost remain UNKNOWN.
- Prior chain attempts, tokens, and cost also remain UNKNOWN under the saved
  carryover record.
- Product run record SHA-256:
  `6862a5aa3e11149185d20a505430134bd5d4e38d63d4e47df1e92364d424e990`.
- The isolated Lab base remains clean at the same HEAD and 11 commits ahead / 0
  behind `origin/main`.
- No research execution, inference result, result substitution, source edit,
  condition invention, retry, credential change, commit, push, reset, cleanup,
  or original `C:\LocalLLM-Lab` change was performed.

## Artifact quality check and boundary

`ARTIFACT_QUALITY_CHECK: FAIL`

The failed planner attempt, absent research plan, empty Evidence store, and
candidate inventory are traceable. The Day objective is unfulfilled because no
fixed-condition processing or performance measurement occurred. Day 10 must
remain non-COMPLETE.

The minimum disposition is to accept this preserved 0/4 result as the terminal
negative Day 10 outcome and authorize Day 11 registered-contract preparation.
An alternative recovery must define one exact bounded, materially changed
performance research condition and its separate authority. An unchanged retry
is not justified by the saved evidence.

## Control Tower disposition

Control Tower replied exactly to
`CONTROL-TOWER-8879-DAY10-TERMINAL-DECISION-20261008-001` with
`RESULT: ACCEPT_TERMINAL_NEGATIVE` and `ARTIFACT_QUALITY_CHECK: FAIL`.
Disposition (A) is accepted: the saved run is the terminal Day 10 negative result,
the Day 10 execution boundary is closed, and the Day remains non-COMPLETE at 0/4
and 0%.

The response requires retaining all four unsatisfied criteria, the empty Evidence
store, the failed planner attempt, the absent result directory, every UNKNOWN
measurement, and the clean Git state. It authorizes only Day 11 registered-contract
inspection and non-effecting Smoke/Go boundary preparation. It does not authorize a
Day 11 run, model or research execution, allocation, permission grant, new
performance condition, credentials, source edit, commit, or push. If Day 11 requires
Day 10 COMPLETE, admission must stop fail-closed and report that prerequisite.
