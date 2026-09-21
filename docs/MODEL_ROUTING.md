# Model and Reasoning Routing Policy

## Purpose

AI Control Center must use the least expensive reasoning/model configuration that can reliably complete a task.

This policy extends the existing Deterministic First principle:

```text
Deterministic processing
        ↓
Is AI required?
   ├─ No  → zero AI usage
   └─ Yes
        ↓
   ModelRouter
        ↓
Approved execution profile
```

The goal is to preserve correctness, safety, and auditability while avoiding unnecessary high-reasoning execution.

## Core Principle: Smallest Sufficient Intelligence

High reasoning must not be the default for routine work.

Use the smallest approved profile that is sufficient for the task.

Initial policy:

| Complexity | Default profile | Intended use |
| --- | --- | --- |
| simple | economical | tiny deterministic edits, narrow structured evaluation |
| normal | standard | ordinary implementation, API changes, routine analysis |
| complex | deep | architecture changes, difficult debugging, multi-component reasoning |
| critical / repeated reasoning failure | escalated approved profile or HUMAN_REVIEW | exceptional cases only |

Logical profiles contain policy and budget estimates. Concrete execution settings
are provider mappings in the same trusted configuration. For example:

```yaml
model_profiles:
  economical:
    provider: codex
    model: terra
    reasoning_effort: low

  standard:
    provider: codex
    model: terra
    reasoning_effort: medium
    provider_profiles:
      openai:
        model: gpt-5.6-terra
        reasoning_effort: medium

  deep:
    provider: codex
    model: terra
    reasoning_effort: high
```

The Router resolves the configured provider mapping before an AI call. The
resulting decision is the concrete provider/model/reasoning/timeout/output
configuration actually supplied to that provider; an Architect or Evaluator
cannot override it. `mock` has no concrete model and reports `provider: mock`.
These identifiers are configuration, not architecture constants.

Stable logical profile IDs should be used in orchestration code.

## ModelRouter

ModelRouter is a policy component independent from Architect, Evaluator, and Codex Runner.

### Inputs

ModelRouter may consider:

- role
- task type
- task complexity
- deterministic gate result
- previous attempt count
- previous failure type
- context size
- remaining task/day token budget
- plan policy
- configured allowed profiles

### Output

A routing decision should contain:

- profile_id
- provider
- model
- reasoning_effort
- timeout
- max_output_tokens
- escalation_reason

ModelRouter does not:

- generate task instructions
- modify task scope
- change acceptance criteria
- change allowed files
- override safety gates
- alter retry limits

## Role Defaults

### Codex Architect

Codex Core default: standard / Medium for normal Day selection. Tiny simple
selection may use economical / Low. The Architect receives bounded queue state
only and uses a read-only structured Codex execution; it cannot turn profile
selection into planning or execution authority.

Use deep only when replanning is genuinely complex, multiple tasks interact, previous reasoning failed, or failure classification remains ambiguous.

Architect may report task complexity, but trusted routing policy makes the final profile decision.

### Codex Builder

Normal implementation: standard / Medium. Complex debugging and architecture:
deep / High. Builder remains behind deterministic failure triage and worktree,
Scope Guard, postcheck, and retry controls.

### Codex First Reviewer

Default: no call. When a trusted policy requests a bounded first review after
inconclusive deterministic evidence, use economical or standard. This role is
not an independent evaluator and cannot approve acceptance.

### Independent Evaluator

Default: economical or standard.

Use deep only for ambiguous semantic evaluation where a lower profile is insufficient.

Deterministic tasks should not invoke Evaluator at all.

### Fault / Repair Flow

Initial repair attempt: standard.

Escalate to deep only when the previous permitted attempt failed for a reasoning-related cause.

Infrastructure failures, missing dependencies, permission errors, invalid configuration, or scope violations must not trigger reasoning escalation.

## Escalation Policy

Escalation is bounded.

```text
Low
 ↓
Medium
 ↓
High
 ↓
HUMAN_REVIEW
```

A retry does not automatically mean higher reasoning.

Escalation requires an explicit recorded reason, such as:

- previous reasoning attempt failed
- failure classification is UNKNOWN
- multi-file dependency was discovered
- semantic ambiguity remains
- task is an architecture-level change
- configured confidence threshold was not met

Examples that must not cause escalation:

- missing dependency
- network failure
- sandbox/permission failure
- invalid environment
- malformed configuration
- Scope Guard failure

## Budget Integration

ModelRouter works with Budget Manager before every AI/Codex call.

Before execution:

1. Check role budget.
2. Check task/day budget.
3. Check profile allowance.
4. Check maximum escalation level.
5. Select the lowest sufficient permitted profile.

If the preferred profile exceeds available budget:

- use a lower profile only if task policy explicitly permits it
- otherwise stop with HUMAN_REVIEW or STOPPED

The router must never silently override budget policy.

Post-run token overage remains an observed warning, not a retroactive failure of already completed work.

## Observability

Persist for each AI/Codex call:

- selected profile
- provider
- model
- reasoning effort
- reason for selection
- escalation history
- gross input tokens
- cached input tokens where available
- uncached input tokens where available
- output tokens
- duration
- outcome

Future dashboard support should display:

- Current Profile
- Model
- Reasoning Effort
- Escalation Count
- Why this profile was selected
- Token usage by profile

## Autonomous Day Integration

Autonomous orchestration should conceptually become:

```text
Task Queue
   ↓
Deterministic Gate
   ↓
ModelRouter
   ↓
Codex Architect / Codex Builder / optional Codex First Reviewer /
optional Independent Evaluator
   ↓
Result
   ↓
Optional bounded escalation
   ↓
Next task
```

Deterministic First remains above ModelRouter. If no AI call is required, ModelRouter is not invoked.

## Safety

A more capable profile does not grant more authority.

Model selection must never:

- bypass Scope Guard
- bypass deterministic tests
- expand allowed files
- change acceptance criteria
- increase retries beyond configuration
- override HUMAN_REVIEW
- bypass token budgets
- weaken Git safety

Reasoning capability and execution authority are separate concerns.
