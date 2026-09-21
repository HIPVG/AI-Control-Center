# Week 1 Day 4-7 Autonomous Execution

## Purpose

Extend the completed Zero-Touch Control Center from the initial trusted
process-consistency experiment into the remaining LocalLLM-Lab Week 1 program.

Authoritative experiment intent comes from LocalLLM-Lab
`docs/week1-runbook.md`. AI Control Center may orchestrate only capabilities
that are already configured and approved. It must not invent missing benchmark
tools, download models, or broaden experiment conditions silently.

## Target operator experience

Normal operation:

```text
Open Dashboard
  ↓
Recommended next action: Continue Week 1
  ↓
[ Continue autonomously ]
  ↓
Day 4 → Day 5 → Day 6 → Day 7
  ↓
complete or genuine attention boundary
```

No repeated free-form Goal should be required while following the approved Week 1
program.

## Day 4 — Cross-family small comparison

Objective:
- run the approved Gemma/Llama cross-family comparison on the same 4-case set;
- keep non-model conditions fixed;
- record family smoke results, telemetry, and review evidence.

Policy:
- use only already-installed and explicitly approved local models;
- no automatic model download/import/install;
- if no approved cross-family model is available, return
  `EXTERNAL_ACTION_REQUIRED` with the missing approved capability;
- do not reinterpret runtime/OOM limitations as model-quality failures.

## Day 5 — Technical benchmark preparation / execution

Priority order from the LocalLLM-Lab runbook:
1. llama-bench;
2. minimal Japanese quality benchmark;
3. structured-output benchmark;
4. context test.

Policy:
- execute only benchmark capability already present and approved in LocalLLM-Lab;
- do not install a missing benchmark automatically;
- keep benchmark command/version/result evidence;
- stop at an external-action boundary if the next benchmark is unavailable.

## Day 6 — Context / processing behavior

Objective:
- record the context profile, cache/offload/processing behavior, and observed
  limitations.

Policy:
- current context profile is preparation-only unless LocalLLM-Lab already
  contains an approved executable condition;
- do not silently increase context length;
- any new context band, output budget, offload strategy, or processing condition
  requires explicit approved configuration first;
- preparation-only work may complete without model execution if that is the
  authoritative runbook state.

## Day 7 — Week 1 summary / next-phase decision

Automatically aggregate:
- model manifests and actual quantization;
- smoke/comparison results;
- telemetry;
- observed limitations;
- known failed/blocked attempts;
- confidence classes and evidence references.

Produce a bounded Week 1 summary and recommend the next phase from the runbook
options:
- RAG / Gold Corpus;
- Generator v1.2;
- more model comparison;
- long-document/context work;
- structured tasks;
- performance/scaling.

The recommendation is advisory. If the options materially change project
direction or require new authority, return `HUMAN_DECISION_REQUIRED`.

## Advancement rules

Control Center may advance from one Day to the next only when:
- the current Day is complete, skipped by authoritative policy, or explicitly
  blocked with a typed reason;
- required artifacts/evidence are recorded;
- no unresolved `EXTERNAL_ACTION_REQUIRED` or `HUMAN_DECISION_REQUIRED` exists.

Routine model-quality findings are experiment results, not code-fix triggers.
Builder must remain unused unless an actual harness/code defect is classified and
policy permits repair.

## Human Gate

`WEEK1_DAY4_7_AUTONOMOUS_VALIDATION`

Minimum external validation should demonstrate:
- Dashboard recommends the next Week 1 Day without another typed Goal;
- at least one real configured Day 4-7 action runs through the Zero-Touch path;
- missing unapproved model/tool/context authority stops cleanly rather than being
  installed or expanded;
- state persists and resumes from the correct Day;
- Day 7 can produce a bounded summary when prior Day evidence is sufficient.
