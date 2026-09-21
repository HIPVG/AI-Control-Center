# Development Reasoning Policy

## Purpose

Codex should choose the smallest reasoning level that is sufficient for autonomous development work.

The objective is not minimum token use. The objective is reliable autonomous completion with minimal human intervention.

Development priority remains:

```text
autonomy
> correctness
> recovery
> human-intervention reduction
> execution time
> token efficiency
```

## Default

Use **Terra / Medium** for normal development work.

Do not ask the human to choose Low, Medium, or High for routine work.

Reasoning level is an execution choice, not an authority choice. A higher reasoning level never expands filesystem scope, Git authority, budgets, acceptance criteria, retry limits, or safety policy.

## Low

Prefer Low when the task is clearly mechanical and bounded, for example:

- documentation-only edits;
- formatting or naming cleanup;
- obvious configuration updates;
- repetitive test additions;
- simple one-file fixes with deterministic acceptance criteria;
- mechanical refactors with no architectural decision.

## Medium

Medium is the normal operating mode.

Use Medium for:

- ordinary feature implementation;
- multi-file changes within an established architecture;
- normal debugging;
- integration work;
- roadmap milestone implementation;
- test design;
- bounded refactoring;
- extending existing APIs, UI, or orchestration behavior.

## High

Escalate to High only when stronger reasoning is justified, for example:

- architecture must be changed or reconciled;
- multiple subsystems interact in a non-obvious way;
- root cause remains unclear after bounded Medium investigation;
- repeated Medium attempts fail for reasoning-related causes;
- concurrency, state recovery, persistence, or authority boundaries are genuinely difficult;
- requirements materially conflict;
- a proposed change could invalidate an architectural assumption;
- a safety-sensitive decision cannot be resolved by deterministic policy.

Do not escalate to High merely because a task is large, unfamiliar, or tedious.

## Failures that do not justify reasoning escalation

Do not increase reasoning level for operational failures such as:

- missing dependency;
- network failure;
- credential failure;
- permission failure;
- unavailable external service;
- known environment failure;
- deterministic test infrastructure failure;
- budget exhaustion;
- scope-guard rejection.

Classify and handle these through the appropriate recovery or escalation path instead.

## Bounded escalation

Normal pattern:

```text
Low → Medium → High
```

or:

```text
Medium → High
```

Escalation should be bounded. Repeated failure at High should not create an endless reasoning loop; use the repository's recovery/escalation policy.

## De-escalation

After a difficult diagnosis or architectural decision is complete, return to Medium or Low for routine implementation, testing, documentation, and cleanup.

High should not remain sticky for an entire milestone without continuing justification.

## Autonomous decision

At the start of a development unit of work, Codex should determine:

- task complexity: simple / normal / complex;
- selected reasoning: low / medium / high;
- concise reason;
- whether this is an escalation from a previous attempt.

The decision should normally be made without asking the human.

Where the runtime cannot change the reasoning level inside the current Codex execution, record the recommendation for the next bounded execution and let the controlling launcher/orchestrator apply it. Do not pretend that a reasoning change occurred when the runtime did not actually apply it.

## Telemetry

When practical, persist or report:

- selected reasoning level;
- reason for selection;
- previous level, if escalated;
- failure type that triggered escalation;
- de-escalation when returning to a lower level.

Do not create verbose logs solely for this purpose.

## Human gate

Reasoning choice itself is not a Human Gate.

Stop for a human only when the underlying work reaches a genuine authority, safety, credential, external-permission, destructive-action, or materially ambiguous requirement boundary.

## Relationship to ModelRouter

Production/workflow ModelRouter policy and this development policy should remain conceptually aligned:

- simple → economical / Low;
- normal → standard / Medium;
- complex → deep / High.

They need not share implementation if that would create unnecessary coupling, but they must not contradict each other without an explicit architectural decision.
