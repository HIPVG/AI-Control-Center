# LocalLLM-Lab Day 1-14 autonomous execution

The authoritative program is `C:\LocalLLM-Lab\docs\runbooks\work-plan-day1-14.md`.
The runner also reads the documentation map, decision architecture, handoff,
current Git state, and relevant tracked evidence. The older Week 1 program is
not an execution model for this flow.

## Day Contract

Selecting a Day creates and persists a structured contract containing its Day
number, runbook objective, completion criteria derived from the runbook text,
required evidence, shared constraints, authoritative sources, satisfied
criteria, and remaining gaps. The contract expresses *what* must be established;
it contains no Day-specific Python task recipe.

## Execution

`Go` inventories trusted state, evaluates each criterion, and asks the bounded
planner for no more than three remaining work items. A Codex Architect adapter
may supply that plan, but Python rejects items that are not evidence checks or
guarded engine work orders, duplicate an item, exceed the limit, address an
unknown criterion, or add authority outside the remaining gaps.

Guarded engine work orders remain subject to the existing Scope Guard, Git
Guard, token budgets, retry limits, worktrees, and deterministic postchecks.
No browser-provided command, path, model, scope, or acceptance criterion is
accepted. A completed task is not sufficient: only its trusted evidence can
satisfy a Day criterion. Missing evidence triggers at most two replans; it
never silently redefines the objective or criteria.

The built-in fallback is deliberately read-only. It can inventory evidence but
cannot mistake source presence for proof that research or implementation was
completed. This fails closed as `DAY_INSUFFICIENT_EVIDENCE` until the guarded
engine records actual evidence.

## Failure and repair boundaries

Failures are recorded as one of:

- `IMPLEMENTATION_DEFECT`
- `TEST_OR_CONTRACT_DEFECT`
- `MODEL_QUALITY_FINDING`
- `EXPERIMENT_CONFIGURATION_ISSUE`
- `MISSING_EXTERNAL_AUTHORITY`
- `INSUFFICIENT_EVIDENCE`

Only an implementation defect enables `Repair and Go`. LocalLLM may provide a
bounded proposal, but it cannot edit files, choose completion, or rerun a
research result. The proposal is handed to the guarded Codex/engine boundary
for inspection, scope validation, implementation, and deterministic testing.
A poor model result from an experiment remains model-quality evidence and is
never offered to the repair loop.

## Persistence and controls

The persisted snapshot includes the selected Day, complete Day Contract,
criteria, work plan, task states, evidence, issue classification, and replan
count. A process restart converts `RUNNING` to `PAUSED`; `Resume` retains
completed evidence rather than restarting the Day. The dashboard shows Go,
Stop, Resume, the current contract/task, evidence, classification, and final
result. Repair is enabled only for a genuine implementation-defect handoff.
