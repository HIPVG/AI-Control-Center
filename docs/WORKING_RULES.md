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
composer is occupied, save a normal `PROGRESS_UPDATE` to local progress/history
with `REVIEWER_POST_PENDING: yes`, continue within existing authorization, and
send one consolidated current report when the composer is available. Do not
replay obsolete progress reports. A pending `DECISION_REQUEST` is different:
stop at the safe checkpoint until it can be posted and answered.

### No Duplicate Approval Requests

Before requesting approval, inspect the latest reviewer response and relevant
history. Do not request the same approval again when its conditions and scope
are unchanged, including approved source scope, bounded recovery authority,
read-only inclusion, normal commit/push, or runtime resume. Seek new approval
only when the planned action materially exceeds the existing authorization.

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

- `REPORT_TYPE: PROGRESS_UPDATE|DECISION_REQUEST`
- `REVIEWER_POST_PENDING: yes|no`
- `DECISION_REQUIRED: yes|no`
- `LATEST_REVIEWER_RESPONSE_READ: yes|no`
- `REVIEWER_INSTRUCTION_APPLIED: <latest instruction applied in this run>`
- `NEXT_ACTION_WITHIN_EXISTING_AUTHORITY: yes|no`
- `NEXT_ACTION_AFTER_REVIEW: <next action authorized by the latest reviewer response, when required>`

At the end of every run, append execution history that records whether the
reviewer response was read, the reviewer instruction applied, any change from
the prior `NEXT_ACTION`, new authorization or restriction, actions actually
run, blocker, and next action. This record must make it possible to detect and
prevent execution of an outdated `NEXT_ACTION` without reviewer review.
