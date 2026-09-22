# Autonomous Next Action Policy

> Current operational rules are governed by `docs/WORKING_RULES.md`. If this
> document conflicts with `WORKING_RULES.md`, the working rules take precedence.

## Purpose

Goal entry is an exception path, not the normal daily interaction.

The normal experience should be:

```text
Current trusted state
  ↓
Control Center derives the next bounded action
  ↓
Codex reasons only when deterministic policy is insufficient
  ↓
Python validates authority and policy
  ↓
Dashboard shows Recommended next action
  ↓
[ Continue autonomously ]
```

A human should type a free-form goal only when changing direction, not when continuing the current trusted program of work.

## Interaction hierarchy

1. **Continue autonomously** — normal path.
2. **Quick actions** — bounded alternatives when more than one trusted direction is available.
3. **Free-form Goal** — intentional change of direction, still subject to the existing Goal-to-Plan policy.

## Recommendation inputs

The next-action planner may use only trusted, bounded state such as:

- current roadmap/milestone state;
- prior trusted experiment outcome;
- configured plans, tasks, and experiments;
- typed escalation/recovery state;
- completion/failure evidence;
- policy/budget limits.

It must not grant new authority.

## Recommendation outputs

A recommendation should be structured and auditable, with fields equivalent to:

- action type;
- trusted target ID;
- concise reason;
- whether reasoning was required;
- whether human attention is required;
- policy validation result.

The recommendation itself does not expand filesystem, command, model-download,
cloud, Git, budget, destructive, or credential authority.

## Success path

After a trusted action completes successfully, Control Center should determine
whether another already-authorized action is the obvious next step.

If yes, expose **Continue autonomously** without requiring the human to rewrite
the same intent as a Goal.

If multiple materially different trusted directions exist, show bounded Quick
Actions or request a human decision.

## Failure path

M25 recovery policy still applies:

```text
failure
  ↓
classify
  ├ retryable → retry
  ├ repairable → bounded repair
  ├ replan-required → bounded replan
  ├ external-action-required → attention
  └ human-decision-required → attention
```

A recovery recommendation must never disguise an authority expansion as a
routine continuation.

## Dashboard target

The primary card should become conceptually:

```text
RECOMMENDED NEXT ACTION

Continue LocalLLM validation
Reason: previous trusted experiment completed successfully.

[ Continue autonomously ]

Quick actions:
[ Re-run smoke ] [ Review results ]

Change direction:
[ Enter a different goal ]
```

The exact UI is implementation-owned.

## Human Gate

The M25 external validation should prove both:

1. a bounded failure can recover/replan without routine human relay; and
2. after a successful trusted action, the Dashboard can propose and execute a
   safe next action through **Continue autonomously** without requiring another
   typed Goal.

Human attention remains required only for genuine authority/external boundaries.

## M25 implementation contract

The current implementation derives `NextAction` entirely in trusted Python from
the latest recorded experiment result and the configured experiment registry.
The only executable recommendation is the fixed
`local_llm_process_consistency_smoke` target. The browser supplies no target,
command, path, model, or configuration to **Continue autonomously**.

Runtime-, configuration-, and harness-blocking outcomes yield
`EXTERNAL_ACTION_REQUIRED` with the recorded classification reason and disable
continuation. A successful or model-quality result keeps the fixed trusted
experiment as the bounded continuation. Executing it audit-records the
structured recommendation and observed outcome.

M25 also exposes a validation-only `invalid-architect-task` scenario. It first
returns an unconfigured task identifier, verifies exactly one bounded
`REPLAN_ARCHITECT`, then returns the sole configured validation task. This
isolated scenario never reads or changes normal Day state.
