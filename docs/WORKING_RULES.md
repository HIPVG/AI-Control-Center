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
