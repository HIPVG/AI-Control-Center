# LocalLLM-Lab Authoritative Day 1-14 Autonomous Execution

## Source of truth

LocalLLM-Lab `docs/README.md` identifies these as current:
- execution sequence: `docs/runbooks/work-plan-day1-14.md`
- architecture: `docs/architecture/decision-reasoning-architecture.md`
- resume evidence: `docs/handoff/handoff-2026-09-18.md`

The older `docs/week1-runbook.md` is historical/component guidance and MUST NOT
drive current autonomous sequencing when it conflicts with the source-of-truth
map.

## Resume rule

Do not assume a Day number from chat history.

At startup:
1. inspect the authoritative runbook;
2. inspect local Git status/branch/log and current source/config/tests;
3. inspect available local generated artifacts and handoff evidence without
   staging or modifying them;
4. determine the first incomplete Day from reproducible evidence;
5. resume there.

Days are sequential work units, not calendar dates.

## Current Day 1-14 sequence

1. repository reconciliation and baseline freeze
2. DRAP v0.4 Feasible + Relevant Action Gate
3. v0.3.2 versus v0.4 regression
4. fresh holdout, metamorphic, counterfactual
5. plan-selection precision / local-versus-teacher gap
6. temporal-state design
7. temporal-case validation
8. Novelty Scout proof of concept
9. explanation and trade-off stage
10. end-to-end performance
11. product configuration
12. reproducibility and operations
13. full regression and fresh holdout
14. sprint review

## One-pass blocker sweep

Before executing the next incomplete Day, inspect ALL remaining Days through Day
14 and produce one internal blocker matrix.

For every Day, record:
- required source/config/schema/test capability;
- required local model/runtime;
- required generated artifact / frozen baseline / teacher packet;
- required runner and CLI entry point;
- expected output artifact;
- whether the action is deterministic-only or uses local inference;
- expected timeout / resource boundary;
- whether the prerequisite exists now;
- blocker classification;
- whether it is auto-resolvable under existing authority.

The sweep must include at least:
- Git cleanliness / branch / remote / staged-diff preservation;
- frozen v0.3.2 + ACIA baseline availability;
- DRAP v0.4 gate implementation dependencies;
- regression runner and baseline/result compatibility;
- fresh holdout generation and anti-overfit controls;
- metamorphic and counterfactual runner availability;
- teacher packet availability and whether new cloud generation is actually
  required;
- shared Python validator inputs;
- temporal-state schema/design dependencies;
- temporal contradiction test fixtures;
- Novelty Scout model/runner and proposal-vs-fact contract;
- explanation/trade-off stage inputs and output contract;
- performance telemetry and runtime readiness;
- product-tier evidence inputs;
- backup/recovery/logging docs and scripts;
- Day 13 new fresh holdout generation;
- Day 14 summary inputs.

## Pre-authorized routine work

The following MUST NOT create a Human Gate:

- source/config/schema/test implementation explicitly required by the
  authoritative Day 1-14 runbook;
- internal harness/runner/adapter repair;
- parser/terminal JSON/result-contract repair;
- bounded parent/child timeout repair;
- artifact finalization / interrupted-run bookkeeping repair;
- state persistence/resume/next-action repair;
- deterministic test fixture and fresh-holdout generator repair;
- wiring existing local runners/models already present and already approved for
  the documented role;
- documentation/source-of-truth alignment;
- deterministic analysis and report generation;
- one controlled rerun after a confirmed harness/code defect is repaired;
- Builder use for a genuine code/harness defect within existing repository/scope
  policy.

Do not blindly rerun an unchanged failed inference.

## Pre-authorized experiment execution

Initial execution of a Day's already-defined local experiment is authorized when:
- the model/runtime is already installed locally and approved for that documented
  role;
- all experiment conditions come from tracked approved config/runbook;
- no new cloud access, model/tool install, context expansion, destructive action,
  or credential change is required.

A harness failure is not a model-quality result.
A model-quality finding is not automatically a code defect.

## Batch human-gate policy

Do not stop for one blocker at a time.

After the full blocker sweep and all auto-resolvable repairs, collect ALL
remaining genuine authority/external blockers across the remaining Days into one
batch Human Gate.

Examples:
- a required model/tool is absent and would need download/install;
- provenance/license approval is required and cannot be established from trusted
  evidence;
- new cloud/teacher generation is required rather than reusing existing packets;
- a new context/output/reasoning condition would expand approved experiment
  authority;
- destructive Git action, credential change, or external permission is required;
- a material product-direction choice has multiple valid options with no
  deterministic selection rule.

The batch gate must list each blocker, affected Day(s), minimum decision, and
what can continue independently.

## Current observed harness failure

Artifact:
`C:\LocalLLM-Lab\results\experiments\EXP-20260921T220217-5542f4aa55`

Observed:
- manifest status remained `preparing`;
- response_count = 0;
- runner produced no terminal JSON.

This is pre-authorized for internal diagnosis and repair. Do not ask for human
authorization to diagnose/repair the existing harness. Before any real rerun,
inspect bounded exit/stderr/artifact evidence, reproduce safely where possible,
repair, run deterministic tests, and then perform at most one controlled rerun
of the already-approved experiment if still relevant to the CURRENT
source-of-truth plan.

If that cross-family experiment is no longer part of the current authoritative
Day 1-14 path, preserve the artifact as historical evidence and do not spend
more runtime on it merely to satisfy the obsolete runbook.

## Human gate

`DAY1_14_BATCH_AUTHORITY_REVIEW`

Only use this gate after the one-pass blocker sweep and automatic resolution of
all routine/internal blockers.
