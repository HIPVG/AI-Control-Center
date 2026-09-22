# AI Control Center autonomous Day architecture

## Purpose and authority

AI Control Center is a Windows-first local control plane for evidence-based,
bounded autonomous engineering and research operation. A person selects one
configured Day and presses **Go**. Python owns facts, state, safety and
acceptance; LocalLLM and Codex provide bounded reasoning or implementation
roles. The system stops after the selected Day. It does not advance a Day,
alter experimental conditions, push `main`, or turn a research finding into a
code repair.

`docs/WORKING_RULES.md` is the governing policy and the selected Day Contract
is the completion authority. This document is the structural baseline. Older
Week 1, Goal-to-Plan and Zero-Touch documents are retained or superseded
features; they are not alternate Day 1-14 control paths.

## Canonical control loop

```text
SELECT DAY -> PREFLIGHT -> LOAD CONTRACT -> INVENTORY
    -> REUSE VALID EXISTING EVIDENCE -> COLLECT MISSING EVIDENCE -> VALIDATE
    -> all criteria satisfied? -- yes --> DAY_COMPLETE -> STOP
                              -- no  --> GAP DIAGNOSIS
GAP DIAGNOSIS
  evidence collectible              -> COLLECT EVIDENCE
  repository state must change      -> CORRECTIVE WORK
  engineering implementation defect -> REPAIR SUPERVISOR
  model-quality research finding    -> PRESERVE AS EVIDENCE
  experiment configuration issue    -> BOUNDED CONFIGURATION WORK
  external/human authority          -> HUMAN / EXTERNAL ACTION REQUIRED
state-changing work -> RECOLLECT EVIDENCE -> VALIDATE
```

A work-item terminal state is operational telemetry, never completion proof.
The Evidence Registry is the only acceptance authority. Repeating an unchanged
observation is neither repair nor replan: an action requires a new state
fingerprint or information gain.

## Components and ownership

| Component | Responsibility | May accept completion? |
| --- | --- | --- |
| Day / Goal Contract | Versioned objective, criteria, evidence requirements and constraints | no |
| Project Adapter | Root, protected paths, collectors, retained resolvers, corrective operations and Git behavior | no |
| Evidence Registry | Typed provider and semantic validator for every evidence type | yes, through validator only |
| Evidence Collector / Retained Resolver | Fresh deterministic evidence or compatible manifest-backed history | no |
| Evidence Validator | Typed content, provenance, status and compatibility checks | yes |
| Gap Diagnoser / Corrective Planner | Classify unsatisfied criteria and choose bounded policy-conforming work | no |
| Work Executor | Server-derived guarded work in a managed worktree | no |
| Repair Supervisor | Persistent time-bounded engineering repair episode | no |
| Solution Catalog | Persistent verified repair knowledge, separate from Day state | no |
| LocalLLM Proposal Engine | Up to three advisory proposals with catalog knowledge and rejection feedback | no |
| Codex Reviewer / Builder / Expert Solver | Review, scoped repair, independent escalation when required | no |
| State / Persistence | Contracts, evidence, fingerprints, episodes and catalog references | no |
| Scope / Git / Budget guards | Paths, commands, retries, time and Git boundaries | no |
| Human Authority Gate | Credentials, destructive acts and genuine product decisions | no |
| UI/API projection | Trusted state and fixed server operations only | no |

LocalLLM-Lab is Adapter #1. An adapter is a small Python interface/registry,
not a plugin marketplace: it contributes root/path protections, evidence
providers, deterministic tests, retained resolvers, allowed corrective
operations, Git checkpoint behavior and the authoritative runbook source.

## Evidence registry

Every configured evidence type has a registered provider contract and typed
validator. `NOT_YET_PRODUCED` is a valid provider outcome; a generic verified
envelope is not a validator. Unknown evidence names fail closed. Common
provenance fields are evidence type, collector/resolver, source paths/commands,
source revision or artifact fingerprint, collection time, validator result and
compatibility result. `Reuse` means only after all such checks; `Mutates` is
whether collection itself changes state.

| Evidence type | Days | Producer | Validator and failure reasons | Reuse | Mutates |
| --- | --- | --- | --- | --- | --- |
| git_head | 1 | deterministic collector | Git head/commit shape; missing Git or malformed SHA | no | no |
| origin_ref | 1 | deterministic collector | Remote/upstream/SHA relation; absent upstream | no | no |
| status_audit | 1 | deterministic collector | Typed index/worktree audit; unavailable status | no | no |
| staging_audit | 1 | deterministic collector | Generated data unstaged; staged protected output | no | no |
| documentation_check | 1 | deterministic collector | Authoritative relationship checks; unreadable/inconsistent docs | no | no |
| test_result | 1,2 | deterministic collector/work adapter | Exit zero plus collected and passed > 0; timeout/empty/failure | fingerprint | no |
| commit_ref | 1 | deterministic collector | Existing reproducible commit; missing/dirty source | no | no |
| source_check | 2,6,8,9 | work result adapter | Registered source assertion; missing/mismatched assertion | fingerprint | corrective only |
| deterministic_tests | 2,6,7,8,9 | work result adapter | Named collected tests pass; empty/failing suite | fingerprint | corrective only |
| architecture_check | 2,6 | work result adapter | Named architecture assertion; inconsistent design | fingerprint | corrective only |
| baseline_ref | 2 | retained resolver | Compatible baseline commit/artifact; incompatible/missing | yes | no |
| preservation_audit | 2 | deterministic collector | Protected output retained/unstaged; mutation/staging violation | fingerprint | no |
| v032_artifact | 3 | retained research resolver | v0.3.2 manifest/schema/status; missing/stale/invalid | yes | no |
| v04_artifact | 3 | retained research resolver | v0.4 manifest/schema/status; missing/stale/invalid | yes | no |
| condition_record | 3,10 | research artifact | Fixed version/model/condition fingerprint; absent/drift | yes | research only |
| comparison_metrics | 3 | research artifact | Required counts/cost/coverage metrics; incomplete | yes | research only |
| failure_policy | 3 | retained resolver | Retained failure/no-rerun policy record; missing | yes | no |
| holdout_manifest | 4,13 | retained resolver | Frozen unseen input manifest; missing/mutable/mismatch | yes | no |
| architecture_ref | 4,13 | retained resolver | Frozen architecture revision; missing/mismatch | yes | no |
| dagb_artifact | 4 | research artifact | Fresh/metamorphic/counterfactual schema; invalid | yes | research only |
| anti_leakage_check | 4 | deterministic/work adapter | Oracle and hard-code checks; absent/failure | fingerprint | no |
| retained_failures | 4,13 | retained resolver | Retained typed outcomes; missing/rewritten | yes | no |
| validator_result | 5 | research artifact | Shared validator version/result; mismatch/failure | yes | research only |
| local_artifact | 5 | research artifact | Local result provenance and status; missing/invalid | yes | research only |
| teacher_evidence | 5 | retained resolver | Frozen comparable Teacher artifact; incompatible/unstated limits | yes | no |
| limitation_record | 5,10 | decision artifact | Explicit comparability/stability limits; missing | yes | no |
| decision_record | 5 | decision artifact | Evidence-linked critic/selector decision; unsupported claim | yes | no |
| schema_contract | 6,9 | work result adapter | Versioned schema and parser; missing/invalid | fingerprint | corrective only |
| provenance_test | 6 | work result adapter | Named provenance test; uncollected/failing | fingerprint | corrective only |
| validation_report | 7 | work result adapter | Temporal validation result; absent/failing | fingerprint | corrective only |
| novelty_artifact | 8 | research artifact | Bounded proposal run/status; missing/invalid | yes | research only |
| provenance_artifact | 8 | research artifact | Proposal provenance record; absent | yes | research only |
| nonmutation_test | 8,9 | work result adapter | Canonical-plan/state nonmutation check; mutation/failure | fingerprint | corrective only |
| performance_artifact | 10 | research artifact | Calls/tokens/time/VRAM/CPU/RAM; incomplete metrics | yes | research only |
| deployment_matrix | 11 | decision artifact | Tier/escalation matrix with evidence; unsupported | yes | no |
| hardware_evidence | 11 | retained resolver | Cited measured hardware evidence; missing/overclaim | yes | no |
| advisory_record | 11 | decision artifact | Explicitly non-binding workload limits; missing | yes | no |
| operator_docs | 12 | deterministic collector | Required operating content; unreadable/missing | fingerprint | no |
| recovery_check | 12 | work result adapter | Named recovery verification; failure | fingerprint | corrective only |
| gitignore_check | 12 | deterministic collector | Generated data exclusions; absent/failure | fingerprint | no |
| full_test_result | 13 | deterministic collector | Complete suite collection/execution; empty/failing | fingerprint | no |
| result_artifact | 13 | research artifact | Frozen new holdout result; missing/invalid | yes | research only |
| classification_record | 13 | research artifact | Typed retained failure classification; absent/invalid | yes | research only |
| status_summary | 13 | decision artifact | Evidence-linked current status; missing/unsupported | yes | no |
| sprint_review | 14 | decision artifact | Complete advisory review; missing/unsupported | yes | no |
| human_review_marker | 14 | human marker | Explicit authority marker; absent/invalid | yes | no |

The registry enumerates all 46 configured names. This compact table does not
authorize grouped fallback validation: every name has a concrete strategy.

### Retained research evidence

The LocalLLM-Lab adapter resolves retained Day 2 and Day 4 evidence through the
registry. A result counts only when expected files exist, manifest/schema and
terminal status validate, configuration/version/fingerprint matches, provenance
is recorded and the evidence-specific validator passes. Valid existing research
output is reused before inference.

## Repair supervision and learning

Only `IMPLEMENTATION_DEFECT` enters this subsystem. A persisted Repair Episode
contains ID, project/Day/work item, failure class and stable bounded fingerprint,
initial evidence, start/deadline, catalog matches, proposals, rejection
feedback, Codex review/outcome, expert-solver outcome, deterministic
verification and catalog reference. Its clock is injectable for tests.

```text
classify -> fingerprint -> find VERIFIED catalog entries
 -> LocalLLM proposal 1..3 (bounded files/context)
 -> deterministic prefilter + Codex review/builder + postcheck
 -> verified success: re-evidence and catalog update if generalizable
 -> reject/repeat/deadline/exhaustion: Codex Expert Solver
 -> independent investigation -> guarded fix -> deterministic verification
 -> re-evidence -> persistent VERIFIED catalog entry
```

`repair_deadline_seconds = 300` is the five-minute local phase and
`MAX_LOCAL_PROPOSALS = 3` is enforced episode policy. The phase stops earlier
for duplicate solution fingerprints, deterministic rejection, all reviewer
rejections or a verified result.

`state/repair-catalog.json` is JSON persistence behind a small interface. A
verified record includes ID; generic/project scope and optional project ID;
failure class/signature; title, symptoms, cause, diagnostic steps, strategy,
preconditions, allowed affected scope and verification; source/status;
timestamps; uses; success/failure counts; and last-use time. It never stores
credentials, secrets or arbitrary shell authority. Only non-retired `VERIFIED`
records guide proposals. Matching ranks exact class/component/signature, then
compatible project entries and then generic entries. Rejected proposals are
episode history, not catalog entries.

## State, cache, safety and UI invariants

- Python owns facts, transitions, execution authority, acceptance, scope, Git
  and retry/escalation enforcement; model proposals never self-certify.
- Only registered evidence can satisfy criteria; unknown evidence fails closed.
- Replan requires information gain or a changed state fingerprint, and that
  fingerprint cannot repeat an identical action.
- Research-subject LocalLLM failure is evidence and never enters repair;
  engineering-assistant output is advisory only.
- Catalog persistence is independent of selected Day, process restart and Day
  switch. Generalizable verified expert repairs enter it.
- Smoke/preflight is never completion. A Day never auto-advances. Generated
  research artifacts are protected. No component pushes or rewrites `main`.

The cache key includes project ID, contract version, evidence type, provider
version and source-state fingerprint. Expensive deterministic work is not
recollected on an unchanged key. Test evidence requires an observed collection
and pass count above zero, preventing exit-zero empty pytest from passing.

On restart `RUNNING` becomes `PAUSED`; repair deadline uses persisted timing,
not a fresh five minutes. The UI renders `SMOKE_PASS` /
`SMOKE_SOURCE_MISSING`, not generic `SUCCESS`. `DAY_COMPLETE` is shown
only when all validators pass. Recommended Action is a direct projection of an
executable backend state. The browser supplies no commands, source paths,
criteria, model settings, budgets or Git authority.

Routine engineering failure follows cheap-local proposal -> deterministic
verification -> bounded Codex review/expert escalation. Verified expert
solutions become persistent repair knowledge for future local proposals.
