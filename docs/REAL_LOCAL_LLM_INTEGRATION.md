# Real LocalLLM Experiment Integration

## Purpose

Connect AI Control Center to the already-existing LocalLLM-Lab real experiment runners so the Control Center can execute and govern real local-model validation, not only dry-run code checks.

This milestone should begin immediately after M21 Exception-driven escalation is externally validated.

## Principle

A model producing a weak or incorrect answer is an **experiment result**, not automatically a code defect.

The orchestration system must distinguish:

- experiment execution failure;
- environment/runtime failure;
- model-quality result;
- deterministic harness defect;
- configuration/policy defect;
- actual code defect.

Do not route ordinary model-quality findings into Codex Builder as CODE_FIX.

## Existing LocalLLM-Lab capability

LocalLLM-Lab already contains real local execution paths and prior Qwen3 8B/14B measurements, including Ollama-based experiment/process-consistency runners.

AI Control Center should reuse those runners rather than build a second inference stack.

## Target flow

```text
Trusted experiment plan
  ↓
preflight / engine health / model availability
  ↓
LocalLLM-Lab real runner
  ↓
responses + telemetry + artifacts
  ↓
deterministic artifact validation
  ↓
Codex interpretation / comparison when reasoning is useful
  ↓
next experiment / report / typed escalation
```

## Initial scope

Start with a small, already-understood real LocalLLM validation rather than full Week 1 automation.

Preferred first integration target:

- project: LocalLLM-Lab
- engine: existing local Ollama path
- model: an already-installed, approved local model such as the existing Qwen3 8B configuration
- cases: bounded process-consistency smoke set
- output: existing LocalLLM-Lab result artifacts
- no automatic model download/install
- no cloud inference fallback

The exact existing runner/config should be discovered from LocalLLM-Lab and reused.

## Task semantics

Introduce or otherwise represent a trusted **experiment** execution path distinct from ordinary code-fix tasks.

Experiment execution may produce outcomes such as:

- SUCCESS / RESULT_RECORDED
- MODEL_QUALITY_FINDING
- ENGINE_UNAVAILABLE
- MODEL_NOT_FOUND
- TIMEOUT
- CONFIGURATION_BLOCKED
- HARNESS_FAILURE
- HUMAN_DECISION_REQUIRED

Only genuine harness/code defects should enter Codex Builder repair flow.

## Authority and safety

Normal real LocalLLM experiment execution may:

- call already-configured local loopback inference endpoints;
- execute trusted LocalLLM-Lab runner commands;
- write experiment artifacts only to configured result locations;
- read bounded result/telemetry evidence;
- continue to the next configured experiment when policy permits.

It must not silently:

- download or install new models;
- change model licenses/approval status;
- enable cloud inference;
- alter benchmark/oracle truth;
- rewrite prior result artifacts;
- expand case/model scope beyond trusted plan policy;
- modify LocalLLM-Lab code merely because a model answer is poor.

## Evaluation

The first integrated run does not need automatic semantic scoring if the existing benchmark intentionally requires human calibration.

However, Control Center should capture enough bounded evidence to let Codex summarize:

- run success/failure;
- model/runtime identity;
- case count and success/failure counts;
- token/latency/resource telemetry where available;
- model-quality observations without converting them into code-fix claims.

Later milestones may add bounded independent evaluation once a trustworthy rubric/task is available.

## Dashboard

Real experiment execution should eventually be visible from the existing dashboard:

- experiment/run state;
- engine/model;
- cases;
- result artifact reference;
- telemetry summary;
- classification of failures/findings;
- next action.

Avoid requiring routine PowerShell commands.

## Completion gate

The first external gate should prove:

1. Control Center starts a trusted real LocalLLM experiment from the dashboard or trusted API.
2. Local inference actually runs on the configured local model.
3. Result artifacts are produced in LocalLLM-Lab.
4. Control Center records the outcome and telemetry/evidence.
5. Poor model output, if any, is treated as experiment evidence rather than automatically invoking Builder.
6. No new model is downloaded and no cloud provider is used.
7. No routine ChatGPT↔Codex copy/paste handoff is required.

Human gate name:

`REAL_LOCAL_LLM_EXPERIMENT_VALIDATION`

## Strategic role

This milestone deliberately arrives before PowerShell-free polish and Goal-to-Plan.

Reason: once real LocalLLM experiments flow through the Control Center, subsequent autonomy work can be driven by actual experiment failures and decisions rather than synthetic orchestration scenarios.
