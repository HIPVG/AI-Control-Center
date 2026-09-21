# Autonomous Next Action Policy

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
