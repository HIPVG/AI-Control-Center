# Week 1 Day 4-7 Control Contract

> Historical/superseded for current sequencing. Current operational rules are
> governed by `docs/WORKING_RULES.md`; `docs/DAY_RUNNER_EXECUTION_SPEC.md`
> and the LocalLLM-Lab Day 1-14 runbook define the current scenario.

The Dashboard's recommended action advances the authoritative Week 1 sequence
without another free-form Goal. Each result is a persisted, typed Day record.

- Day 4 checks the LocalLLM-Lab model matrix for an approved cross-family
  runtime. Missing runtime identity or a missing configured runner stops at
  `EXTERNAL_ACTION_REQUIRED`; Control Center does not download a model.
- Day 5 checks the existing benchmark plan. A design-only or disabled benchmark
  is an external capability boundary, never an installation request.
- Day 6 records the existing preparation-only context profile deterministically
  and does not perform inference or increase context settings.
- Day 7 aggregates only recorded Day evidence and emits
  `HUMAN_DECISION_REQUIRED` for the advisory next-phase choice.

All checks use fixed LocalLLM-Lab files selected by server-side project
configuration. The browser supplies no path, command, model, benchmark, or
context setting. Model-quality findings never invoke Builder.
