# Autonomous Day orchestration

The Day Runner is a persistent scheduler over trusted task IDs in
`config/plans.yaml`. It does not accept commands, paths, prompts, or task
definitions from the browser.

## Safety model

- The Architect selects only an eligible configured queue item.
- The existing task executor remains responsible for deterministic prechecks,
  worktrees, Scope Guard, Codex execution, and postchecks.
- Deterministic tasks never invoke the semantic evaluator.
- Semantic tasks receive only a bounded structured result and configured metric
  names. A `REPAIR` decision is bounded by the plan's repair-loop limit.
- Architect, evaluator, and Codex call counts are persisted and guarded. Role
  token usage is persisted separately.
- Any provider error, unknown selection, cap breach, or review result enters
  the Human Review queue and stops the plan.

## Providers

`mock` providers are deterministic and used by tests. `openai` providers use
the official Python SDK and are opt-in: `OPENAI_API_KEY` plus a configured
model in `config/orchestration.yaml` are required. They use the Responses API,
`store: false`, a strict JSON schema, a 30-second default timeout, and at most
one transient retry. Startup never creates an OpenAI client or performs a call.

Provider requests contain only trusted compact task/queue metadata, bounded
task evidence, and configured rubric fields. Provider diagnostics retain model,
duration, attempt count, typed decision, and token usage; credentials, headers,
raw requests, and raw responses are never persisted.

## Operation

`POST /api/day/start/{plan_id}?mode=single-step` advances at most one selected
task, then persists `PAUSED` when work remains. `mode=continuous` processes
trusted queue items until completion, review, provider/safety failure, or a
hard limit. `POST /api/day/resume` preserves the original mode unless the same
typed mode query is supplied. `POST /api/day/stop` persists a stop request.

Hard limits are trusted plan/config values: tasks per run, failed tasks,
Architect/Evaluator/Codex calls, repair loops, and role-specific token budgets.
Pre-call provider budget gates stop safely; a usage value reported after a
successful provider response records a warning rather than rewriting completed
work. Day and overall progress are calculated from terminal queue tasks.

`week1-day3-local-llm-v2` is the first three-task LocalLLM validation plan.
The completed historical one-task `week1-day3-local-llm` plan remains unchanged.
`week1-day3-local-llm-real-architect` is opt-in and fails with a typed provider
configuration error until credentials and a model are explicitly configured.

## Semantic task discovery

`PC-001-A`, `PC-001-C`, and `PC-002-A` are configured deterministic dry-run
cases. Existing LocalLLM-Lab review sheets and rubric assets require real model
response artifacts and human review; they are not a safe autonomous semantic
production task. **NO_SAFE_SEMANTIC_TASK_FOUND**: the Evaluator provider is
implemented and test-covered, but no synthetic semantic production task is
invented.
