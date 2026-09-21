# Autonomous Day orchestration

The Day Runner is a persistent scheduler over trusted task IDs in
`config/plans.yaml`. It does not accept commands, paths, prompts, or task
definitions from the browser.

## Safety model

- Codex Architect selects only an eligible configured queue item through a
  read-only structured CLI call in an isolated role workspace.
- The existing task executor remains responsible for deterministic prechecks,
  worktrees, Scope Guard, Codex execution, and postchecks.
- Deterministic tasks never invoke an independent evaluator. Semantic review
  requires the explicit trusted task policy `independent_evaluator_required`.
- Semantic tasks receive only a bounded structured result and configured metric
  names. A `REPAIR` decision is bounded by the plan's repair-loop limit.
- Architect, evaluator, and Codex call counts are persisted and guarded. Role
  token usage is persisted separately. Before every provider/Codex path, the
  trusted ModelRouter selects and persists the lowest allowed logical profile;
  profile token totals and bounded escalation reasons are persisted separately.
- Any provider error, unknown selection, cap breach, or review result enters
  the Human Review queue and stops the plan.

## Providers

`codex` is the normal core provider: Architect, Builder, and optional First
Reviewer are separate roles sharing the hardened Codex CLI foundation. Architect
and Reviewer use `read-only`, `--json`, and an explicit output schema in a
managed role workspace; Builder alone receives `workspace-write` in an isolated
task worktree. Normal Codex-Core Day plans require no `OPENAI_API_KEY`.

`mock` providers are deterministic and used by tests; their diagnostics report
`provider: mock` and no executed model. `openai` providers are optional
independent providers and use
the official Python SDK when `OPENAI_API_KEY` is set. The trusted ModelRouter
resolves the concrete configured OpenAI model, reasoning effort, timeout, and
maximum output from `config/model_profiles.yaml`; provider settings cannot
override that selection. They use the Responses API, `store: false`, a strict
JSON schema, and at most one transient retry. Startup never creates an OpenAI
client or performs a call.

Provider requests contain only trusted compact task/queue metadata, bounded
task evidence, and configured rubric fields. Provider diagnostics retain model,
duration, attempt count, typed decision, and token usage; credentials, headers,
raw requests, and raw responses are never persisted.

Provider-generated responses use dedicated strict DTO schemas. Every DTO field
is required (nullable fields use `null`), every object forbids additional
properties, and runtime-only token usage or diagnostics are composed only by
trusted Python after provider output validation. Provider failures persist a
bounded error code, request stage, and sanitized diagnostics for Human Review.

## Operation

`POST /api/day/start/{plan_id}?mode=single-step` advances at most one selected
task, then persists `PAUSED` when work remains. `mode=continuous` processes
trusted queue items until completion, review, provider/safety failure, or a
hard limit. `POST /api/day/resume` preserves the original mode unless the same
typed mode query is supplied. `POST /api/day/stop` persists a stop request.

For M20, Dashboard v2 exposes a continuous action only when the selected
trusted plan enables it. If that same plan is `PAUSED` or `STOPPED`, the action
uses the typed resume endpoint so already terminal queue items are not rerun;
otherwise it starts the configured plan in continuous mode. The browser still
cannot submit task definitions, commands, paths, prompts, budgets, or an
unsupported execution mode. The DayRunner itself rejects a replacement start
while a Day is `RUNNING`, `PAUSED`, or in `HUMAN_REVIEW`; it must be resumed or
the review handled without silently discarding its trusted queue and audit.

## Exception-driven escalation

Day failures are persisted as typed escalation events. Bounded transient
Architect failures (`CODEX_TIMEOUT`, failed/invalid bounded role output) retry
once under trusted plan policy; invalid Architect selections trigger one bounded
replan using the same configured queue. Missing runtime prerequisites become
`EXTERNAL_ACTION_REQUIRED`; unknown, scope, authority, or policy failures remain
`HUMAN_DECISION_REQUIRED`. Automatic recovery never changes task scope, plans,
budgets, or retry ceilings.

Hard limits are trusted plan/config values: tasks per run, failed tasks,
Architect/Evaluator/Codex calls, repair loops, and role-specific token budgets.
Pre-call provider budget gates stop safely; a usage value reported after a
successful provider response records a warning rather than rewriting completed
work. Day and overall progress are calculated from terminal queue tasks.

`week1-day3-local-llm-v2` and `week1-day3-local-llm-v3-codex-core` are
three-task Codex-Core validation plans. The latter is the explicit external
Codex-Core validation plan. The completed historical one-task
`week1-day3-local-llm` plan remains unchanged.
`week1-day3-local-llm-real-architect` is opt-in and fails with a typed provider
configuration error until credentials and a trusted profile mapping are configured.
`week1-day3-local-llm-v2-real-architect` is the equivalent three-task variant.
For a normal PowerShell production session, set `OPENAI_API_KEY`,
`AI_CONTROL_CENTER_ARCHITECT_PROVIDER=openai` before starting
`scripts/start.ps1`. Evaluator overrides use the corresponding
`..._EVALUATOR_PROVIDER` name. Concrete model routing stays in
`config/model_profiles.yaml` and is persisted as bounded diagnostics/state.

## Validated Codex-Core baseline and context policy

`week1-day3-local-llm-v3-codex-core` completed external single-step validation:
Codex Architect selected `PC-001-A`, its deterministic precheck completed with
`COMPLETE_NO_CHANGE`, Builder and Independent Evaluator calls remained zero,
and the Day paused at `33.33%`. The observed Architect call used the `standard`
profile at `medium` reasoning, with 19,132 uncached input tokens, 88 output
tokens, and about 9.6 seconds duration.

That measurement established a baseline, not a reason to relax safety. The
Architect now runs outside repository roots so Codex cannot inherit project
instructions or source context. Its bounded structured input contains only the
plan/day, eligible IDs with titles/types, compact queue/prior-result state,
remaining call budgets, stop limits, and progress. Router settings stay outside
the Architect prompt and remain authoritative in Python and audit telemetry.

## Model routing boundary

`config/model_profiles.yaml` holds stable logical profiles (`economical`,
`standard`, `deep`) and provider-specific concrete execution mappings. The
router consumes trusted plan policy and remaining budgets, but cannot alter task
scope, commands, acceptance criteria, retries, or budgets. The current Codex
CLI runner does not receive guessed model or reasoning flags: it retains its
explicit configuration while its selected profile is audited.

## Semantic task discovery

`PC-001-A`, `PC-001-C`, and `PC-002-A` are configured deterministic dry-run
cases. Existing LocalLLM-Lab review sheets and rubric assets require real model
response artifacts and human review; they are not a safe autonomous semantic
production task. **NO_SAFE_SEMANTIC_TASK_FOUND**: the Evaluator provider is
implemented and test-covered, but no synthetic semantic production task is
invented.
