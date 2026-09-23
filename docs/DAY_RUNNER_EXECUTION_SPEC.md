# LocalLLM-Lab Day Runner — Canonical Execution Specification

**Status:** External canonical design
**Version:** v1.0
**Authority:** This document defines Day Runner execution semantics. Codex/Work is the Builder, not the design authority. Final conformance is determined by an external checker.

## 1. Purpose

A human selects exactly one configured Day from Day 1–14 and presses **Go once**.

Within already-authorized scope, AI Control Center must continue autonomously through retained evidence reuse, evidence collection, normal selected-Day work, deterministic validation, repository/configuration correction, engineering repair, and revalidation until one legitimate terminal condition occurs:

- `COMPLETE`
- `HUMAN_ACTION_REQUIRED`
- `EXTERNAL_ACTION_REQUIRED`
- `FAILED_UNRECOVERABLE`
- `STOPPED`
- `PAUSED`

`COMPLETE` alone means that the selected Day is complete.

`INSUFFICIENT_EVIDENCE` is never a terminal Day outcome. It is an observation that must be refined into a concrete diagnosis and legal next action.

Normal internal repair must not require a second human click.

## 2. Non-goals

The Day Runner must not:

- auto-advance to another Day;
- silently change experiment conditions;
- install software or use cloud services without authority;
- request credentials through normal repair;
- rewrite poor model results into better research results;
- push or merge `main`;
- infer completion from a task terminal state, source presence, `exit 0` with zero tests, or Smoke;
- accept browser-supplied shell commands, paths, model choices, scopes, budgets, or acceptance criteria.

## 3. Authority precedence

1. Explicit current human instruction
2. `docs/WORKING_RULES.md`
3. `docs/CURRENT_WORK.md`
4. LocalLLM-Lab authoritative Day 1–14 runbook
5. This canonical execution specification
6. `config/local_llm_day_program.yaml`
7. Python implementation, registries, API, UI, and tests
8. Engineering history, roadmap, Week 1, Zero-Touch, and legacy/reference documents

The runbook owns **what the Day means**. This specification owns **how the Day is executed and completed**. Codex/Work cannot redefine either.

## 4. Formal Day Runner state machine

Formal states:

- `IDLE`
- `PREFLIGHT`
- `LOADING_CONTRACT`
- `INVENTORY`
- `VALIDATING`
- `DIAGNOSING_GAP`
- `COLLECTING_EVIDENCE`
- `EXECUTING_DAY_WORK`
- `CORRECTIVE_WORK`
- `REPAIR_SUPERVISOR`
- `REVALIDATING`
- `PAUSED`
- `STOPPED`
- `COMPLETE`
- `HUMAN_ACTION_REQUIRED`
- `EXTERNAL_ACTION_REQUIRED`
- `FAILED_UNRECOVERABLE`

A work-item state is operational telemetry only. It is never Day completion proof.

### 4.1 Main flow

```text
IDLE
  -> PREFLIGHT
  -> LOADING_CONTRACT
  -> INVENTORY
  -> VALIDATING
      -> all evidence valid -> COMPLETE
      -> gap remains -> DIAGNOSING_GAP
          -> COLLECTING_EVIDENCE
          -> EXECUTING_DAY_WORK
          -> CORRECTIVE_WORK
          -> REPAIR_SUPERVISOR
          -> HUMAN_ACTION_REQUIRED
          -> EXTERNAL_ACTION_REQUIRED
  -> REVALIDATING
  -> VALIDATING
```

The loop continues while a legal, non-repeating, authorized action can produce new information or state.

## 5. Complete transition semantics

### `IDLE`
- `Smoke(day)` keeps state `IDLE`.
- `Go(configured day)` transitions to `PREFLIGHT`.

### `PREFLIGHT`
Checks selected project, selected Day, contract availability, registry integrity, runtime prerequisites, Git/scope/safety invariants, and required external authority.

Transitions:
- prerequisites pass -> `LOADING_CONTRACT`
- external prerequisite missing -> `EXTERNAL_ACTION_REQUIRED`
- safety/controller invariant invalid -> `FAILED_UNRECOVERABLE`

### `LOADING_CONTRACT`
Bind exact Day Contract version and current runbook/config authority. Unknown evidence types fail closed.

Transitions:
- valid -> `INVENTORY`
- invalid contract/unknown evidence -> `FAILED_UNRECOVERABLE`

### `INVENTORY`
Collect Git state, source state, retained artifact candidates, existing Evidence Store entries, configuration fingerprints, and protected-path status. Then -> `VALIDATING`.

### `VALIDATING`
Run registered validators against Evidence Store records.
- all criteria satisfied -> `COMPLETE`
- any requirement missing/invalid -> `DIAGNOSING_GAP`

### `DIAGNOSING_GAP`
Create one `GapDiagnosis` per unsatisfied `criterion_id × evidence_type` and classify it into exactly one legal class:

- `COLLECT_EVIDENCE`
- `PRODUCE_DAY_EVIDENCE`
- `CORRECT_REPOSITORY_STATE`
- `ENGINEERING_REPAIR`
- `EXPERIMENT_CONFIGURATION_REPAIR`
- `MODEL_QUALITY_FINDING`
- `EXTERNAL_AUTHORITY_REQUIRED`
- `HUMAN_PRODUCT_DECISION_REQUIRED`

`INSUFFICIENT_EVIDENCE` must be refined into one of these before leaving diagnosis.

### `COLLECTING_EVIDENCE`
Run a registered, non-mutating collector or retained resolver. Then -> `REVALIDATING`.

### `EXECUTING_DAY_WORK`
Perform normal selected-Day work that creates missing evidence. This is not repair. Then -> `REVALIDATING`.

### `CORRECTIVE_WORK`
Perform a bounded, pre-authorized repository/configuration correction that allows normal Day work/evidence collection to proceed. Then -> `REVALIDATING`.

### `REPAIR_SUPERVISOR`
Repair only genuine engineering defects.
- verified repair -> `REVALIDATING`
- genuine authority blocker -> corresponding authority state
- no safe repair route remains -> `FAILED_UNRECOVERABLE`

### `REVALIDATING`
Re-inventory affected state, recollect affected evidence, run result adapters and validators, then return to `VALIDATING`.

### `PAUSED` / `STOPPED`
Resume only after contract/version/safety revalidation.

### Authority states
`HUMAN_ACTION_REQUIRED` and `EXTERNAL_ACTION_REQUIRED` preserve the selected Day and full state. After blocker resolution, `Resume` reruns preflight, verifies blocker resolution, revalidates contract/version, and continues the same Day.

### `FAILED_UNRECOVERABLE`
Allowed only when a controller/safety invariant makes safe continuation impossible. Missing evidence, planner exhaustion, or repeated planner output alone are insufficient.

## 6. Gap Diagnosis model

Each missing evidence requirement has a persisted `GapDiagnosis` with at least:

```text
criterion_id
evidence_type
failure_reason
classification
strategy_id
authority_basis
input_fingerprint
action_fingerprint
expected_information_gain
expected_state_change
attempted_action_fingerprints
```

A criterion may have multiple evidence requirements and therefore multiple diagnoses.

Example:

```text
criterion: regression_baseline

test_result = VALID
commit_ref = MISSING
```

Only `commit_ref` receives an action. The already-valid test must not be rerun merely because another evidence type is missing.

## 7. Evidence Store

Raw task results never satisfy criteria directly.

Required path:

```text
Work
 -> Result Adapter
 -> Evidence Record
 -> Evidence Validator
 -> Evidence Store
 -> Criterion Evaluation
```

### 7.1 EvidenceRecord

Minimum fields:

```text
record_id
project_id
day
contract_version
evidence_type
provider_id
provider_version
validator_id
validator_version
source_paths
source_revision
source_fingerprint
configuration_fingerprint
collected_at
value
status
validator_result
validator_failure_reason
compatibility_result
retained_artifact_reference
```

Criteria should reference validated evidence records by ID/type rather than trust arbitrary work-item dictionaries.

## 8. Two registries

### 8.1 Evidence Validator Registry
Key: `evidence_type`

Responsibility: determine whether evidence is valid.

All 46 configured evidence types must be registered. No generic fallback. Unknown evidence fails closed.

### 8.2 Evidence Acquisition Strategy Registry
Key: `(day, evidence_type)`

Responsibility: determine the legal route and fixed authority/safety boundaries when evidence is missing or invalid. For `RESEARCH_RUN`, this registry does not need to name one exact script/config/input tuple; concrete execution details may be planned at runtime under §9.1.

Minimum fields:

```text
day
evidence_type
provider_id
validator_id
reuse_policy
collection_mode
missing_classification
action_template_id
execution_mode
mutation_policy
research_sensitive
authority_requirement
result_adapter
expected_information_gain
expected_state_change
allowed_output_scope
```

This registry, not Codex, decides the missing-evidence route.

## 9. Server-owned Action Templates

Codex may operate only inside an already-authorized template.

Execution modes:
- `READ_ONLY`
- `BASELINE_CHECKPOINT`
- `ENGINEERING_WORKTREE`
- `RESEARCH_RUN`
- `DECISION_OR_DOCUMENTATION_WORKTREE`

Each template declares:

```text
action_id
input evidence type(s)
allowed paths/output scope
context scope
execution mode
expected state/information change
verification
post-action evidence types
research mutation policy
Git policy
```

Codex must not choose gap classification, criterion, evidence type, project, authority class, mutation mode, protected paths, or acceptance semantics.

### 9.1 Runtime Research Execution Planning

For `RESEARCH_RUN`, the acquisition strategy and Action Template authorize the
**kind of work and its safety/acceptance boundaries**. They do **not** require a
predeclared static mapping from every research action to one exact
script/config/input tuple.

The following remain server-owned and fixed before runtime planning:

- selected Day and Day Contract;
- required evidence types;
- authoritative runbook and research semantics;
- action template and execution mode;
- allowed source/context scope;
- allowed output scope;
- mutation policy;
- protected paths;
- model/research authority;
- validator and acceptance semantics;
- holdout/freeze/nonmutation constraints.

Within those fixed boundaries, an Architect may inspect the trusted repository,
authoritative runbook, current evidence, existing scripts, existing configs, and
existing input/manifest files and propose a bounded `ResearchExecutionPlan`
for the concrete execution.

Minimum `ResearchExecutionPlan` fields:

```text
action_id
day
script_path
config_paths
input_paths
output_paths
arguments
condition_fingerprint
expected_evidence_types
reference_sources
```

The concrete `script_path`, `config_paths`, `input_paths`, `output_paths`, and
bounded `arguments` are runtime plan details, not authority.

Python must validate the plan before execution. The Research Guard must prove:

- all referenced paths exist where existence is required;
- every path is inside the trusted/allowed scope;
- the selected script/config/input combination is compatible with the selected
  Day and authoritative runbook;
- no forbidden source/config/schema/test mutation is requested;
- frozen architecture / holdout / fixed-condition requirements are preserved;
- output locations are approved research artifact/log/result locations;
- expected evidence types match the registered `(day, evidence_type)` strategy;
- the semantic condition fingerprint is recorded before execution.

If exactly one safe bounded execution plan can be derived from trusted
repository evidence, it may execute without human relay.

If no safe bounded plan can be derived, fail closed and diagnose the reason.

If multiple materially different candidate plans remain and choosing among them
would change research conditions, experiment meaning, holdout definition, or
another human-owned semantic decision, route to:

`HUMAN_PRODUCT_DECISION_REQUIRED`

Absence of a static Day-to-script mapping is **not by itself** an error and must
not become `RESEARCH_CONDITION_NOT_APPROVED`.

The controller must not invent new research conditions merely to make execution
possible.

## 10. Gap classes

### `COLLECT_EVIDENCE`
Evidence exists or can be observed with a registered read-only provider. Route: `COLLECTING_EVIDENCE`.

### `PRODUCE_DAY_EVIDENCE`
The selected Day has not yet performed the normal work that creates required evidence. Route: `EXECUTING_DAY_WORK`.

### `CORRECT_REPOSITORY_STATE`
A bounded pre-authorized repository/environment state blocks normal collection or Day work. Route: `CORRECTIVE_WORK`.

### `ENGINEERING_REPAIR`
Unexpected implementation/harness/parser/test-contract/controller defect. Route: `REPAIR_SUPERVISOR`.

### `EXPERIMENT_CONFIGURATION_REPAIR`
Approved configuration is malformed/incomplete and can be corrected without changing the experimental condition. Route: `CORRECTIVE_WORK`. If fixing it changes the research condition, route to human authority.

### `MODEL_QUALITY_FINDING`
A poor model result is a research result. Preserve it. Never repair the answer merely to improve the result.

### `EXTERNAL_AUTHORITY_REQUIRED`
Credentials, external permission, unavailable required dependency, installation, cloud access, etc.

### `HUMAN_PRODUCT_DECISION_REQUIRED`
Material scope expansion, changing research conditions, destructive choice, competing product/research interpretations, or explicit human review markers.

## 11. Normal Day work versus repair

Missing evidence does not imply a defect.

Example:

```text
Day 4 dagb_artifact missing
 -> Day 4 research has not yet been run
 -> PRODUCE_DAY_EVIDENCE
 -> RESEARCH_RUN
```

not:

```text
dagb_artifact missing
 -> ENGINEERING_REPAIR
```

Repair is only for unexpected implementation failure during otherwise-authorized work.

## 12. Day 1–14 Action Map

### Day 1 — Repository reconciliation and baseline freeze
Read-only evidence:
- `git_head`
- `origin_ref`
- `status_audit`
- `staging_audit`
- `documentation_check`
- `test_result`

Normal Day work:
- `commit_ref` via `BASELINE_CHECKPOINT`

### Day 2 — Feasible + Relevant Action Gate
Retained/read-only:
- `baseline_ref`
- `preservation_audit`

Normal engineering work:
- `source_check`
- `deterministic_tests`
- `architecture_check`
- `test_result`

Action: `D2_FEASIBLE_RELEVANT_GATE`
Execution: `ENGINEERING_WORKTREE`

### Day 3 — v0.3.2 versus v0.4 regression
Prerequisite/retained:
- `v032_artifact`
- `v04_artifact`

Normal research:
- `condition_record`
- `comparison_metrics`
- `failure_policy`

Action: `D3_FIXED_REGRESSION`
Execution: `RESEARCH_RUN`

### Day 4 — Fresh holdout / metamorphic / counterfactual
Research setup:
- `holdout_manifest`
- `architecture_ref`

Research output:
- `dagb_artifact`
- `retained_failures`

Deterministic postcheck:
- `anti_leakage_check`

Actions:
- `D4_FREEZE_HOLDOUT`
- `D4_DAGB_RUN`
- `D4_ANTI_LEAKAGE`

### Day 5 — Plan-selection precision
Research:
- `validator_result`
- `local_artifact`

Retained/external:
- `teacher_evidence`

Decision:
- `limitation_record`
- `decision_record`

If required frozen Teacher evidence is unavailable and external generation is not authorized: `EXTERNAL_ACTION_REQUIRED`.

### Day 6 — Temporal-state design
Normal engineering:
- `schema_contract`
- `source_check`
- `provenance_test`
- `deterministic_tests`
- `architecture_check`

Action: `D6_TEMPORAL_STATE_DESIGN`
Execution: `ENGINEERING_WORKTREE`

### Day 7 — Temporal-case validation
Normal engineering/test work:
- `deterministic_tests`
- `validation_report`

Action: `D7_TEMPORAL_CASE_VALIDATION`

### Day 8 — Novelty Scout proof of concept
Research:
- `novelty_artifact`
- `provenance_artifact`

Guard evidence:
- `source_check`
- `deterministic_tests`
- `nonmutation_test`

Action: `D8_NOVELTY_SCOUT`
Execution: `RESEARCH_RUN`

### Day 9 — Explanation and trade-off stage
Normal engineering:
- `source_check`
- `deterministic_tests`
- `nonmutation_test`
- `schema_contract`

Action: `D9_EXPLANATION_STAGE`
Execution: `ENGINEERING_WORKTREE`

### Day 10 — End-to-end performance
Research:
- `performance_artifact`
- `condition_record`
- `limitation_record`

Action: `D10_PERFORMANCE_RUN`
Execution: `RESEARCH_RUN`

### Day 11 — Product configuration
Prerequisite/retained:
- `hardware_evidence`

Decision/documentation:
- `deployment_matrix`
- `advisory_record`

Action: `D11_PRODUCT_CONFIGURATION`
Execution: `DECISION_OR_DOCUMENTATION_WORKTREE`

### Day 12 — Reproducibility and operations
Normal documentation/engineering:
- `operator_docs`
- `recovery_check`
- `gitignore_check`

Action: `D12_REPRODUCIBILITY_OPERATIONS`
Execution: `DECISION_OR_DOCUMENTATION_WORKTREE`

### Day 13 — Full regression and fresh holdout
Deterministic:
- `full_test_result`

Research setup:
- `holdout_manifest`
- `architecture_ref`

Research:
- `result_artifact`
- `retained_failures`

Decision/classification:
- `classification_record`
- `status_summary`

Actions:
- `D13_FULL_REGRESSION`
- `D13_NEW_HOLDOUT`
- `D13_CLASSIFY_RESULT`

### Day 14 — Sprint review
Decision/documentation:
- `sprint_review`

Human-only:
- `human_review_marker`

Control Center must never manufacture the human review marker.

Expected flow:

```text
sprint_review produced
 -> HUMAN_ACTION_REQUIRED
 -> human review completed
 -> Resume
 -> human_review_marker validated
 -> COMPLETE
```

A selected Day must not auto-run prerequisite Days. If a prerequisite is genuinely absent, route to the appropriate authority state.

## 13. Day 1 non-destructive baseline checkpoint

`commit_ref` missing is normal Day work, not a repair failure.

The baseline checkpoint must not mutate the user's current branch, current index, or worktree.

Preferred pattern:

```text
temporary Git index
 -> read-tree
 -> add only policy-approved tracked/untracked source to temp index
 -> write-tree
 -> commit-tree
 -> dedicated checkpoint ref
```

Possible ref:

```text
refs/heads/ai-control-center/day1-baseline-<id>
```

Requirements:
- no `git reset`;
- no `git clean`;
- no current-branch commit;
- no force-push;
- no `main` push;
- no generated results/models/datasets/artifacts staged;
- no untracked user work deleted;
- deterministic verification that checkpoint tree matches intended baseline;
- remote push is not required merely to satisfy `commit_ref`.

If approved source cannot be identified safely, route to authority rather than guess.

## 14. Research Run guard

`RESEARCH_RUN` is separate from engineering repair.

Research Run:
- uses the authoritative Day/runbook condition;
- writes only approved generated result/artifact/log locations;
- does not silently modify tracked source/config/schema/tests;
- records model/config/input fingerprints;
- preserves failed/model-quality results;
- does not rerun unchanged failed inference merely to obtain a better result;
- does not enter Repair Supervisor because the model answer is poor;
- does not save hidden reasoning/raw chain-of-thought.

Poor model output is `MODEL_QUALITY_FINDING`, not `ENGINEERING_REPAIR`.

## 15. Engineering Repair Supervisor

Only `ENGINEERING_REPAIR` enters Repair Supervisor.

Required flow:

```text
Verified Solution Catalog
 -> LocalLLM proposal up to 3
 -> local phase <= 300 seconds
 -> deterministic prefilter
 -> guarded Codex Builder/Reviewer
 -> if no verified success:
      automatic Codex Expert Solver
 -> deterministic verification
 -> re-evidence
 -> verified catalog update
 -> later compatible LocalLLM proposals receive catalog guidance
```

LocalLLM never edits files. Codex never expands authority. Rejected proposals never enter the Solution Catalog.

## 16. Repair & Go

`Repair & Go` is not the normal repair mechanism.

Normal engineering repair is automatic inside the original Go execution.

`Repair & Go` is enabled only when all are true:
- a persisted Repair Episode exists;
- automatic repair was interrupted;
- contract/scope/fingerprint remain compatible;
- episode/deadline policy allows resume.

It is disabled for ordinary evidence gaps, normal Day work, model-quality findings, generic failures, complete states, and authority states.

## 17. Semantic no-op and cycle detection

A semantic action fingerprint includes at least:

```text
project
contract_version
day
criterion_id
evidence_type
action_template_id
relevant source-state fingerprint
relevant configuration fingerprint
bounded action input
```

Do not include volatile values such as timestamps, UUIDs, temporary paths, or log ordering unless they materially define action semantics.

An identical action against identical semantic state is forbidden. Repeated observation is not a replan. Global `MAX_REPLANS` must not be used as a Day terminal condition.

## 18. Controller algorithm

```python
while active:
    preflight_if_needed()

    inventory()

    collect_reusable_and_read_only_evidence()

    validate_all_criteria()

    if all_criteria_valid:
        complete()
        return

    gaps = diagnose_each_missing_evidence_requirement()

    actions = select_server_owned_actions(gaps)

    if genuine_human_blocker:
        human_action_required()
        return

    if genuine_external_blocker:
        external_action_required()
        return

    if no_safe_nonrepeating_action:
        failed_unrecoverable()
        return

    action = deterministic_next_action(actions)

    execute(action)

    recollect_affected_evidence()

    revalidate()
```

Codex does not own this loop.

## 19. Action priority

When multiple gaps exist, prefer:

1. compatible retained evidence reuse;
2. read-only collection;
3. normal selected-Day work;
4. repository/configuration corrective work;
5. engineering repair;
6. authority gate.

When one Action Template can validly produce multiple missing evidence records, execute it once and adapt/validate each resulting evidence type.

## 20. Persistence and restart

Persist at minimum:
- selected Day;
- contract/version;
- current state/phase;
- criteria;
- Evidence Store;
- GapDiagnoses;
- active/last action;
- semantic fingerprints;
- cache metadata;
- Git/protected-path audits;
- reports;
- blockers;
- Repair Episode references;
- Solution Catalog references.

On restart:
- active state becomes `PAUSED`;
- persisted success is revalidated;
- repair deadline remains absolute and is not reset;
- in-flight work is not repeated unless semantic evidence proves it did not execute.

## 21. Authority-state Resume

`HUMAN_ACTION_REQUIRED` and `EXTERNAL_ACTION_REQUIRED` preserve the Day.

After the prerequisite is resolved:

```text
Resume
 -> PREFLIGHT
 -> revalidate blocker
 -> revalidate contract/version
 -> continue same Day
```

A second Go must not silently discard the old Day state.

## 22. API contract

Required endpoints:
- `GET /api/local-llm/days`
- `GET /api/local-llm/day/status`
- `POST /api/local-llm/day/{day}/smoke`
- `POST /api/local-llm/day/{day}/start`
- `POST /api/local-llm/day/resume`
- `POST /api/local-llm/day/repair-and-go`
- `POST /api/local-llm/day/stop`

Snapshot must include:
- state;
- phase;
- Day;
- contract version;
- criterion evidence;
- GapDiagnoses;
- active/last action;
- report;
- blocker;
- semantic fingerprints/cache metadata needed for audit;
- server-derived Recommended Action;
- server-derived enabled controls.

Refusals are typed. No silent reset.

## 23. UI contract

The UI projects backend policy. It does not calculate policy.

### Button matrix

| State | Go | Resume | Repair & Go | Stop |
| --- | ---: | ---: | ---: | ---: |
| `IDLE` | ON | OFF | OFF | OFF |
| active states | OFF | OFF | OFF | ON |
| generic `PAUSED` | OFF | ON | OFF | OFF |
| paused interrupted repair | OFF | OFF | ON | OFF |
| `STOPPED` | OFF | ON | OFF | OFF |
| `HUMAN_ACTION_REQUIRED` | OFF | ON after resolution | OFF | OFF |
| `EXTERNAL_ACTION_REQUIRED` | OFF | ON after resolution | OFF | OFF |
| `COMPLETE` | OFF | OFF | OFF | OFF |
| `FAILED_UNRECOVERABLE` | OFF | OFF | OFF | OFF |

### Recommended Action

```text
IDLE                  -> GO
active                -> WAIT
PAUSED                -> RESUME
STOPPED               -> RESUME
interrupted repair    -> REPAIR_AND_GO
authority blocker     -> SHOW_REQUIRED_ACTION
COMPLETE              -> SELECT_NEXT_DAY
FAILED_UNRECOVERABLE  -> SHOW_FAILURE
```

Enabled UI controls must match executable backend transitions exactly.

## 24. Smoke semantics

Smoke is preflight diagnostics only.

`SMOKE_PASS` is not `SUCCESS`, `COMPLETE`, or `DAY_COMPLETE`.

Smoke cannot satisfy Day criteria and cannot enable next-Day selection.

## 25. Legitimate FAILED_UNRECOVERABLE boundary

Allowed examples:
- invalid/missing trusted contract;
- Evidence Registry corruption/incompleteness;
- persistence/state-machine corruption;
- scope/Git invariant failure;
- protected-artifact safety violation;
- unclassifiable controller safety invariant;
- every safe action is proven semantic no-op and no human/external authority route exists.

Not allowed:
- evidence is missing;
- planner tried twice;
- planner repeated itself;
- test is not yet created;
- research artifact is not yet produced;
- ordinary Day work remains.

## 26. Codex/Work authority

Codex/Work is the Builder.

Allowed:
- read declared context;
- implement inside server-authorized scope;
- run deterministic tests;
- report failures;
- act as bounded Builder/Reviewer/Expert Solver when invoked by runtime.

Forbidden:
- change criteria;
- add/change evidence types;
- change gap classification;
- change Action Templates;
- change authority class;
- change research conditions;
- expand scope;
- alter this canonical specification to fit existing code;
- declare final architectural conformance;
- declare final PASS.

## 27. Required conformance tests

Final acceptance requires all of the following.

### 27.1 Registry completeness
- validator coverage: 46/46 configured evidence types;
- acquisition strategy coverage: every `(day, evidence_type)` pair;
- generic fallback: 0;
- unknown evidence: fail closed.

### 27.2 State-machine coverage
Test every legal transition, forbidden transitions, restart, stop/resume, authority resume, and strict `FAILED_UNRECOVERABLE` behavior.

### 27.3 Per-evidence diagnosis
Create a criterion with two evidence types, A already valid and B missing. Prove only B receives diagnosis/action, A is not unnecessarily recollected, and completion occurs only after B is produced and validated.

### 27.4 Day 1 one-Go production E2E
Disposable Git project through the real production controller/engine/API:

```text
Smoke
 -> Go once
 -> test_result valid
 -> commit_ref missing
 -> diagnose commit_ref only
 -> BASELINE_CHECKPOINT
 -> recollect
 -> validate
 -> COMPLETE
```

Prove no second Go, no Repair & Go, no `main` mutation, no user worktree/index mutation, no generated artifact staging, and no reset/clean.

### 27.5 Normal Research Run E2E
Disposable/fake deterministic model boundary through real orchestration:

```text
missing research artifact
 -> PRODUCE_DAY_EVIDENCE
 -> RESEARCH_RUN
 -> preserved artifact
 -> registry validation
```

Also prove a poor model-quality result is preserved and never enters Repair Supervisor. Do not use actual LocalLLM-Lab research for this Control Center conformance test.

### 27.6 Repair Supervisor E2E
Real controller/engine path:

```text
normal Day work
 -> genuine implementation defect
 -> automatic Repair Supervisor
 -> <=3 LocalLLM proposals
 -> automatic Expert Solver if required
 -> deterministic verification
 -> re-evidence
 -> completion
```

Then prove the next compatible episode receives verified Solution Catalog guidance.

### 27.7 Authority E2E
External prerequisite:

```text
Go
 -> EXTERNAL_ACTION_REQUIRED
 -> resolve fixture prerequisite
 -> Resume
 -> same Day continues
```

Human decision:

```text
Go
 -> HUMAN_ACTION_REQUIRED
 -> record authorized fixture decision
 -> Resume
 -> same Day continues
```

### 27.8 Semantic no-op
Prove an identical semantic action against unchanged state is not repeated. Do not translate ordinary missing evidence into failure merely because a planner repeats itself.

### 27.9 Running-browser UI E2E
Start the actual local server and use real browser automation, not static source-string inspection.

Verify:
- Smoke visibly shows `SMOKE_PASS`, not Day completion;
- one Go starts autonomous continuation;
- phase changes are visible;
- Repair & Go remains disabled for normal evidence gaps;
- no second Go is required;
- qualifying interrupted repair enables Repair & Go;
- Resume works for paused/stopped/authority cases as specified;
- Complete enables next-Day selection;
- Recommended Action matches backend executable state.

Capture browser evidence such as screenshots or browser-test artifacts/logs. If real browser automation cannot run, UI conformance is BLOCKED, not PASS.

### 27.10 Full regression
- collected tests > 0;
- all collected deterministic tests pass;
- `git diff --check` passes.

## 28. Final acceptance

Codex/Work may report only:

```text
READY_FOR_EXTERNAL_REVIEW
```

or:

```text
BLOCKED
```

It must not declare final `PASS`, `ARCHITECTURE_CONFORMANCE: PASS`, or final acceptance.

The external checker independently inspects this specification, production call paths, tests, API behavior, Git state, and actual rendered UI/browser evidence.

A Codex self-report is never sufficient evidence of conformance.
