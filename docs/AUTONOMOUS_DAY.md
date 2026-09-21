# Autonomous Day orchestration

The Day Runner is a persistent, single-step scheduler over trusted task IDs in
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

`mock` providers are deterministic and used by tests. `openai` providers are
opt-in and fail closed unless both `OPENAI_API_KEY` and `OPENAI_DAY_MODEL` are
set. They use the Responses API with `store: false` and a strict JSON schema;
no OpenAI request is made merely by loading the application.

## Operation

`POST /api/day/start/{plan_id}` starts the configured plan and advances one
queue decision/task transition. Continuous mode is deliberately unsupported.
`POST /api/day/resume` advances one paused or stopped plan. `POST /api/day/stop`
persists a stop request. `GET /api/day/status` and `GET /api/day/plans` expose
only persisted status and trusted plan metadata.
