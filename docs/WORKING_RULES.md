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

## Default run window and periodic reporting

Unless the human specifies otherwise, an autonomous work window is 30 minutes.

- Emit a reviewer-facing `PROGRESS_UPDATE` about every 5 minutes during active work,
  even if no major event occurred.
- `PROGRESS_UPDATE` is non-blocking: report and continue within existing authority.
- At about 25 minutes, avoid starting a new large investigation or redesign; prefer
  evidence preservation, commit/push when appropriate, history update, and a safe
  checkpoint.
- Internal DoD reassessment may happen more often; periodic reporting is not a
  substitute for real execution.

## Reviewer report types

Exactly three control report types are used:

### `PROGRESS_UPDATE` — non-blocking

Use for routine state transitions, validation, commit/push, LocalLLM activity,
evidence creation, remaining gaps, and ordinary checkpoints. Reporting does not
consume or revoke an existing Day-start authorization. After delivery attempts,
continue when the next action remains within existing authority.

### `DECISION_REQUEST` — blocking

Use only when a new decision/authority is genuinely needed, such as new source or
write scope, destructive state operation, reset/restart/reselect, `main` change, new
business/product direction, unknown fatal recovery, security/compliance decision,
new installation/cloud use, or repair scope beyond authorization. Stop at a safe
checkpoint after delivering the report and wait for the reviewer response.

### `COMPLETION_REPORT` — blocking

A Day or major task completion is never an ordinary progress update. After the
artifact-quality gate passes and completion criteria are satisfied, deliver a
`COMPLETION_REPORT`, stop, and wait for reviewer response before starting the next
Day/major task.

Do not ask the human for separate permission merely to send any report.

## Reviewer report destination and delivery

All reviewer-facing reports are intended for the ChatGPT reviewer. They must also be
shown in full in the current user-facing Codex output so the human can inspect or
relay them, but user-facing display alone is **not** successful delivery for a
blocking report.

Canonical delivery channels:

1. direct ChatGPT reviewer delivery when available and safe;
2. fallback transport repository `HIPVG/AI-Control-Center-Review-Bridge` when direct
   delivery is unavailable or unsafe.

For `PROGRESS_UPDATE`, delivery is best-effort and non-blocking. If both channels
fail, display the full report, record the failure/pending status, and continue within
existing authority.

For `DECISION_REQUEST` and `COMPLETION_REPORT`, successful direct delivery or
successful Review-Bridge publication is required before the report is considered
delivered.

### Blocking-report retry rule

If both direct ChatGPT delivery and Review-Bridge delivery fail:

1. record both failure results;
2. wait 2 minutes;
3. retry direct delivery, then Review-Bridge;
4. if both still fail, wait another 2 minutes;
5. retry direct delivery, then Review-Bridge a third and final time.

This is 3 total delivery attempts (initial + 2 retries). Do not stop after only one
failed attempt.

After all 3 attempts fail, output the full report and:

- `DELIVERY_FAILED: yes`
- `DELIVERY_ATTEMPTS: 3`
- `DIRECT_DELIVERY_RESULTS: <all attempts>`
- `REVIEW_BRIDGE_RESULTS: <all attempts>`
- `LAST_ERROR: <exact bounded error>`

Then stop at the safe checkpoint because the blocking report could not be delivered.

## Composer draft handling

An unsent ChatGPT composer draft must never be overwritten, deleted, or edited.
However, composer state is not itself an execution-control signal and must never be
used as an excuse to omit reviewer delivery.

### Draft detection must inspect the actual editable buffer

Codex may claim `COMPOSER_DRAFT_DETECTED: yes` only when the actual user-editable
composer buffer contains non-whitespace user text.

Acceptable evidence is a direct read of the editable value itself, for example the
actual `.value` of an input/textarea or the actual text/content model of a
`contenteditable` editor. The observation must distinguish real editable content
from presentation metadata.

The following are **not evidence of a draft** and must never be used to infer one:

- placeholder text, including text rendered inside or over the composer;
- `placeholder`, `data-placeholder`, `aria-label`, accessible name, title, or
  similar attributes;
- ghost text, suggestions, example prompts, follow-up labels, or quick-reply UI;
- nearby status text or buttons such as generation/progress indicators;
- the mere presence of a composer element;
- the fact that ChatGPT is currently generating a response.

A visible string such as `フォローアップ` is not a draft unless it is verified to
exist in the actual editable buffer.

When reporting a verified draft, include:

- `COMPOSER_DRAFT_DETECTED: yes`
- `DETECTION_METHOD: <exact editable-buffer observation>`
- `DETECTED_DRAFT_LENGTH: <character count after trimming>`
- `DETECTION_TIMESTAMP: <timestamp>`

Do not include or expose the draft text itself unless the human explicitly requests
it.

If Codex cannot distinguish real editable content from placeholder/UI state, record
`COMPOSER_DRAFT_DETECTED: unknown`, never `yes`. `unknown` is not permission to
skip reviewer delivery.

A verified non-empty draft may cause direct delivery to be skipped only to avoid
overwriting that buffer; Review-Bridge delivery must still be attempted immediately.
A placeholder, UI label, or unverified state never justifies skipping direct delivery.

Any false-positive claim that a placeholder/UI label was a draft is a
`REPORTING_PROTOCOL_FAILURE` and must be recorded in engineering history.

`REVIEWER_POST_PENDING: yes` is informational only. It never satisfies delivery of
a blocking report.

## Latest reviewer response and no duplicate approvals

Subject to the precedence rules, the latest reviewer response supersedes earlier
reviewer instructions and the agent's own old `NEXT_ACTION`. After a blocking report,
Codex must read the complete reviewer response before another action starts.

Do not request the same approval again when scope/conditions are unchanged. Re-check
the latest reviewer response and history before escalating.

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

## Required report metadata

Every reviewer-facing report must include at least:

- `REPORT_TYPE`
- `CURRENT_DAY` or task identity
- `STATE / PHASE`
- `CURRENT_ACTION` or completion state
- `EVIDENCE` / `VALIDATION` as applicable
- `LOCAL_LLM_INVOCATIONS`
- `BLOCKER` or `REMAINING_GAPS`
- `NEXT_ACTION` / `NEXT_ACTION_AFTER_REVIEW`
- `REVIEWER_DELIVERY_CHANNEL: direct_chatgpt|review_bridge|none`
- `REVIEWER_DELIVERY_STATUS: delivered|pending|failed`
- the full `REVIEW_POLICY_CONTEXT` block

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
- user-facing Codex display alone does not satisfy blocking-report delivery;
- composer-draft protection does not excuse delivery;
- ordinary progress reports do not block execution;
- completion always requires artifact-quality checking and reviewer clearance before
  the next Day.

When ambiguity remains, stop only if the ambiguity materially changes authority,
scope, safety, evidence validity, or business/product direction. Otherwise choose the
smallest safe interpretation that preserves forward progress.
