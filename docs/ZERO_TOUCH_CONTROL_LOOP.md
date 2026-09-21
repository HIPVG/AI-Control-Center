# Zero-Touch Control Loop

## Purpose

AI Control Center exists to remove the human relay between ChatGPT, Codex, PowerShell, and Git.

The target experience is:

```text
Human goal
  ↓
AI Control Center
  ├─ plan
  ├─ execute
  ├─ verify
  ├─ recover / replan
  ├─ commit / push / prepare PR when policy permits
  └─ report
```

ChatGPT remains useful as an optional strategic adviser, but must not be required as a routine bridge between Control Center and Codex.

## North-star outcome

A normal work session should require:

- one human goal or one trusted plan start;
- zero copy/paste handoffs between ChatGPT and Codex;
- zero routine PowerShell commands;
- zero routine Human Review stops;
- automatic recovery for bounded, known failure classes;
- human attention only for genuine exceptions or authority boundaries.

Token use remains observable, but autonomy and successful completion take precedence over micro-optimizing token counts while usage remains operationally acceptable.

## Operating principles

1. **Codex Core remains the reasoning engine.**
2. **Python remains the authority for deterministic facts, policy, limits, state, and safety.**
3. **Human attention is exception-driven, not step-driven.**
4. **Routine failures should be classified and handled automatically when bounded policy allows it.**
5. **The dashboard is the normal control surface. PowerShell is setup/debug tooling, not daily operation.**
6. **The system may plan and replan, but may not silently expand authority.**
7. **Direct automated merge to main, destructive actions, credential entry, or other irreversible/high-authority actions remain explicit boundaries.**

## Escalation model

Replace routine `HUMAN_REVIEW` thinking with typed escalation:

- `AUTO_RESOLVABLE`: deterministic or bounded automated recovery is available.
- `RETRYABLE`: retry is permitted by policy and budget.
- `REPLAN_REQUIRED`: Codex Architect may revise the bounded plan.
- `EXTERNAL_ACTION_REQUIRED`: a credential, permission, external system, or unavailable dependency requires outside action.
- `HUMAN_DECISION_REQUIRED`: authority, ambiguity, destructiveness, policy change, main merge, or another genuine human decision is required.

Only the final two categories should normally interrupt a person.

## Autonomy stages

### A1 — Dashboard-operated autonomous Day
Status: externally validated.

A human can start a trusted Codex-Core single step from the dashboard and observe real state.

### A2 — Continuous zero-touch Day
Status: externally validated.

A trusted three-task Codex-Core plan resumed from 33.33% and completed to 100% without per-task human actions. Builder, Independent Evaluator, and Human Review remained unused because all three deterministic prechecks passed. Bounded failure recovery remains the next stage.

### A3 — Recovery and replanning
Failures are classified. Retry, repair, reviewer guidance, and bounded replan occur automatically where policy permits.

### A4 — Goal-to-Plan
A human supplies a goal rather than a pre-authored task sequence. Codex proposes a bounded plan, Python validates authority/scope, and execution begins without copy/paste prompt handoffs.

### A5 — Git completion
For permitted work, successful verified changes are committed and pushed to an agent branch and a PR can be prepared automatically. Main merge remains an explicit authority boundary unless policy is deliberately changed later.

## Human-intervention budget

The primary optimization metric is not tokens. It is unnecessary human interaction.

Track where practical:

- manual commands required;
- copy/paste handoffs required;
- human interruptions per Day;
- auto-resolved failures;
- auto-replans;
- successful zero-touch completions;
- unresolved escalations;
- elapsed time to recovery;
- AI/token usage as an operational secondary metric.

## Daily-operation target

Normal use should become:

1. Control Center starts automatically with Windows.
2. User opens the dashboard.
3. User chooses a trusted plan or enters a goal.
4. User selects Run.
5. Control Center runs until complete or a genuine escalation occurs.
6. User receives a concise completion/attention report.

No routine PowerShell interaction should be necessary.

## Authority boundaries retained

Automatic execution must still stop or request explicit authority for cases such as:

- credentials/secrets that are not already available;
- destructive or irreversible operations;
- main-branch merge;
- policy/budget/scope expansion beyond trusted limits;
- ambiguous requirements that materially change project intent;
- external permissions or unavailable dependencies;
- repeated recovery failure beyond bounded limits.

## Development priority

Development should now optimize for:

```text
Autonomy
  > reliability
  > recovery
  > observability
  > token optimization
```

Token optimization remains measured, but should not displace features that remove human relay work.
