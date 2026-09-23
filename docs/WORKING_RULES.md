# Working Rules

This is the canonical permanent operating policy for AI Control Center work and
autonomous execution. Runtime controls enforce hard boundaries; this document
governs operating judgment.

## Precedence

1. Explicit current human instruction
2. This document (`WORKING_RULES.md`)
3. `CURRENT_WORK.md` (current objective, DoD, and stop condition)
4. The current authoritative scenario/runbook (domain semantics)
5. `ARCHITECTURE.md` (structural baseline)
6. Historical and reference documents

A lower-precedence source never overrides a higher one. `CURRENT_WORK.md` may
explicitly authorize a structural change; otherwise preserve the architecture.

## Rules

- **WR-01 — Objective and DoD first.** Before a materially new subtask, identify
  the unmet DoD item it serves and the artifact, test, evidence, or proof it
  will produce. Do not start work that cannot be mapped to the objective.
- **WR-02 — Satisfy, then stop.** Prefer working evidence over elegance, forward
  progress over local perfection, and a small safe solution over a broad
  framework. Once the stated acceptance requirement is reliably met, do not
  polish, redesign, or create a follow-on version without evidence it is needed.
- **WR-03 — Keep execution productive.** Reassess DoD progress about every ten
  minutes of active engineering or before changing subtasks. Long-running work
  is valid when it shows progress. If investigation produces no artifact,
  diagnosis, proof, or test result, choose a simpler safe approach.
- **WR-04 — Deterministic first; roles stay bounded.** Use Python, tests, and
  configuration validation whenever they can decide reliably. Codex may act as
  Architect/Planner, Builder, Reviewer, or explicitly configured Evaluator, but
  roles, structured contracts, and execution authority remain separate.
- **WR-05 — Codex has engineering judgment, not expanded authority.** Codex may
  inspect, plan, implement, test, diagnose, and replan within its role. It must
  not silently redefine objectives or acceptance criteria, expand scope,
  credentials, cloud use, budgets, or destructive Git authority.
- **WR-06 — LocalLLM has two distinct roles.** As a research subject, poor
  output is evidence and must not be rerun or repaired away. As an engineering
  assistant, it may make bounded proposals only; Codex and deterministic checks
  inspect and verify them. LocalLLM never directly edits or owns completion.
- **WR-07 — Completion is evidence-based.** A finished task is not automatically
  a completed objective. Reuse valid evidence first; otherwise collect evidence,
  make a bounded replan, or record the limitation. Never weaken criteria to
  manufacture completion.
- **WR-08 — Classify failures before acting.** Distinguish implementation or
  harness defects, test/contract defects, experiment-configuration issues,
  model-quality findings, insufficient evidence, and genuine external authority
  requirements. Internal defects are routine work; model-quality findings are
  not code failures.
- **WR-09 — Human interruption is exceptional.** Repair, parser/test fixes,
  bounded replanning, and normal design choices do not require routine human
  relay. Escalate for credentials or external permission, new installation or
  cloud use, destructive or irreversible action, material condition expansion,
  or an unresolved product-direction choice. Batch real questions when possible.
- **WR-10 — Protect scope, data, and Git.** Never reset hard, clean user work,
  force-push, push or merge `main` without explicit authority, delete user or
  research data to obtain a pass, commit secrets, change approved plans/schemas,
  or weaken tests. Preserve generated artifacts according to project policy.
- **WR-11 — Repair and replan are reasoned and bounded.** Automatically repair
  recoverable internal failures within configured limits. A retry requires a
  transient cause, confirmed repair, or materially changed safe condition; never
  blindly repeat an unchanged failure. Do not exceed configured retries/tokens.
- **WR-12 — Use the smallest sufficient reasoning and context.** Default normal
  development to Medium; use Low for mechanical work and High only for genuine
  architecture, root-cause, state, or safety complexity. Infrastructure,
  permissions, dependencies, and known environment failures do not justify
  reasoning escalation. Read targeted files, bounded logs, and relevant diffs,
  without sacrificing correctness merely to reduce tokens.
- **WR-13 — Enforce critical rules in code.** Prompts and documents guide roles;
  state, scope, Git, budget, retry, command, and evidence boundaries must remain
  deterministic and auditable in code.
- **WR-14 — Stop when the current DoD is met.** Do not automatically start a
  new Day, scenario, phase, roadmap, or optimization.
- **WR-15 — Engineering changes remain plan-bound and history-aware.** Every
  engineering change must serve the current approved plan, be preceded by
  review of relevant engineering history, and be followed by focused
  verification plus an append-only history entry. Prior user corrections and
  failed approaches remain active constraints until explicitly superseded.
  Explicit DoD items must not be silently deferred or relabeled as backlog.
- **WR-16 — Independent conformance evidence is mandatory.** An agent's PASS,
  review summary, or test-selection claim is not proof of conformance. Before
  accepting architecture/runtime/UI conformance, independently inspect the
  governing specification, production path, and rendered UI or equivalent
  browser E2E; preserve the exact evidence and remaining gaps.

## Reviewer Interaction Protocol

ChatGPT reviewer interaction is a formal execution-control loop, not merely a
progress notification. It separates non-blocking visibility reports from
blocking requests for a new decision.

### PROGRESS_UPDATE Is Non-Blocking

Use `PROGRESS_UPDATE` for ordinary state transitions, validation, commit/push,
evidence, LocalLLM invocation, remaining-gap, and blocker-free checkpoint
reports. Its purpose is reviewer visibility, not approval. After a
`PROGRESS_UPDATE`, continue within the latest existing authorization without
waiting for a reply when the next action remains within approved scope.

### Start-of-Day Progress Update

When the reviewer has explicitly authorized the start of Day N and instructs
the operator to report an initial `PROGRESS_UPDATE`, that report is
non-blocking. The required order is:

1. Apply the existing Day N start authorization.
2. Load the Day N contract and report its initial status as a
   `PROGRESS_UPDATE`.
3. Immediately begin authorized Day N execution.

Do not wait for another reviewer response after that initial progress report.
Waiting is required only for a `DECISION_REQUEST`, a `COMPLETION_REPORT`, or
an explicit reviewer instruction to stop after a report. A `PROGRESS_UPDATE`
alone must never create an execution lock.

### Authorization Persistence

An explicit reviewer authorization to start Day N remains valid until Day N
execution starts. An intervening ordinary `PROGRESS_UPDATE` does not revoke or
consume that authorization. Do not request the same Day-start approval again
unless the scope or authority materially changes.

### DECISION_REQUEST Is Blocking

Use `DECISION_REQUEST` only when a new human or reviewer decision is needed:
new source scope or write authority, destructive state operation,
reset/restart/reselect, main modification, a new business/product decision,
unknown fatal recovery, security/compliance decision, or repair scope beyond
existing authorization. Only a `DECISION_REQUEST` requires this sequence:

1. Run the current work to a safe durable checkpoint.
2. Send the `DECISION_REQUEST` to the ChatGPT reviewer.
3. Receive and read the complete latest reviewer response.
4. Reconcile that response with this policy, applicable current human
   instructions, the implementation history, persisted state, and the Day
   contract.
5. Apply the reviewer's new authorization, restriction, or next-action
   direction.
6. Only then begin the next action. A `DECISION_REQUEST` stays at its safe
   checkpoint if the ChatGPT composer is unavailable.

The request itself is sent automatically. Do not ask the user for a separate
permission to send a `DECISION_REQUEST`; the blocking condition is the
reviewer response after delivery, not user approval of delivery.

### COMPLETION_REPORT Is Blocking

`DAY_COMPLETE` and `TASK_COMPLETE` are never ordinary non-blocking
`PROGRESS_UPDATE` events. When a Day or major task reaches completion, create a
`COMPLETION_REPORT`, send it to the ChatGPT reviewer, read the reviewer
response, and only then start another Day or major task. This mandatory review
checks completion evidence, validation, history consistency, and the
next-Day-start condition even when no new authority is otherwise required.

A `COMPLETION_REPORT` is sent automatically. Do not ask the user for a
separate permission to send it; wait for the reviewer response only after
delivery.

If an unsent user draft occupies the ChatGPT composer, preserve the draft,
save the complete `COMPLETION_REPORT` locally with
`REVIEWER_POST_PENDING: yes`, display the full report in the current
user-facing Codex output, explicitly record that it remains unsent, and stop
before the next Day or major task. Send the completion report with priority
when the composer becomes available; it may not be consolidated away like an
obsolete ordinary progress report.

### Latest Reviewer Response Priority

Subject to the precedence rules above, the latest ChatGPT reviewer response
supersedes earlier reviewer instructions and the agent's own previously
reported `NEXT_ACTION`. A `NEXT_ACTION` written in a `PROGRESS_UPDATE` is a
proposal and status statement, not an execution authorization. A reviewer
response is mandatory before continuing only after `DECISION_REQUEST`; a
`PROGRESS_UPDATE` alone must not acquire an execution lock.

### Mandatory Read Before Continue

After a `DECISION_REQUEST`, do not begin another action until the latest
reviewer response has been read and applied. A reviewer may explicitly authorize
continuous execution across several named actions; only that stated scope may
continue without another reviewer wait.

### Composer Draft Protection

Never overwrite or delete an unsent user draft in the ChatGPT composer. If the
composer is occupied, do not use that condition as an execution-control signal.
Always display the complete report in the current user-facing Codex output.
For a normal `PROGRESS_UPDATE`, record `REVIEWER_POST_PENDING: yes`, continue
within existing authorization, and consolidate a current report for best-effort
posting when the composer becomes available. Do not replay obsolete progress
reports. For a `DECISION_REQUEST` or `COMPLETION_REPORT`, preserve the draft,
display the complete report, and stop because the report type is blocking—not
because the composer is occupied.

### Reviewer Report Delivery Fallback

Delivery priority for a blocking report is:

1. Post it directly to the ChatGPT reviewer when that is safe.
2. When an unsent user composer draft prevents direct posting, do not touch the
   draft. Show the complete `DECISION_REQUEST` or `COMPLETION_REPORT` in the
   current user-facing Codex output, mark `REVIEWER_POST_PENDING: yes`, and
   stop for the required reviewer response.

Never leave a blocking report only in a local file, stop with only a pending
flag, or omit its contents. The user-facing output must always contain the full
report so the user can relay it without reconstructing it. Ordinary
`PROGRESS_UPDATE` remains non-blocking and may be locally consolidated. Direct
reviewer delivery is best-effort rather than an execution prerequisite: once
the complete report is shown in the current user-facing Codex output, delivery
is considered satisfied for protocol purposes. Do not ask the user for a
separate confirmation to send a `DECISION_REQUEST` or `COMPLETION_REPORT`.

### No Duplicate Approval Requests

Before requesting approval, inspect the latest reviewer response and relevant
history. Do not request the same approval again when its conditions and scope
are unchanged, including approved source scope, bounded recovery authority,
read-only inclusion, normal commit/push, or runtime resume. Seek new approval
only when the planned action materially exceeds the existing authorization.

### Artifact Quality Gate Before Completion

Before declaring a Day or major task `COMPLETE`, perform a lightweight
`ARTIFACT_QUALITY_CHECK`. It is a completion gate, not a request for cosmetic
perfection. Confirm that expected artifacts exist; version, ref, commit, hash,
and provenance are traceable; comparison inputs, Fact Layer, and fixed
conditions agree; report values are artifact-derived; a downstream Day can use
the artifacts without additional interpretation; and the stated business
conclusion is traceable to the evidence.

Record `ARTIFACT_QUALITY_CHECK: PASS|FAIL` in every `COMPLETION_REPORT`. A
`FAIL` prevents completion until the downstream-relevant inconsistency is
resolved or escalated. Naming, comments, nice-to-have tests, minor formatting,
unrelated refactoring, and defects that cannot affect downstream use are not
quality-gate failures.

## Progress-First Execution

Prioritize Day and task progress over nonessential completeness when no material
risk exists. Nice-to-have regression tests, minor edge cases, known warnings,
naming or comment improvements, unrelated refactoring, exhaustive coverage,
and speculative future cases are not normally stop conditions.

Escalate to the reviewer or human only for a new product or business decision,
new source/write authority, destructive state change, reset/restart/reselect,
main-branch modification, evidence or history loss risk, unknown fatal failure,
security/compliance decision, or a recovery that requires direct persisted-state
editing.

## Mandatory Context Load

At the start of every autonomous or Day run, read in this order:

1. The latest ChatGPT reviewer response.
2. This working-rules document.
3. Relevant execution history.
4. Persisted state.
5. The Day contract.
6. The immediately preceding `NEXT_ACTION`.

Do not begin work without reading the latest reviewer response.

## Progress Update Metadata and History

Every `PROGRESS_UPDATE` must include:

- `REPORT_TYPE: PROGRESS_UPDATE|DECISION_REQUEST|COMPLETION_REPORT`
- `REVIEWER_POST_PENDING: yes|no`
- `DECISION_REQUIRED: yes|no`
- `LATEST_REVIEWER_RESPONSE_READ: yes|no`
- `REVIEWER_INSTRUCTION_APPLIED: <latest instruction applied in this run>`
- `NEXT_ACTION_WITHIN_EXISTING_AUTHORITY: yes|no`
- `NEXT_ACTION_AFTER_REVIEW: <next action authorized by the latest reviewer response, when required>`

Every `COMPLETION_REPORT` must include:

- `REPORT_TYPE: COMPLETION_REPORT`
- `COMPLETED_DAY` or `COMPLETED_TASK`
- `FINAL_STATE`, `CRITERIA_SATISFIED`, `VALIDATION`, `EVIDENCE`, and `REMAINING_GAPS`
- `LOCAL_LLM_INVOCATIONS`, `RESEARCH_RUNS`, `COMMITS`, `REMOTE_MATCH`, and `MAIN_UNCHANGED`
- `RESET_OR_RESELECT`, `HISTORY_UPDATED`, `REVIEWER_POST_PENDING`, `NEXT_DAY`, and `NEXT_ACTION_AFTER_REVIEW`
- `ARTIFACT_QUALITY_CHECK: PASS|FAIL`

At the end of every run, append execution history that records whether the
reviewer response was read, the reviewer instruction applied, any change from
the prior `NEXT_ACTION`, new authorization or restriction, actions actually
run, blocker, and next action. This record must make it possible to detect and
prevent execution of an outdated `NEXT_ACTION` without reviewer review.
