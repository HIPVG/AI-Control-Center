# LocalLLM Repair Governance

> **Superseded as a repair-policy source.** The sole canonical Repair
> Supervisor, LocalLLM proposal limit, automatic Codex Expert escalation,
> Solution Catalog teacher loop, and Repair & Go boundary are in
> [DAY_RUNNER_EXECUTION_SPEC.md](DAY_RUNNER_EXECUTION_SPEC.md). The historical
> material below must not be used operationally; notably, a missing or rejected
> LocalLLM proposal now escalates automatically rather than becoming a handoff.

## Purpose

This policy defines the repair boundary for the LocalLLM Day 1-14 program.
It applies to deterministic test failures, harness failures, configuration
drift, and incomplete experiment artifacts.

## Fixed responsibilities

| Responsibility | Owner |
| --- | --- |
| Propose a repair method from bounded failure evidence and supplied source scope | LocalLLM |
| Validate the proposal's scope, exact replacements, and safety constraints | AI Control Center / Codex |
| Run the proposal's focused deterministic test and required regression checks | AI Control Center / Codex |
| Implement an accepted proposal | AI Control Center / Codex |
| Write the outcome, evidence, and reusable guidance to the repair JSON | AI Control Center / Codex |
| Make a final product, plan, schema, or authority decision | Human |

Codex must not independently invent a source repair before LocalLLM has
returned a bounded proposal. A missing, malformed, or unsafe LocalLLM proposal
is recorded as `LOCAL_LLM_NO_PROPOSAL` or `LOCAL_LLM_PROPOSAL_REJECTED`; it is
not silently replaced with a Codex-authored patch.

## Required repair record

Every managed repair records these fields in a JSON artifact:

- Day, run ID, and failure class;
- the LocalLLM proposal status and bounded source scope;
- proposal validation result;
- focused-test and regression outcomes;
- implemented files, if any;
- final disposition: `APPLIED`, `REJECTED`, `NO_PROPOSAL`, or `HUMAN_REVIEW`.

The record must not contain raw prompts, raw model responses, or hidden
reasoning. It may contain the LocalLLM diagnosis, exact proposed edits, and
the deterministic evidence needed to validate them.

## Execution sequence

1. Preserve the failed artifact and classify the failure.
2. Send the smallest relevant failure excerpt and source-file scope to
   LocalLLM.
3. Validate the returned structured proposal before any edit.
4. Run the focused deterministic test for an accepted proposal.
5. Implement the accepted proposal and run the configured regression checks.
6. Update the corresponding repair JSON with the result and reusable guidance.
7. Rerun a local experiment only when its runbook permits a post-repair
   controlled rerun.

## Boundaries

- LocalLLM proposes; it does not receive shell, Git, filesystem, or plan
  authority.
- AI Control Center/Codex validates and implements only the LocalLLM proposal;
  it does not replace that proposal with an independently invented fix.
- A model-quality result is not a source repair unless LocalLLM identifies a
  bounded harness or contract defect and deterministic evidence supports it.
- Browser input cannot define source scope, commands, budgets, or repair rules.
