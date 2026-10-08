# 8879 Day 12 terminal result — 2026-10-08

## Scope and identity

- Instance: `state/product-operator-normal-v1`
- Target: isolated `state/product-operator-normal-v1/local-llm-lab`
- Target Git HEAD: `e33b0a410fb8647711f02ae4e6e0b66472e6eff0`
- Day: `12`
- Product run: `run-67938903262d407b8767a38f537b0a7a`
- Separate Go allocation: `goa-36293398ac144f12af89c3aa3cb36d2d`
- Contract: `v2026-09-22-v2-evidence-contract`
- Contract fingerprint: `b163bc586e8d436c9dbd493db3b99dc6f553d417c472b33c07d4d2d5ba1059dd`
- Registration fingerprint: `a079ec7454c1181bb12662454ca84807a43a6f80e3838840735a0d30db510cc2`
- Authority profile: v16, fingerprint `98f23c3a07e30341a274f639ba6e5b02d48e2ea4cc8b2ae418e9c14a61e1273b`
- Limits: 1,800 active seconds / 3 attempts / 20,000 tokens / 500 JPY

## Actual result

The registered `D12_REPRODUCIBILITY_OPERATIONS` action ran once in managed
worktree `5b591069cc6545468850682149da6052`. It wrote only the authorized
`docs/day-12-report.md`. The saved state is `HUMAN_ACTION_REQUIRED`, 2/3
criteria, 67%, with blocker `REPAIR_SCOPE_AUTHORITY_REQUIRED`.

Two Evidence records are VALID:

- `operator_docs`: `590cb5f499e0c8c9db760f21cef76457`. The report covers setup,
  install prerequisites, backup, recovery, artifact handling, and logging.
- `recovery_check`: `26d68390c58e2e85ab33d2532c7299c6`. A Python zip byte
  roundtrip completed with exit code 0, one pass and zero failures.

These satisfy `d12-setup_and_prerequisites` and
`d12-backup_and_recovery`. The required `gitignore_check` Evidence was not
created, so `d12-artifact_operations` remains unsatisfied. The recorded action
attempt is COMPLETE as an action invocation but classified
`INSUFFICIENT_EVIDENCE` with failure
`ACTION_OUTPUT_FAILED_EVIDENCE_VALIDATION`. No research planner or model was
started.

## Source-control exclusion diagnosis

The registered check evaluates these four paths with
`git check-ignore --no-index`:

- `results/probe.json`
- `models/probe.gguf`
- `datasets/probe.json`
- `artifacts/probe.json`

Both the managed worktree and isolated base reported only the first two paths.
`results/` and `models/` are excluded by `.gitignore`, while the file excludes
only `datasets/generated/` under datasets and has no rule that excludes
`artifacts/`. Therefore `datasets/probe.json` and `artifacts/probe.json` are not
ignored.

This is a real mismatch between the repository state and the Day 12 artifact
handling requirement. It is not a Control Center Evidence adapter defect. The
generated report says to keep models, datasets, results, and artifacts outside
Git, but the current ignore rules do not enforce that complete set. Treating the
report text alone as proof would conceal the failed deterministic check.

The registered Day action authorizes only `docs/day-12-report.md` as an output.
Changing `.gitignore` would alter the evaluated repository and exceed this run's
saved output scope. No such edit or unchanged retry was performed.

## Resource and preservation evidence

- Saved Day active work: 1.641 seconds.
- One registered action attempt; LocalLLM/model invocations: 0.
- Model input/output tokens: 0/0 because no model or research planner started.
- Whole-run cost and prior-chain attempts/tokens/cost remain UNKNOWN.
- Generated report SHA-256:
  `11cbacc8b81afa978662456a1a454e13962e20605116b9d71ac2b7eb4db265b9`.
- Product RunRecord SHA-256:
  `87f90561bf70e2031e9f4ca9a84cc8fddbdb759b6f3458fd45b443e5de175bf2`.
- The managed worktree has only untracked `docs/day-12-report.md`.
- The isolated Lab base remains clean at the same HEAD and 11 commits ahead / 0
  behind `origin/main`.
- No `.gitignore` change, result substitution, retry, software install, model
  execution, credential change, commit, push, reset, cleanup, or original
  `C:\LocalLLM-Lab` change was performed.

## Artifact quality check and boundary

`ARTIFACT_QUALITY_CHECK: FAIL`

The operator procedure and recovery check are traceable, but the source-control
exclusion claim is contradicted by the deterministic repository check. Day 12
must remain non-COMPLETE at 2/3 and 67%.

The minimum disposition is to accept this preserved result as the terminal
negative Day 12 outcome and authorize Day 13 registered-contract preparation.
An alternative recovery must separately authorize the exact `.gitignore`
change, define whether broad `datasets/` and `artifacts/` exclusion is intended,
and use a new run under the changed condition. An unchanged retry cannot produce
the missing Evidence.

## Control Tower disposition

Control Tower replied exactly to
`CONTROL-TOWER-8879-DAY12-TERMINAL-DECISION-20261008-001` with
`RESULT: ACCEPT_TERMINAL_NEGATIVE` and `ARTIFACT_QUALITY_CHECK: FAIL`.
Disposition (A) is accepted. Run `run-67938903262d407b8767a38f537b0a7a`
is the terminal Day 12 negative result and remains non-COMPLETE at 2/3 and 67%.

The response requires preservation of the missing `gitignore_check`, actual
`.gitignore` state, report and RunRecord hashes, UNKNOWN usage, clean isolated
base, and the two VALID Evidence records. It does not authorize an ignore-rule
edit, new Day 12 run, retry, model, allocation, permission grant, commit, or push.
It authorizes Day 13 registered-contract inspection and non-effecting Smoke/Go
boundary preparation only. Every proposed Day 13 output path must be checked; an
output under non-ignored `datasets/`, `artifacts/`, or another unverified path
must stop before Go and report the exact path.
