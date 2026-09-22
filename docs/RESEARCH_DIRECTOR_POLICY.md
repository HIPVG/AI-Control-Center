# Research Director Policy

> Current operational rules are governed by `docs/WORKING_RULES.md`. If this
> document conflicts with `WORKING_RULES.md`, the working rules take precedence.

## Primary objective

AI Control Center exists to accelerate decision-relevant LocalLLM research, not
to maximize automation completeness.

For the current LocalLLM-Lab program, the top-level research question is:

> Can a 12 GB-class GPU with 12–14B-class local models, task decomposition, and
> deterministic Python layers support a practical manufacturing decision-support
> product, and where are the remaining capability / architecture / hardware
> limits?

The system must optimize for evidence that changes a product or architecture
decision.

## Work-selection order

Prefer work in this order:

1. decision-critical experiment;
2. analysis of existing evidence;
3. safe workaround that preserves experimental validity;
4. reusable repair required by more than one experiment;
5. infrastructure / UX polish.

Do not perfect tooling before the next important experiment.

Before starting any non-experiment task, answer internally:

1. Which uncertainty or decision does this unlock?
2. Does it block the next decision-critical experiment or threaten evidence validity?
3. Is there a cheaper safe workaround?
4. Will this repair be reused?
5. What happens if the work is deferred?

If the task does not materially improve decision-relevant evidence, record it in
backlog and continue.

## Research-time budget

Normal target:
- >=80% experiment execution, evidence review, and decision analysis;
- <=15% blocking/reusable repair;
- <=5% orchestration/UI polish.

A blocking repair may temporarily exceed its share, but execution must return to
research immediately after the blocker is removed.

## Runbook semantics

The Day 1–14 runbook defines intended work units and evidence goals. It is not a
railroad.

The system may defer or skip a Day item when:
- existing evidence already answers the intended question;
- the item is no longer decision-relevant to the current architecture;
- an optional dependency is unavailable but later high-information work can
  proceed independently.

Every defer/skip must record:
- the intended question;
- existing evidence or blocker;
- why proceeding elsewhere gives higher information value;
- what condition would cause the item to be revisited.

Do not mark skipped work as experimentally completed.

## Platform feature freeze during research

No new AI-Control-Center feature should be built during the Day 1–14 program
unless at least one is true:
- the next decision-critical experiment cannot run without it;
- evidence integrity would otherwise be compromised;
- the feature will be reused by at least two remaining experiments;
- it removes at least roughly 30 minutes of expected repeated human relay.

Everything else goes to backlog.

## Failure handling

A harness / runner / parser / timeout / artifact-finalization defect is internal
implementation work and is automatically repairable within existing scope.

A weak model answer is experimental evidence, not a code defect.

Do not repeat an unchanged failed inference simply to seek a better result.

After a repair, one controlled rerun is allowed when required to validate the
repair or collect decision-critical evidence.

## Human attention

Do not interrupt the human for routine implementation or each predictable
missing prerequisite.

Continue all independent work first.

Human attention is reserved for:
- new model/runtime/tool installation or download;
- new cloud use or teacher generation;
- credentials / external permissions;
- destructive or irreversible action;
- material experiment-condition expansion;
- a genuine product-direction decision with multiple valid alternatives.

Batch such questions when possible.

The planned final decision point for the current Day 1–14 program is
`DAY14_FINAL_DECISION_REVIEW`.

## Success metric

Primary success metrics:
- important uncertainties retired;
- architecture/product decisions enabled;
- valid new experimental evidence produced;
- human interruptions avoided.

Milestone count, automation completeness, and UI polish are secondary.
