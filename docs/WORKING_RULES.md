# Working Rules

## Canonical status

This file is the single canonical permanent operating policy for AI Control Center
engineering, autonomous Day execution, LocalLLM experiments, and ChatGPT reviewer
interaction. Runtime code still enforces hard safety boundaries, but operating
judgment must follow this document.

Do not use a cached copy. Codex must read the current branch version at the start
of every run and again whenever a reviewer-facing report says the policy changed.

## Precedence

1. Explicit current human instruction
2. This document (`docs/WORKING_RULES.md`)
3. `docs/CURRENT_WORK.md` (active objective, DoD, stop condition)
4. Current authoritative scenario/runbook or Day contract
5. `docs/ARCHITECTURE.md`
6. Historical/reference documents

A lower-precedence source never overrides a higher one. Historical zero-touch,
autonomous-Day, roadmap, or runbook text is descriptive/reference material when it
conflicts with this policy.

## Current interaction mode

The current LocalLLM Day workflow is reviewer-supervised. The zero-touch documents
remain an architectural target, but they do not bypass the reviewer gates defined
here. In particular, `DECISION_REQUEST` and `COMPLETION_REPORT` require reviewer
delivery and reviewer response before execution may cross the blocking boundary.

## Mandatory context load

Before planning, executing, repairing, or resuming a run, Codex must read in order:

1. the complete latest human/reviewer message, not only its first line;
2. this file from the current branch;
3. relevant execution/engineering history;
4. persisted state;
5. the active Day contract/runbook;
6. the immediately preceding `NEXT_ACTION`.

If a reviewer message contains multiple instructions, Codex must parse the entire
message before acting. When the message asks for an `INSTRUCTION_DIGEST`, Codex
must produce that digest before any code execution, test, commit, push, Day Runner
action, or LocalLLM invocation.

## Core execution rules

- **WR-01 Objective and DoD first.** Every material action must map to an unmet
  DoD item and produce an artifact, test, evidence item, diagnosis, or proof.
- **WR-02 Progress over polish.** Prefer a small safe solution and working evidence
  over redesign, exhaustive coverage, or cosmetic perfection.
- **WR-03 Deterministic first.** Use Python/tests/config validation when they can
  decide reliably; keep model judgment bounded and separately auditable.
- **WR-04 Authority does not expand silently.** Codex may inspect, implement, test,
  diagnose, and replan inside approved scope, but may not silently expand source
  scope, write authority, credentials, budgets, cloud use, destructive Git authority,
  acceptance criteria, or business/product scope.
- **WR-05 Classify failures before acting.** Distinguish harness/implementation
  defects, contract/test defects, experiment-condition issues, model-quality
  findings, insufficient evidence, and genuine external/human authority needs.
- **WR-06 LocalLLM roles stay distinct.** As a research subject, poor output is
  evidence and must not be tuned/rerun away unless the contract explicitly permits
  it. As an engineering assistant, LocalLLM may propose only; Codex/deterministic
  checks verify. LocalLLM never owns completion.
- **WR-07 Protect scope, data, evidence, and Git.** Never hard-reset/clean user work,
  force-push, modify or merge `main`, delete evidence to obtain a pass, fabricate
  provenance, weaken tests, or commit secrets without explicit authority.
- **WR-08 Repair/replan is bounded.** Retry only for a transient cause, confirmed
  repair, or materially changed safe condition. Never blindly repeat an unchanged
  failure.
- **WR-09 Human interruption is exceptional.** Do not stop for naming, comments,
  nice-to-have tests, minor edge cases, known warnings, speculative future cases,
  unrelated refactors, or exhaustive coverage.
- **WR-10 Completion is evidence-based.** A finished action is not a completed Day.
  Never weaken criteria or manufacture evidence to make completion appear true.
- **WR-11 Critical boundaries belong in code.** Scope, state, Git, budget, retry,
  command, and evidence boundaries must remain deterministic and auditable.
- **WR-12 History-aware changes.** Review relevant history before engineering
  changes; preserve prior failed approaches/user corrections until explicitly
  superseded; append history after verified changes.
- **WR-13 Stop after current DoD.** Do not start the next Day, phase, scenario, or
  optimization until the required completion-review boundary is cleared.
- **WR-14 Classify the next action before doing it.** Every material next action
  must be classified as exactly one of `IMPLEMENTATION`, `VALIDATION`,
  `DIAGNOSIS`, or `AUTHORITY`. Do not turn validation into more implementation,
  diagnosis into redesign, or a reviewer checkpoint into a new project without
  evidence that the broader action is required.

## Default run window and active-work clock

Unless the human specifies otherwise, an autonomous work window is **30 minutes of
ACTIVE_WORK**, not 30 minutes of wall-clock time.

`ACTIVE_WORK` counts time spent implementing, validating, diagnosing, testing,
analyzing, or producing the current bounded artifact/evidence. It does **not** count:

- reviewer-report delivery wait;
- reviewer processing wait;
- reviewer-response fetch wait;
- genuine human-authority wait.

Normal `PROGRESS_UPDATE` cadence is **10 minutes of ACTIVE_WORK** after the latest
matching reviewer response was applied.

- At 10 active minutes, report at the next safe work boundary.
- If the current bounded subtask is expected to finish shortly, the report may be
  deferred by up to 3 additional active minutes.
- Do not exceed **15 minutes of ACTIVE_WORK** without a progress report.
- Reset the 10-minute progress counter to zero when the matching reviewer response is
  fully read and applied.
- At about 25 active minutes in a 30-active-minute window, do not start a new large
  investigation/redesign; finish the current bounded evidence-producing action and
  move toward a safe checkpoint.

A `DECISION_REQUEST` or `COMPLETION_REPORT` is event-driven and is delivered
immediately when its condition occurs; it never waits for the 10-minute progress timer.

### Two-minute response/transport cadence

A deterministic local transport/fetch loop may run about every **2 minutes**. Its job
is to:

- deliver a pending report to the operational reviewer bus when one exists;
- fetch a matching reviewer response for the single outstanding `REPORT_ID`;
- apply that response and resume the approved plan.

The 2-minute cadence is **not** a progress-report cadence. Do not emit a report every
2 minutes.

## Reviewer report types

Exactly three control report types are used. Every report must also state
`ACTION_CLASS: IMPLEMENTATION|VALIDATION|DIAGNOSIS|AUTHORITY`.

### `PROGRESS_UPDATE` — reviewer steering checkpoint

Use for routine progress, validation, commits/pushes, evidence creation, model activity,
remaining gaps, and scope-control checkpoints.

Its purpose is to detect over-investigation early and keep execution tied to the current
DoD, not to restart planning.

- Normally due after 10 minutes of ACTIVE_WORK, subject to the safe-boundary rules above.
- After successful publication to the operational reviewer bus, pause at the safe
  checkpoint and wait for the matching reviewer response.
- If publication itself fails, do not stop ordinary already-authorized work solely
  because transport failed; record the failure and retry on the next 2-minute
  transport cycle.
- After a matching response is applied, reset the progress counter and continue the
  approved plan.
- A progress checkpoint must not become a new project. Prefer `CONTINUE` or a
  narrower next action unless evidence shows a different action class is required.

### `DECISION_REQUEST` — blocking

Use only when a genuine decision/authority boundary is reached, such as new source or
write scope, destructive operation, reset/reselect, `main` authorization, new
business/product direction, credentials, security/compliance judgment, unknown fatal
recovery, or repair scope beyond existing authority.

Publish immediately, stop at a safe checkpoint, and do not cross the decision boundary
until a matching reviewer response is fully read and applied.

### `COMPLETION_REPORT` — blocking

A Day or major task completion is never an ordinary progress update.

After the declared DoD is satisfied and `ARTIFACT_QUALITY_CHECK: PASS`, publish the
completion report immediately and stop the current Day/task. Do not start the next
Day/task until the matching reviewer response accepts completion and authorizes the
next boundary.

Do not ask the human for separate permission merely to send any report.

## Operational reviewer bus

The normal machine-to-machine reviewer path is the validated GitHub event-driven bus:

- repository: `HIPVG/AI-Control-Center-Review-Bridge`
- operational PR: **#1**
- event Task trigger: new top-level PR conversation comment containing `REPORT_TYPE:`
- event Task instruction file: `poc/reviewer-task-prompt.md` on the PR head branch
  (the legacy path is intentionally retained because the working Task is already
  configured to read it).

The PoC on 2026-09-24 validated all three report types, matching
`REPORT_ID`/`IN_REPLY_TO`, blocking behavior, completion acceptance, and zero
manual relay after start.

### Report publication

For every reviewer-facing report:

1. create a unique stable `REPORT_ID`;
2. ensure no other reviewer report is outstanding;
3. publish one top-level comment to operational PR #1 containing `REPORT_TYPE:`;
4. record the comment/report identifier and publication time;
5. after successful publication, end the current Codex turn at the safe checkpoint; do not poll the PR from inside Codex;
6. the deterministic Control Center reviewer-bus watcher owns response polling and resumes the most recent Codex exec session when the matching response arrives.

The operational path does **not** use the ChatGPT composer. Do not automate the
composer, inspect drafts/placeholders, or attempt direct browser message injection as
part of normal reviewer transport.

A past composer/draft failure is historical evidence, not a fallback design.

### Correlation and deduplication

Only one reviewer report may be outstanding at a time.

Every reviewer response must contain:

- `IN_REPLY_TO: <REPORT_ID>`
- `RESULT: CONTINUE|DECISION|ACCEPT_COMPLETE|REJECT|HUMAN_REQUIRED`
- `NEXT_ACTION: <minimum-sufficient action>`

Codex must:

- ignore stale/mismatched responses;
- never apply a response whose `IN_REPLY_TO` differs from the outstanding
  `REPORT_ID`;
- read the complete matching response before acting;
- treat a duplicate response/report as a protocol error and apply only the first valid
  matching response.

### Reviewer response acquisition

After a report is successfully published to operational PR #1:

1. Codex ends its current turn at the appropriate safe checkpoint;
2. the Control Center reviewer-bus watcher polls the PR conversation about every 2 minutes;
3. the watcher finds the first new response whose `IN_REPLY_TO` exactly matches the outstanding `REPORT_ID`;
4. the watcher starts a **fresh bounded Codex continuation turn** in the AI-Control-Center working directory with the complete matching response; it does not use `resume --last` or depend on a desktop/CLI session database;
5. the continuation turn reconstructs authoritative context from `AGENTS.md`, `docs/WORKING_RULES.md`, `docs/CURRENT_WORK.md`, relevant engineering history, persisted state, and the active plan/runbook before acting;
6. the continuation turn applies `RESULT`, `DECISION` when present, and the full `NEXT_ACTION`, clears the outstanding report, and continues according to report type.

The watcher must use the Control Center's isolated `CODEX_SQLITE_HOME` under managed project state rather than the desktop Codex state database.

The 2026-09-24 PoC measured reviewer-response creation latencies of 36s, 35s, and 47s
for progress, decision, and completion respectively. Production still uses the simpler
2-minute fetch cadence unless later measurements justify changing it.

If no matching response is observed within 10 wall-clock minutes after successful
publication, record `REVIEWER_RESPONSE_TIMEOUT` and keep the safe checkpoint. Do not
silently switch to composer automation or fabricate a reviewer decision; surface the
transport failure for human attention.

### Human involvement

Human interruption is exceptional.

The event-driven reviewer should resolve ordinary progress steering, evidence/validation
decisions, and completion acceptance itself. Use `RESULT: HUMAN_REQUIRED` only for a
genuine human authority/product-direction boundary defined above.

A human must not be used as a routine copy/paste relay between Codex and the reviewer.

## Latest reviewer response and no duplicate approvals

Subject to precedence rules, the latest **matching** reviewer response supersedes earlier
reviewer instructions and the agent's old `NEXT_ACTION`.

Do not request the same approval again when scope and conditions are unchanged. Re-check
the matching reviewer response and history before escalating.

## Artifact quality gate before completion

Before declaring a Day or major task complete, perform
`ARTIFACT_QUALITY_CHECK: PASS|FAIL`.

Minimum checks:

1. expected artifacts exist;
2. version/ref/commit/hash/provenance are traceable;
3. comparison inputs, Fact Layer, fixed conditions, and run identity are compatible;
4. report values are derived from the actual artifacts;
5. failed/truncated/model-quality results are not hidden;
6. downstream work can consume the artifacts without ambiguous reinterpretation;
7. the business conclusion is traceable to evidence.

`FAIL` blocks completion until the downstream-relevant inconsistency is repaired or
escalated. Naming, comments, formatting, cosmetic issues, nice-to-have tests, and
unrelated refactoring are not quality-gate failures.

## Evidence and provenance

- Prefer reuse of already-valid evidence over rerun.
- Historical artifacts may be registered only when provenance and condition
  compatibility are actually validated; never invent a record to satisfy a gate.
- If fixed-condition comparability cannot be proven, do not claim a comparison.
- Keep superseded contracts/results traceable rather than deleting history.
- Preserve model-quality failures as findings; do not normalize them away.

## Git and branch policy

- Work on the approved agent branch.
- `main` is read-only unless the human explicitly authorizes a change/merge.
- No force-push, hard reset, destructive clean, or evidence deletion.
- Commit/push bounded reviewed changes when authorized by the active workflow.
- Keep unrelated user changes out of commits whenever practicable.

## Reviewer policy context in every report

Every `PROGRESS_UPDATE`, `DECISION_REQUEST`, and `COMPLETION_REPORT` must include a
compact `REVIEW_POLICY_CONTEXT` block with:

- `CANONICAL_POLICY_REPO: HIPVG/AI-Control-Center`
- `CANONICAL_POLICY_BRANCH: agent/autonomous-multitask-orchestration`
- `CANONICAL_POLICY_PATH: docs/WORKING_RULES.md`
- `POLICY_COMMIT: <commit containing the policy version read>`
- `POLICY_READ_BY_CODEX: yes|no`
- `POLICY_CHANGED_SINCE_LAST_REVIEW: yes|no`
- `POLICY_CHANGE_SUMMARY: <material changes when yes>`
- `APPLICABLE_RULES: <short action-oriented digest>`
- `LATEST_REVIEWER_RESPONSE_READ: yes|no`
- `REVIEWER_INSTRUCTION_APPLIED: <latest instruction applied>`
- `POLICY_DEVIATION: none|<explicit deviation and authority>`

When `POLICY_CHANGED_SINCE_LAST_REVIEW: yes`, the ChatGPT reviewer should re-read
the canonical policy before issuing a new decision.

## Simple reviewer-report rule

Reviewer-facing reports are control packets, not essays. Keep them as short as possible
while preserving the information needed to steer the next action.

For `PROGRESS_UPDATE` in particular:

- report only what changed since the previous reviewer checkpoint;
- do not repeat unchanged background, prior findings, or the full Day contract;
- do not duplicate the same report body;
- use one short line per field where practical;
- prefer artifact/file references over pasting long evidence;
- target roughly 8-12 short lines unless a real blocker needs more context.

A normal progress report should usually answer only:

- what changed;
- what is being done now;
- whether there is a blocker;
- the minimum sufficient next action.

If policy context is unchanged, use one compact line instead of a repeated multi-line
block, for example:

`REVIEW_POLICY_CONTEXT: commit=<sha>; read=yes; changed=no; deviation=none`

Only expand policy context when the policy actually changed or a deviation must be
explained.

`DECISION_REQUEST` and `COMPLETION_REPORT` may be longer when the reviewer genuinely
needs evidence to decide, but they must still avoid repetition and unrelated detail.

Every reviewer-facing report must include:

- `SIMPLE_REPORT: yes`

If the same report is accidentally emitted twice, treat the duplicate as a reporting
error and do not send both copies.

## Minimum sufficient action principle

For every task and every reviewer-facing report, choose the smallest safe action
that is sufficient to achieve the immediate objective. Do not broaden the action
merely because a broader operation is available.

Examples:

- if only operating rules changed, sync/read only the operating-rule file(s);
- if one file needs inspection, inspect that file rather than the whole repository;
- if a local defect is isolated, repair only that defect;
- do not pull/update the whole branch, rerun unrelated tests, refactor, or expand
  scope unless the immediate objective actually requires it.

Before executing a reported `NEXT_ACTION`, Codex must ask internally: "What is the
smallest sufficient action?" If a narrower action safely achieves the same goal,
use the narrower action.

Every reviewer-facing report must include:

- `MINIMUM_SUFFICIENT_ACTION: <the smallest next action>`
- `WHY_NOT_BROADER: <why broader actions are unnecessary now>`

These fields are operational instructions, not commentary: the subsequent action
must follow them unless the reviewer explicitly authorizes a broader action.

## Reviewer instruction against overreach

Every reviewer-facing report must explicitly instruct the ChatGPT reviewer to keep the
next instruction result-oriented and minimum-sufficient.

Include this exact control field in every report:

`REVIEWER_GUIDANCE: Eliminate unnecessary overreach. Give only the minimum-sufficient, result-oriented instruction needed for the current objective. Do not recommend broader work merely because it is possible, cleaner, more general, more future-proof, or theoretically better. No speculative redesign, broad refactor, full-repository operation, extra validation, extra research, or higher-level optimization unless it is required to achieve the current DoD or remove the current blocker.`

The reviewer should prefer:
- the smallest action that directly advances the current DoD;
- evidence/result production over framework improvement;
- local fixes over generalized redesign;
- existing valid evidence over rerun;
- stopping once the current objective is satisfied.

A broader instruction is allowed only when the narrower action cannot safely achieve the
current objective; the reviewer must state why the narrow action is insufficient.

## Required report metadata

Every reviewer-facing report must include at least:

- `REPORT_ID`
- `REPORT_TYPE`
- `ACTION_CLASS: IMPLEMENTATION|VALIDATION|DIAGNOSIS|AUTHORITY`
- `ACTIVE_WORK_MINUTES` (or equivalent active-work duration)
- `CURRENT_DAY` or task identity
- `STATE / PHASE`
- `CURRENT_ACTION` or completion state
- `EVIDENCE` / `VALIDATION` as applicable
- `LOCAL_LLM_INVOCATIONS`
- `BLOCKER` or `REMAINING_GAPS`
- `NEXT_ACTION` / `NEXT_ACTION_AFTER_REVIEW`
- `REVIEWER_DELIVERY_CHANNEL: github_event_pr|none`
- `REVIEWER_DELIVERY_STATUS: delivered|pending|failed`
- `MINIMUM_SUFFICIENT_ACTION: <the smallest next action>`
- `WHY_NOT_BROADER: <why broader actions are unnecessary now>`
- `SIMPLE_REPORT: yes`
- `REVIEWER_GUIDANCE: <mandatory anti-overreach instruction to the reviewer>`
- a compact `REVIEW_POLICY_CONTEXT` line when unchanged; expand it only when changed or deviating

`COMPLETION_REPORT` additionally requires:

- completed Day/task
- criteria satisfied
- artifact-quality result
- research runs
- commits and remote match
- `MAIN_UNCHANGED`
- reset/reselect status
- history updated status
- next Day (if any), which must not start before reviewer clearance

## Engineering history

At the end of every work window, append history recording:

- policy/reviewer response read;
- instruction applied;
- changes from prior `NEXT_ACTION`;
- new authorization/restriction;
- actions actually run;
- validation/evidence;
- reporting/delivery failures;
- blocker and next action;
- whether unnecessary detail work delayed progress.

A reporting protocol failure, including falsely or unverifiably claiming a composer
draft as the reason for skipped delivery, must be recorded explicitly.

## Supersession and ambiguity rule

This file supersedes conflicting operational language in historical documents. In
particular:

- zero-touch goals do not make ChatGPT review optional at the blocking boundaries
  defined here;
- user-facing Codex display alone does not satisfy reviewer delivery;
- publication to operational PR #1 is successful reviewer-bus delivery because the
  validated GitHub event Task is the active reviewer trigger;
- normal reviewer transport does not use the ChatGPT composer;
- successfully published progress reports pause execution until a matching reviewer
  response; publication failures do not revoke existing ordinary work authority;
- waiting/reviewer latency is excluded from ACTIVE_WORK;
- completion always requires artifact-quality checking and matching reviewer clearance
  before the next Day.

When ambiguity remains, stop only if the ambiguity materially changes authority,
scope, safety, evidence validity, or business/product direction. Otherwise choose the
smallest safe interpretation that preserves forward progress.
