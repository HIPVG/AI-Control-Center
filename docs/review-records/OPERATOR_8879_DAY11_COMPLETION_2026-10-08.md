# 8879 Day 11 completion record — 2026-10-08

## Scope and identity

- Instance: `state/product-operator-normal-v1`
- Target: isolated `state/product-operator-normal-v1/local-llm-lab`
- Target Git HEAD: `e33b0a410fb8647711f02ae4e6e0b66472e6eff0`
- Day: `11`
- Initial stopped run: `run-f6432c0df31b4f1c84fb720ed5257dc2`
- Initial Go allocation: `goa-7604d3c1d7344131babcb60a8c365180`
- Completed run: `run-422634dd539044d2900b37ae9190fd04`
- Completed-run Go allocation: `goa-0fa4b8493d504b6799a8c2bb3b949345`
- Contract: `v2026-09-22-v2-evidence-contract`
- Contract fingerprint: `0e7059d86a72fe4a1cd2f252f51ab2a44dcc63332badf55e9323b5c92d649008`
- Registration fingerprint: `56e437f3bc632a072625be9784c10b302150215021814f87da0d2aed907782c4`
- Authority profile: v15, fingerprint `07a152c4046047c68ac6b1b9357946d1e4ffce0b267ef10c92e47217bfe35713`
- Limits per allocation: 1,800 active seconds / 3 attempts / 20,000 tokens / 500 JPY

## Preserved first result

The first run stopped as `HUMAN_ACTION_REQUIRED` with
`PREREQUISITE_DAY_REQUIRED`. Its exact reason was that no compatible validated
`hardware_evidence` record had yet been produced. It executed no registered Day
action. This run and its allocation remain in history and were not relabelled or
deleted.

The isolated Lab already contained a fixed Day 4 cross-model result at
`results/day4-cross-model/EXP-20260923T151059-424c537a66`: four fixed cases for
each of `phi4:14b` and `qwen3-14b-q4:latest`, temperature 0, seed 42, context
8192, output limit 1024, reasoning disabled, and eight successful saved
responses. The manifest SHA-256 is
`6e4937f95329821b42bebd99e8b9c3b2bc906cd4ca0d4a823615986bb634c29f`;
the telemetry SHA-256 is
`28d847e7f5ef8df588a49600cddb55a3730cc1ad344f9439901390b727009999`.
It records an RTX 3060 with 12,288 MiB total VRAM and observed GPU peaks from
11,281 to 11,564 MiB. It does not contain a 24 GB/30B comparison, repeatability
distribution, measured process RAM, human quality score, or business-value
measurement.

## Bounded product corrections

The actual Go exposed two product-side composition gaps. Corrections were
limited to those entry points:

1. The retained-evidence resolver and Day adapter now validate the exact saved
   Day 4 manifest/telemetry condition and expose it as Day 11
   `hardware_evidence`, retaining every limitation above.
2. Terminal telemetry now accepts exactly one registered
   `DECISION_OR_DOCUMENTATION_WORKTREE` action when the saved run, authority,
   contract, strategy, criterion, evidence identities, hashes, and absence of a
   planner/model effect all agree. Wrong template identity remains rejected.

The second correction was required because the completed Day snapshot had
correctly saved the document action while the RunRecord remained `PREFLIGHT`.
The existing same-run settlement path was applied after the correction. It did
not repeat the action, create a new run, or modify the Day result.

Focused validation:

- retained-evidence and result-adapter tests: 22 passed;
- deterministic decision settlement positive, wrong-identity negative, and
  existing Day 1 taskless settlement: 3 passed;
- Python compilation: passed;
- `git diff --check`: passed with line-ending warnings only.

One optional broader related suite was stopped after prolonged no-output
execution and is not counted as a pass. No full-repository test claim is made.

## Completed result and evidence

The completed run created one advisory document in managed worktree
`b6c1921c8c664ed2bbbea288389dfcae`:

- `docs/day-11-report.md`
- SHA-256: `a1cdb6db48ddff197c81313ff6be3c6eae6a6669822041f2047846edb9754ed0`

The document recommends the 12–16 GB tier only where the measured workload fits
capacity and quality requirements. It requires measured memory or quality
deficit for an upper tier, and comparative benefit plus business justification
for optional 30B/24 GB. It explicitly leaves unmeasured quality,
repeatability, hardware benefit, product readiness, and commercial judgment
open.

All three current contract criteria are satisfied with strict same-run records:

- `d11-deployment_matrix`: `deployment_matrix=fa33cae19627e1e5cccd1fb0d8a412c1`
- `d11-expansion_evidence`: `hardware_evidence=2b7efc8ff4dd643d405dbd83431721a4`
- `d11-workload_limits`: `advisory_record=915a3cbcead492db13c55cea225dd356`

The Day snapshot and RunRecord are both `COMPLETE`, completion readiness is
`READY`, remaining gaps are empty, and the UI shows the same run and all three
criteria as `STRICT` and satisfied.

The saved action attempt is retained exactly. Its outcome is `COMPLETE`, while
its historical `observed_classification` is `INSUFFICIENT_EVIDENCE` and
`failure_reason` is `ACTION_OUTPUT_FAILED_EVIDENCE_VALIDATION` from the first
internal result binding before final same-run revalidation. These fields were
not rewritten to improve appearance.

## Resource and preservation evidence

- Run active work: 1.531 seconds.
- Registered deterministic action attempts: 1 of 3.
- LocalLLM/model invocations: 0.
- Input/output model tokens: 0/0, supported by the registered deterministic
  decision action and `research_planner_started=false`.
- Cost: `UNKNOWN`; no measured cost record exists.
- Manual relay count: `UNKNOWN`; the action does not observe relay
  interventions.
- Completed RunRecord SHA-256:
  `1dbbae9639012601d47f043b962948fe67be824c6285aeeeb4532b1c544ee054`.
- Run telemetry SHA-256:
  `1d3b0cb75d46027727811e49076389d595cdaf24a388674739c8d864472c7d8b`.
- The isolated Lab base remains clean at the same HEAD and 11 commits ahead / 0
  behind `origin/main`.
- The managed worktree contains only the untracked registered advisory output.
- No inference rerun, 24 GB/30B inference, source change in the isolated Lab,
  original `C:\LocalLLM-Lab` change, reset, clean, stage, commit, or push
  occurred.

## Artifact quality check and boundary

`ARTIFACT_QUALITY_CHECK: PASS`

PASS is limited to current-contract traceability, strict same-run evidence,
measured 14B/12 GB observations, explicit advisory limitations, and agreement
of saved state with the UI. It does not establish general model quality,
repeatability, a 24 GB/30B benefit, product readiness, or a commercial decision.

Day 12 must not start until Control Tower returns an exact-correlated completion
decision for `CONTROL-TOWER-8879-DAY11-COMPLETION-20261008-001`.

## Control Tower disposition

Control Tower returned exact-correlated `RESULT: ACCEPT_COMPLETE` and
`ARTIFACT_QUALITY_CHECK: PASS`. Day 11 is accepted only for the current
evidence-bounded advisory contract. All measurement limits, UNKNOWN values,
historical failure fields, the untracked Day 11 output, and the original Lab's
pre-existing dirty paths remain unchanged.

Read-only inspection by Control Tower found three Day 9-named untracked files in
the original Lab whose timestamps precede the Day 11 runs. This does not
contradict the Day 11-specific nonmutation result, but provenance was not
established. The files must not be reset, cleaned, staged, committed, or
attributed by this operation. The acceptance does not retroactively validate an
earlier Day 9 original-worktree nonmutation claim.

The response authorizes recording this acceptance and preparing only the Day 12
registered-contract inspection plus ordinary non-effecting Smoke/Go boundary.
It does not itself authorize a Day 12 run, implementation, recovery, model call,
allocation, permission grant, original-Lab modification, commit, or push.
