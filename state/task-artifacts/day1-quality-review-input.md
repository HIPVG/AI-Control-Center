# Day 1 business-quality review packet

## Scope and exclusions

Review these business-baseline artifacts only. Exclude AI-Control-Center
controller logs, temporary indices, debug output, and implementation internals.

- `C:\LocalLLM-Lab\docs\architecture\decision-reasoning-architecture.md`
- `C:\LocalLLM-Lab\docs\handoff\handoff-2026-09-18.md`
- `C:\LocalLLM-Lab\config\process-consistency-smoke.json`
- Day 1 deterministic completion evidence listed below.

## Frozen Day 1 evidence

- LocalLLM-Lab HEAD: `e33b0a410fb8647711f02ae4e6e0b66472e6eff0`
- Day 1 temporary-index baseline ref:
  `refs/heads/ai-control-center/day1-baseline-374457d3d5795395`
- Baseline commit: `374457d3d579539549df0936e3c96a47c9a1a319`
- Baseline tree: `8387ec4e7399cfd1a33c2eaebb2f352259e36727`
- Regression evidence: 61 passed, 0 failed, exit code 0.
- Day 1 criteria: 4/4 satisfied; remaining gaps empty.
- LocalLLM invocations and ResearchRuns for Day 1: 0.
- The LocalLLM-Lab working tree contains intentional uncommitted configuration
  and source changes. The baseline ref is the reproducible snapshot; it is not
  a clean working-tree commit.

## Business and architecture claims to assess

The intended product is local-first manufacturing decision support alongside
MES/ERP/Historian. It uses LLMs for semantic interpretation, issue organization,
alternative construction, and explanations; deterministic Python owns numeric
calculation, referential consistency, constraints, and state.

The product hypothesis is that a 12GB GPU plus a 12-14B model and deterministic
layers can be practically useful; 30B/24GB is not yet a requirement.

The architecture claims: Python owns facts and state; known issues and action
contracts are deterministic; the LLM proposes compact plans; Python validates
schema, preconditions, compatibility, effects, and coverage; holdout results
must not tune frozen production logic; raw response and hidden reasoning are
not retained as evaluation artifacts.

Reported research claims: a v0.4 feasible-and-relevant action gate comparison
reported 11 valid / 0 invalid plans versus v0.3.2's 10 valid / 2 invalid,
reduced reasoner prompt tokens from 11,104 to 10,345 and output tokens from
682 to 620. The same document says this does not establish lower latency or
broad generalization, and that fresh holdout, metamorphic, and counterfactual
evaluation remain the boundary. It also says v0.5 is awaiting a post-fix
controlled run.

The handoff records that Local 14B had 11/24 valid plans (45.8%) against
teacher comparisons at 100%, while blocking and mandatory issue coverage were
100%; the main stated gap is plan-selection precision. It recommends the
feasible-and-relevant gate before purchasing larger hardware.

## Review configuration

`process-consistency-smoke.json`:

```json
{"system_prompt_version":"1.0-ja","system_prompt":"あなたは製造業の業務データを確認するアシスタントです。与えられた資料だけを根拠に回答してください。業務上の不整合、確認が必要な点、影響があれば説明してください。資料に存在しない事実を推測で補わないでください。不明な点は不明と明示してください。","context_length":4096,"max_output_tokens":512}
```

## Required output

Independently identify only grounded findings. For each include severity
(`Critical`, `Major`, or `Minor`), finding, concrete packet evidence, affected
artifact, and recommended action. Assess business-objective alignment, missing
information, contradictions, evidence versus claims, reproducibility, fitness
as a Day 2 comparison baseline, downstream risks, and any unsupported facts.
Do not invent facts outside this packet.
