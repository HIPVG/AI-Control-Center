# LocalLLM-Lab Day Runner — canonical execution specification

> **Status: the single execution specification for the LocalLLM-Lab Day 1–14
> Day Runner.** This defines runtime behaviour, not architectural aspiration.
> A Codex or test report claiming PASS is not conformance evidence; section 15
> requires independent verification.

## 1. Purpose, non-goals, and authority

### Purpose

A human selects exactly one configured Day and presses **Go**. Within existing
authority, the system continues through collection, diagnosis, corrective work,
repair, and revalidation until one outcome occurs: all selected-Day criteria
validate (`COMPLETE`); a genuine external prerequisite is needed
(`EXTERNAL_ACTION_REQUIRED`); a genuine human product/safety decision is needed
(`HUMAN_ACTION_REQUIRED`); or an irrecoverable controller/safety invariant is
preserved (`FAILED_UNRECOVERABLE`).

`INSUFFICIENT_EVIDENCE` is a diagnosis input, never a terminal outcome. Go is a
continuation command, not one planner attempt. It must not stop after
`replan → replan → FAILED` merely because evidence is absent.

### Non-goals

- Do not auto-advance/select another Day, alter experiment conditions, download
  or install, use cloud, accept credentials, rewrite research outcomes, or
  push/merge `main`.
- Do not infer completion from a work-item status, model statement, source
  presence, exit-zero empty test run, or smoke result.
- Do not repair a LocalLLM research-subject quality result; retain it as evidence.
- Do not accept browser-provided commands, paths, prompts, scope, models,
  budgets, or acceptance criteria.

### Authority precedence

| Rank | Authority | Owns |
| --- | --- | --- |
| 1 | explicit current human instruction | scope, exceptions, product decisions |
| 2 | `docs/WORKING_RULES.md` | permanent operating/safety policy |
| 3 | `docs/CURRENT_WORK.md` | selected scenario, DoD, stop boundary |
| 4 | LocalLLM-Lab `docs/runbooks/work-plan-day1-14.md` | Day semantics and experiment conditions |
| 5 | **this specification** | Day Runner state/transitions/API/UI/verification |
| 6 | `config/local_llm_day_program.yaml` | versioned Day Contracts and evidence names |
| 7 | registry, Python, API, UI, tests | implementation only |
| 8 | history, roadmap, Week 1, Zero-Touch, old policy documents | context; never alternate transitions |

The YAML cannot create a transition, privilege, or completion rule absent here.
Code and an agent report cannot supersede this document. A runbook/spec conflict
stops for a human product/scope decision; it never silently changes conditions.

## 2. Roles and ownership

| Component | Must do | Must not do |
| --- | --- | --- |
| Python controller | transition, authority, fingerprints, persistence, acceptance | self-certify unverifiable evidence |
| Day Contract | versioned objective/criteria/evidence/constraints | provide an execution recipe |
| Evidence Registry | collector/resolver/validator contract per type | accept unknown evidence |
| Collector/resolver | fresh or compatible retained evidence | mark completion |
| Validator | decide named evidence satisfaction | change state |
| Gap Diagnoser | type each unsatisfied criterion and route it | expand authority/criteria |
| Corrective Work | server-derived bounded action | choose commands/paths/success criteria |
| LocalLLM | at most three bounded advisory proposals | edit, certify, set scope, decide completion |
| Codex reviewer/builder | guarded inspection/repair | grant authority/self-approve |
| Codex Expert Solver | independent repair after bounded local phase | bypass scope/Git/tests |
| Solution Catalog | teach from verified generalizable repairs | store secrets/prompts/commands/rejections |
| Human/external | genuine product/authority decision | routine repair relay |
| UI/API | project snapshot/fixed controls | calculate policy or authorize work |

## 3. Formal state machine

| State | Meaning | Terminal for invocation? |
| --- | --- | --- |
| `IDLE` | no active selected-Day execution | no |
| `PREFLIGHT` | fixed source/controller/safety prerequisites checked | no |
| `LOADING_CONTRACT` | selected Day Contract version-bound | no |
| `INVENTORY` | source state and retained candidates observed | no |
| `VALIDATING` | criterion evidence validated | no |
| `DIAGNOSING_GAP` | each unsatisfied criterion typed | no |
| `COLLECTING_EVIDENCE` | registered non-mutating provider active | no |
| `CORRECTIVE_WORK` | guarded repository/config/harness work active | no |
| `REPAIR_SUPERVISOR` | bounded engineering-repair episode active | no |
| `REVALIDATING` | post-action evidence recollected/revalidated | no |
| `PAUSED` | restart/interruption safe suspension | no; Resume |
| `STOPPED` | user stop after durable checkpoint | no; Resume |
| `COMPLETE` | all current criteria have valid evidence | yes |
| `HUMAN_ACTION_REQUIRED` | genuine human product/safety decision needed | yes until new authority |
| `EXTERNAL_ACTION_REQUIRED` | credential/permission/external prerequisite needed | yes until resolved |
| `FAILED_UNRECOVERABLE` | controller/safety invariant prevents safe continuation | yes; diagnosis required |

A work-item state is telemetry, never a Day state or completion proof.

### Complete transition table

| From | Guard/event | To | Mandatory result |
| --- | --- | --- | --- |
| `IDLE` | `Smoke(day)` | `IDLE` | record `SMOKE_*`; no work/completion claim |
| `IDLE` | `Go(configured day)` | `PREFLIGHT` | bind Day; clear only incompatible state; checkpoint |
| `PREFLIGHT` | prerequisites pass | `LOADING_CONTRACT` | record controller/config/authority versions |
| `PREFLIGHT` | external prerequisite missing | `EXTERNAL_ACTION_REQUIRED` | typed external reason; no repair |
| `PREFLIGHT` | invalid safety/controller invariant | `FAILED_UNRECOVERABLE` | preserve invariant/snapshot |
| `LOADING_CONTRACT` | valid contract/version | `INVENTORY` | persist contract/constraints |
| `LOADING_CONTRACT` | invalid contract/unknown evidence | `FAILED_UNRECOVERABLE` | fail closed before work |
| `INVENTORY` | observation complete | `VALIDATING` | source-state fingerprint/candidates persisted |
| `VALIDATING` | every criterion valid | `COMPLETE` | validator proof/final report persisted |
| `VALIDATING` | criterion invalid | `DIAGNOSING_GAP` | one diagnosis per remaining criterion |
| `DIAGNOSING_GAP` | `COLLECT_EVIDENCE` | `COLLECTING_EVIDENCE` | registered information-gain action |
| `DIAGNOSING_GAP` | repository/config correction | `CORRECTIVE_WORK` | guarded pre-authorized action |
| `DIAGNOSING_GAP` | `ENGINEERING_REPAIR` | `REPAIR_SUPERVISOR` | create/resume Repair Episode |
| `DIAGNOSING_GAP` | model-quality finding | `REVALIDATING` | retain outcome and re-evaluate criterion |
| `DIAGNOSING_GAP` | external authority | `EXTERNAL_ACTION_REQUIRED` | exact blocker and criterion |
| `DIAGNOSING_GAP` | human product decision | `HUMAN_ACTION_REQUIRED` | decision/options/rationale |
| `DIAGNOSING_GAP` | no safe nonrepeating action and no authority route | `FAILED_UNRECOVERABLE` | invariant and attempted fingerprints |
| `COLLECTING_EVIDENCE` | provider completes | `REVALIDATING` | provenance/validator record; no unchanged retry |
| `CORRECTIVE_WORK` | bounded work completes | `REVALIDATING` | before/after fingerprints and protected-path audit |
| `CORRECTIVE_WORK` | scope/Git/safety guard fails | `FAILED_UNRECOVERABLE` | preserve; do not bypass guard |
| `REPAIR_SUPERVISOR` | verified local/expert repair | `REVALIDATING` | episode/catalog outcome before re-evidence |
| `REPAIR_SUPERVISOR` | real external/human blocker | authority state | preserve episode/blocker |
| `REPAIR_SUPERVISOR` | no safe independent route remains | `FAILED_UNRECOVERABLE` | exhausted-policy evidence |
| `REVALIDATING` | evidence valid | `VALIDATING` | validate all criteria |
| `REVALIDATING` | gap remains | `DIAGNOSING_GAP` | new information/state required |
| any active nonterminal | `Stop` | `STOPPED` | durable checkpoint after atomic step |
| any active nonterminal | process restart | `PAUSED` | retain state; deadline not reset |
| `PAUSED`/`STOPPED` | `Resume` | `PREFLIGHT` or `INVENTORY` | revalidate contract/evidence |
| authority state | explicit authority + resolved prerequisite | `PREFLIGHT` | authorizing event persisted |

`COMPLETE`, both authority states, and `FAILED_UNRECOVERABLE` are invocation
terminals. Only `COMPLETE` is Day completion. New Go cannot discard an active
same-Day snapshot instead of resuming it.

## 4. Gap Diagnosis and no-op fingerprint

Each missing criterion creates `GapDiagnosis`: criterion/evidence IDs, observed
provenance, failure reason, classification, permitted action template,
authority basis, input fingerprint, action fingerprint, and expected
information gain/state change.

| Classification | Meaning | Required route |
| --- | --- | --- |
| `COLLECT_EVIDENCE` | registered evidence uncollected or retained candidate available | `COLLECTING_EVIDENCE` |
| `CORRECT_REPOSITORY_STATE` | pre-authorized non-research repository condition blocks proof | `CORRECTIVE_WORK` |
| `ENGINEERING_REPAIR` | bounded implementation/harness/parser/test-contract defect | `REPAIR_SUPERVISOR` |
| `EXPERIMENT_CONFIGURATION_REPAIR` | approved config invalid/incomplete without condition change | `CORRECTIVE_WORK`, otherwise authority gate |
| `MODEL_QUALITY_FINDING` | model behaviour is observed research result | retain/revalidate; never repair answer |
| `EXTERNAL_AUTHORITY_REQUIRED` | credential, permission, unavailable dependency/install/cloud/external action | external state |
| `HUMAN_PRODUCT_DECISION_REQUIRED` | material direction, condition expansion, destructive choice, competing interpretations | human state |

`INSUFFICIENT_EVIDENCE` must be refined to exactly one row before leaving
`DIAGNOSING_GAP`. It never authorizes `FAILED`.

Forbid an action when its fingerprint was already attempted against identical
contract version, criteria, source state, evidence cache key, configuration,
and repair input. Replanning requires changed safe state, new information, or
a different authorized class. Repeated observation is neither repair nor replan.

## 5. Evidence Registry, provenance, cache, retention

Every YAML evidence name has exactly one registered provider contract; unknown
names fail closed. A record contains type/schema/provider/validator versions;
collector/resolver identity; fixed source path/command identity; source revision
or artifact fingerprint; collection time/input fingerprint; value/status;
validator result/failure reason; compatibility decision; mutation declaration;
and retained artifact reference where applicable.

Collectors obtain current facts. Resolvers reuse retained evidence only after
file/manifest/schema/status/condition/provenance compatibility validation.
Validators alone decide satisfaction. `NOT_YET_PRODUCED` is a valid observation,
never satisfying evidence.

Cache key = at least project ID, Contract version, evidence type, provider
version, source-state fingerprint, relevant configuration fingerprint. Reuse
only a successful, non-empty, validator-passing immutable record. Failed,
empty, unknown, incompatible, and diagnostics-only records never hit cache.
Generated artifacts, models, datasets, results, failed experiments, and raw
research evidence are retained and never rewritten/deleted to pass.

## 6. Corrective Work

Corrective Work is server-derived, not an unbounded plan. It has declared
allowed paths/context, deterministic verification, scope/Git/budget guard, and
expected evidence effect; it cannot alter criteria or experiment conditions.
Persist before/after/action fingerprints, protected-path audit, deterministic
result, and evidence impact, then enter `REVALIDATING`. No promised information
gain/state change means diagnose again, never unchanged retry.

## 7. Repair Supervisor and Solution Catalog teacher loop

Only `ENGINEERING_REPAIR` enters repair. Persist `RepairEpisode` with Day,
contract/work-item/failure identity, initial evidence, absolute deadline,
catalog matches, proposal/rejection fingerprints, reviewer/builder and expert
outcomes, verification, and catalog reference.

1. Find compatible `VERIFIED` catalog entries.
2. Request no more than **three** LocalLLM proposals within a **300-second**
   local phase, using only bounded files/excerpt/catalog guidance/feedback.
3. Deterministically prefilter; guarded Codex reviewer/builder may reject or
   implement only in a managed worktree.
4. Duplicate, deterministic rejection, three attempts, deadline, missing, or
   malformed proposal automatically invokes independent **Codex Expert Solver**.
5. Expert repair remains same-scope and needs deterministic verification.
6. Verified success re-evidences/revalidates and writes a generalizable
   `VERIFIED` catalog record: cause, preconditions, bounded strategy, scope,
   verification, provenance, and outcome statistics. Later LocalLLM proposals
   receive compatible guidance. Rejections are never catalog entries.

Catalog never stores credentials, raw prompts/thinking, or executable command
authority. `Repair & Go` is not normal repair: Go performs this sequence. It
only resumes an interrupted `REPAIR_SUPERVISOR` episode whose contract/scope/
deadline/fingerprint still validate. It is disabled for evidence gaps,
model-quality findings, generic failure, completed, and authority states.

## 8. Git, scope, safety, persistence, restart

Use managed worktrees and explicit allowed paths only. Never hard-reset/clean
user work, delete protected research material, force-push, or push/merge `main`
without explicit human authority. Dirty source is evidence, never cleanup
permission. Models/browser never set commands, paths, branches, remotes,
budgets, criteria, scope, or acceptance tests.

Persist selected Day, contract/version, state/substate, criteria/evidence,
diagnoses, work items, caches/fingerprints, Git/protected audits, reports, and
episode/catalog references. Episodes/catalog persist separately. Restart turns
active state into `PAUSED`; persisted success is revalidated; repair deadline is
absolute (not a new 300 seconds); unverified in-flight work is replayed only if
fingerprints prove it was not already performed.

## 9. API contract

| Endpoint | Allowed effect | Required response |
| --- | --- | --- |
| `GET /api/local-llm/days` | read configured identities | Day/objective |
| `GET /api/local-llm/day/status` | read only | trusted snapshot + recommendation |
| `POST /api/local-llm/day/{day}/smoke` | no active run; observation only | `SMOKE_*`, never completion |
| `POST /api/local-llm/day/{day}/start` | IDLE/permitted new Day | persisted active snapshot; autonomous worker continues |
| `POST /api/local-llm/day/resume` | PAUSED/STOPPED | revalidated continuation snapshot |
| `POST /api/local-llm/day/repair-and-go` | qualifying interrupted repair only | episode result/typed refusal |
| `POST /api/local-llm/day/stop` | active nonterminal | durable stop checkpoint |

Snapshot must include state, Day, contract version, criterion evidence,
diagnoses, active/last work item, report, blocker, audit-relevant fingerprints/
cache metadata, and server-derived Recommended Action. Refusals must be typed;
no silent reset/replacement/manufactured success.

## 10. UI and Recommended Action contract

UI renders API state; it derives no policy. Recommendation contains `action_id`,
label, enabled, reason, and typed blocker/criterion context.

| Control | Enabled exactly when |
| --- | --- |
| Smoke | no active execution and configured selected Day |
| Go | configured selected Day and `IDLE`, or explicit safe new-Day reset |
| Resume | `PAUSED`/`STOPPED` with resumable validated snapshot |
| Stop | active nonterminal state |
| Repair & Go | qualifying interrupted repair episode only |
| Select next Day | `COMPLETE`; selection itself starts no work |

Active state recommends `WAIT`; incomplete stoppable state recommends `RESUME`;
complete recommends `SELECT_NEXT_DAY`; authority states recommend
`SHOW_REQUIRED_ACTION`; unrecoverable recommends `SHOW_SAFETY_FAILURE`; only
qualifying repair recommends `REPAIR_AND_GO`. Enabled UI and endpoint must
match exactly. `SMOKE_PASS != DAY_COMPLETE`: Smoke cannot set evidence or enable
next-Day selection.

## 11. Legitimate FAILED boundary

`FAILED_UNRECOVERABLE` requires invalid/missing trusted contract/registry,
persistence/state-machine corruption, scope/Git/protected-artifact violation,
unclassifiable safety invariant, or proof that every alternative is forbidden
or repeated and neither human nor external authority can resolve it. Report the
invariant, fingerprints, preserved evidence, and why it is not an authority
gate. Missing evidence, planner exhaustion, or repeated unchanged plan alone
never qualifies.

## 12. Repository-document relationship

`docs/ARCHITECTURE.md`, `docs/LOCALLLM_DAY1_14_AUTONOMOUS.md`, and
`docs/LOCAL_LLM_REPAIR_GOVERNANCE.md` are compatibility/history pointers, not
execution authorities. `AUTONOMOUS_DAY.md`, `AUTONOMOUS_NEXT_ACTION.md`,
`DAILY_OPERATION.md`, Zero-Touch documents, and `MODEL_ROUTING.md` describe
legacy/general queue or adjacent capabilities: they can contribute guards but
cannot control this state machine. Week 1 documents are historical. Roadmap,
progress, engineering history, real-integration, fault-repair, and external
validation documents are planning/evidence records, not runtime authority.

## 13. Current implementation gap (2026-09-22)

Production `LocalLLMDayProgram._execute()` has `MAX_REPLANS = 2` and turns
unmet evidence into `DAY_INSUFFICIENT_EVIDENCE`/`DAY_NO_OP_REPLAN` plus
`FAILED`. Its model only has `IDLE/RUNNING/PAUSED/COMPLETE/FAILED/STOPPED`, not
the formal diagnosis/corrective/authority states. The engine's ordinary static
and dynamic work adapter emits empty evidence, so it cannot close later-Day
criteria through registered evidence. The UI correctly disables Repair & Go
when server recommendation is not implementation-defect repair, thereby exposing
the incorrect terminal contract. Tests assert the old no-op failure path and
use synthetic executors for repair/teacher-loop proofs; they do not prove a
production one-Go recovery or browser UI E2E. Any prior
`ARCHITECTURE_CONFORMANCE: PASS` is therefore not evidence.

This gap record is not authorization for implementation changes.

## 14. Design-conformance tests required before PASS

1. Registry names/unknown fail-closed, retained compatibility/provenance/cache
   invalidation/non-empty test evidence.
2. Every transition-table row: restart, stop/resume, gap classes, no-op
   fingerprints, authority gates, strict failed boundary.
3. Disposable production-path E2E: **Smoke → Go once → collect/diagnose/
   corrective work or repair/revalidate → COMPLETE**, no manual Repair & Go;
   plus separate genuine authority-gate E2Es.
4. Real engine-adapter repair E2E: ≤3 LocalLLM proposals, persisted 300-second
   deadline, automatic Expert Solver, deterministic verification, catalog write,
   then catalog guidance in a later episode.
5. Running-server browser E2E: buttons, recommendation/API equivalence,
   `SMOKE_PASS != DAY_COMPLETE`, one-Go continuation, disabled Repair & Go for
   evidence gaps, enabled only for qualifying interrupted repair.
6. Independent inspection of this spec, production path, API responses, and
   rendered UI. **Codex self-report is never evidence.**

This last requirement is a permanent-rule candidate: independently verify design,
production path, and actual UI before accepting an agent PASS.
