# Day 2 DRAP v0.4 execution and independent validation

## Fixed condition

- Run ID: `DRAP-20260923T142237-220f9467`
- Results root: `C:\LocalLLM-Lab\results\decision-reasoning-v0.4\DRAP-20260923T142237-220f9467`
- Model: `phi4:14b` for semantic abstraction and cross-functional reasoning.
- Configuration: v0.4; temperature 0; seed 42; context 4096; 240-second
  per-call timeout; 1024-token abstraction/reasoner caps; serial execution;
  retry disabled; thinking disabled.
- Day 1 comparison baseline: frozen ref
  `refs/heads/ai-control-center/day1-baseline-374457d3d5795395`, commit
  `374457d3d579539549df0936e3c96a47c9a1a319`, tree
  `8387ec4e7399cfd1a33c2eaebb2f352259e36727`.

## Actual execution evidence

- Manifest status: `COMPLETED`; `dry_run=false`.
- Manifest planned / reported actual calls: 9 / 9.
- Metrics rows: 9 stages, of which 8 produced LocalLLM metrics and one
  (`DR-004` reasoner) was `SKIPPED_NOT_NEEDED`. The manifest's
  `actual_llm_calls=9` includes that skipped stage, so physical model-call count
  is not asserted from that field alone.
- No generated response reached the 1024-token cap; each generated metric has
  `done_reason=stop`.
- The run retained per-stage output tokens, prompt tokens, elapsed time, prompt
  and evaluation rates, peak VRAM, CPU, RAM, GPU utilization, validation, and
  manifest provenance. Raw responses and thinking are not persisted.
- Gate: `FEASIBLE_RELEVANT_ACTION_GATE-v1`, enforced. Across five cases every
  permitted action was both feasible and relevant to an active verified issue.

## Independent Codex validation

`C:\Users\広瀬剛\AppData\Local\Programs\Python\Python312\python.exe -m unittest tests.test_decision_reasoning_v4 -v`

Result: 5 passed, 0 failed. This verifies the pinned baseline, feasible and
relevant filtering, normal-control reasoner suppression, payload exclusion of
disallowed actions, and dry-run action-gate evidence.

## Preserved model-quality findings

The run has `prototype_status=NEEDS_REVISION`, not a harness failure:

- DR-001: `PLAN_VALIDATION`; `INSUFFICIENT_INFORMATION_WITH_PLANS`.
- DR-004: `SEMANTIC_ABSTRACTION`; `ABSTRACTION_FALSE_POSITIVE`; reasoner
  skipped because no action was needed.
- DR-005: `PLAN_VALIDATION`; `INSUFFICIENT_INFORMATION_WITH_PLANS`.

These results are retained without retry, prompt tuning, source modification,
or conditions change. They do not invalidate the deterministic action gate:
the gate's feasibility/relevance evidence and the independent deterministic
tests pass.
