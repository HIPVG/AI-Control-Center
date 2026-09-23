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

- Target a reviewer-facing `PROGRESS_UPDATE` about every 5 minutes during active work,
  even if no major event occurred. A separate report/instruction transport task checks
  about every 2 minutes; therefore a 5-minute periodic report becomes due on the first
  2-minute check after the threshold, giving an effective periodic interval of up to
  about 6 minutes. This is intentional.
- `PROGRESS_UPDATE` is a reviewer checkpoint: if delivery succeeds, pause at the safe checkpoint and wait for the reviewer response before continuing; if delivery cannot be completed, continue within existing authority and try again at the next scheduled report.
- At about 25 minutes, avoid starting a new large investigation or redesign; prefer
  evidence preservation, commit/push when appropriate, history update, and a safe
  checkpoint.
- Internal DoD reassessment may happen more often; periodic reporting is not a
  substitute for real execution.

### Two-minute report/instruction transport cadence

A deterministic local transport/fetch task may run about every 2 minutes. Its job is
to:
- detect whether a periodic progress report is due;
- deliver any pending reviewer-facing report;
- fetch/apply any available reviewer instruction/response.

The 2-minute transport cadence is **not** the PROGRESS_UPDATE cadence. Do not emit a
full progress report every 2 minutes merely because the transport task runs every 2
minutes.

Periodic progress remains nominally 5 minutes. With a 2-minute checker, the first
eligible check after 5 minutes may occur at approximately minute 6, so the effective
periodic reporting gap is bounded to about 6 minutes.

Do not wait for the periodic threshold when a blocking event occurs. A
`DECISION_REQUEST`, `COMPLETION_REPORT`, or material authority/safety blocker becomes
eligible for delivery immediately and should be handled on the next 2-minute transport
check.

## Reviewer report types

Exactly three control report types are used. `PROGRESS_UPDATE` is delivery-dependent: successful delivery pauses for reviewer guidance; failed delivery does not halt ordinary work.

### `PROGRESS_UPDATE` — reviewer checkpoint

Use for routine state transitions, validation, commit/push, LocalLLM activity,
evidence creation, remaining gaps, and ordinary checkpoints. Its purpose is to give
the reviewer a chance to stop over-investigation, redirect work, or tighten scope.

If a `PROGRESS_UPDATE` is successfully delivered to the ChatGPT reviewer, pause at
the current safe checkpoint and wait for the complete reviewer response before
continuing. Apply that response before the next action.

If delivery cannot be completed through either direct ChatGPT delivery or the
Review-Bridge, do not stop ordinary work solely because reporting transport failed.
Record the failed delivery, continue within existing authority, and try again at the
next 2-minute progress checkpoint. Reporting does not consume or revoke an existing
Day-start authorization.

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

### First action: direct ChatGPT delivery

For **every** reviewer-facing report, the first delivery action is to try the target
ChatGPT reviewer conversation directly. Review-Bridge is never the first choice.

Do not create, stage, commit, or push a Review-Bridge packet before the direct
ChatGPT path for that report has actually been attempted, except when a verified
non-empty user draft occupies the actual editable composer buffer. In that one
case, protect the draft and treat the direct attempt as temporarily unavailable;
for blocking reports, re-check after the required 2-minute interval before any
Bridge fallback is allowed.

A past direct-delivery failure never changes this ordering for a later report.
Each new report starts again with direct ChatGPT delivery as the first action.

All reviewer-facing reports are intended for the ChatGPT reviewer. They must also be
shown in full in the current user-facing Codex output so the human can inspect or
relay them, but user-facing display alone is **not** successful delivery for a
blocking report.

Canonical delivery channels:

1. direct ChatGPT reviewer delivery when available and safe;
2. fallback archive/relay repository `HIPVG/AI-Control-Center-Review-Bridge` when direct
   delivery is unavailable or unsafe. Review-Bridge is a dead-drop transport only;
   ChatGPT does not automatically wake up or self-detect a new packet.

For `PROGRESS_UPDATE`, try direct ChatGPT delivery once at the checkpoint.
If direct delivery succeeds, pause and actively acquire the reviewer response.
If direct delivery is unavailable or fails, display the report and continue within
existing authority. Do not switch to Review-Bridge merely because a progress report
could not be sent directly; try direct delivery again at the next scheduled checkpoint.

For `DECISION_REQUEST` and `COMPLETION_REPORT`, direct ChatGPT delivery is the
normal path. Review-Bridge is a last-resort dead-drop after the bounded direct-delivery
window is exhausted; publication there does not mean ChatGPT has received the report.

### Blocking-report direct-delivery window

For a blocking report, perform at most 3 direct-delivery opportunities:

1. inspect the **actual editable composer buffer**;
2. if it is empty, attempt direct ChatGPT delivery;
3. if it contains a verified non-empty user draft, do not overwrite it; treat direct
   delivery as temporarily unavailable for this opportunity;
4. if direct delivery did not succeed, wait 2 minutes;
5. repeat the same buffer check/direct attempt;
6. if still unsuccessful, wait another 2 minutes and make the third and final
   opportunity.

A verified draft therefore causes a **re-check after 2 minutes**, not an immediate
switch to Review-Bridge. Placeholder/UI text never counts as a draft.

If direct delivery succeeds at any opportunity, do not use Review-Bridge; start the
normal reviewer-response acquisition loop.

Only after all 3 direct-delivery opportunities fail or remain unavailable:

- publish the full blocking report to Review-Bridge **once** as an audit/relay fallback;
- display the full report to the human;
- record:
  - `DIRECT_DELIVERY_OPPORTUNITIES: 3`
  - `DIRECT_DELIVERY_RESULTS: <all opportunities>`
  - `REVIEW_BRIDGE_PACKET: <packet id or failure>`
  - `LAST_ERROR: <exact bounded error>`
- stop at the safe checkpoint for human relay/attention.

Do **not** wait 2 minutes and retry Review-Bridge publication as though it were a
ChatGPT delivery channel. A Review-Bridge Git push rejection or other bridge transport
failure is not a reviewer-response retry condition. Record it, show the report to the
human, and stop for relay/attention.

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

A verified non-empty draft protects that buffer, but it does not trigger immediate
Review-Bridge fallback. For a blocking report, re-check the actual buffer after the
2-minute direct-delivery interval, for at most 3 direct-delivery opportunities total.
Use Review-Bridge only after those opportunities are exhausted. For a
`PROGRESS_UPDATE`, simply continue and retry direct delivery at the next progress
checkpoint. A placeholder, UI label, or unverified state never justifies skipping a
direct-delivery opportunity.

Any false-positive claim that a placeholder/UI label was a draft is a
`REPORTING_PROTOCOL_FAILURE` and must be recorded in engineering history.

`REVIEWER_POST_PENDING: yes` is informational only. It never satisfies delivery of
a blocking report.

## Reviewer response acquisition

Successful report delivery is not enough. When a report requires reviewer guidance
(a successfully delivered `PROGRESS_UPDATE`, any `DECISION_REQUEST`, or any
`COMPLETION_REPORT`), Codex must actively acquire the reviewer response rather than
entering a passive indefinite wait.

For direct ChatGPT delivery:

1. Record the delivered report timestamp and/or another stable marker of the sent report.
2. Stay at the safe checkpoint and poll the target ChatGPT conversation for a new
   assistant/reviewer message that is newer than the delivered report.
3. Poll about every 15 seconds while the response is generating; generation/status
   UI is not composer-draft evidence.
4. When generation completes, read the **entire** new reviewer message, not only the
   first line or visible preview.
5. Verify the message is newer than the sent report, then apply it as the latest
   reviewer response before the next action.

If no new completed reviewer response is observed within 5 minutes after successful
direct delivery, record `REVIEWER_RESPONSE_TIMEOUT`, keep the safe checkpoint, and
retry response acquisition once more for up to 5 minutes. Do not resend the same
report merely because response acquisition is slow unless the reviewer channel shows
the original delivery did not actually succeed.

Review-Bridge has no autonomous response-acquisition semantics. Codex may read a
matching `outbox/<packet-id>/review.md` only after the human/reviewer has explicitly
caused or confirmed that a response was written there. Do not poll an empty outbox
expecting ChatGPT to wake up by itself.

A statement such as `waiting for reviewer response` is incomplete unless Codex is
actually performing the corresponding acquisition loop or has exhausted the bounded
acquisition windows above.

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
- user-facing Codex display alone does not satisfy blocking-report delivery;
- Review-Bridge publication alone does not mean ChatGPT has received the report;
- composer-draft protection does not excuse delivery;
- successfully delivered progress reports pause execution until reviewer response; undelivered progress reports do not block ordinary work;
- completion always requires artifact-quality checking and reviewer clearance before
  the next Day.

When ambiguity remains, stop only if the ambiguity materially changes authority,
scope, safety, evidence validity, or business/product direction. Otherwise choose the
smallest safe interpretation that preserves forward progress.
