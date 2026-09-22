# AI Control Center v0.1 Codex Bootstrap

> Historical bootstrap reference. Current operational rules are governed by
> `docs/WORKING_RULES.md`; `docs/CURRENT_WORK.md` defines the active work. If
> this document conflicts with them, they take precedence.

You are implementing the first working version of **AI Control Center**.

Read these files first:

1. `AGENTS.md`
2. `docs/WORKING_RULES.md`
3. `docs/CURRENT_WORK.md`
4. `docs/ARCHITECTURE.md`

Treat the current operational sources as authoritative; use this v0.1 bootstrap
only when the current work explicitly calls for it.

Do not reinterpret the architecture unless implementation is impossible. If something is ambiguous, choose the smallest and safest implementation that preserves the design principles.

## Objective

Build the v0.1 local Windows-first Web dashboard and orchestration skeleton.

The system must support the architecture required for:

1. deterministic checks
2. Codex execution
3. automated tests
4. AI evaluation
5. bounded repair loops
6. Git diff inspection
7. token usage monitoring

For v0.1, real OpenAI API calls and real Codex execution may remain behind interfaces or mocks. The dashboard and orchestration skeleton must work without API credentials.

## Non-negotiable Principles

### Deterministic First

Do not make Codex the default path.

Intended workflow:

```text
Task
 ↓
Deterministic Check
 ├─ PASS → Complete
 └─ FAIL
      ↓
    Triage
      ↓
    CODE_FIX only
      ↓
    Codex
```

### Strict Role Separation

Architect:
- creates structured work orders
- defines goal, scope, and acceptance criteria
- does not modify code

Codex Builder:
- modifies only allowed files
- makes the smallest change
- runs specified tests
- does not redefine goals
- does not make final acceptance decisions
- does not push to main

Evaluator:
- evaluates results and relevant diff
- returns only PASS / REPAIR / HUMAN_REVIEW
- does not modify code

### Structured Contracts

Implement Pydantic models or equivalent structured schemas for at least:

- WorkOrder
- ExecutionResult
- TestResult
- EvaluationResult
- TokenUsage
- RunState

Do not rely on uncontrolled conversational history between agents.

## Context Broker

Implement an abstraction that assembles the smallest sufficient context for Codex/Evaluator.

A task context should normally include only:

- task ID
- goal
- acceptance criteria
- allowed files
- relevant error excerpt
- relevant diff
- necessary configuration
- test command
- retry number

Do not routinely send whole repositories, complete logs, or unrelated history.

## Token Budget

Implement configuration-based token budgets with these initial defaults:

```yaml
codex:
  daily_input_tokens: 300000
  daily_output_tokens: 50000
  task_input_tokens: 40000
  task_output_tokens: 10000
  max_retry: 2

evaluator:
  daily_input_tokens: 150000
  daily_output_tokens: 20000
```

Required decisions:

```text
ALLOWED
TASK_BUDGET_EXCEEDED
DAILY_BUDGET_EXCEEDED
RETRY_LIMIT_EXCEEDED
```

Never silently exceed a configured limit.

## State Machine

Implement at least:

```text
IDLE
PLANNING
PRECHECK
RUNNING_TEST
TRIAGE
CODEX_FIX
EVALUATING
COMPLETE
HUMAN_REVIEW
FAILED
STOPPED
```

Only the state manager may mutate workflow state.

Write tests for valid and invalid transitions.

## Git Safety

Create a Git Guard abstraction.

Never automatically push to `main`.

Block or reject destructive operations such as:

```text
git reset --hard
git clean -fd
git branch -D
```

Implement a Scope Guard that compares WorkOrder.allowed_files with actual changed files.

If out-of-scope files change, the workflow must escalate to HUMAN_REVIEW.

## Technology

Backend:
- Python 3.12
- FastAPI
- Uvicorn
- Pydantic

Frontend:
- HTML
- CSS
- Vanilla JavaScript

Do not add React.
Do not add Node.js build tooling.
Do not add Docker.

Initial state persistence:
- JSON files
- behind an interface so SQLite can replace it later

Default bind address:
- 127.0.0.1

## Target Repository Structure

Create approximately:

```text
backend/
  app.py

  orchestrator/
    engine.py
    state_machine.py

  agents/
    architect.py
    evaluator.py
    triage.py

  runners/
    codex.py
    pytest_runner.py
    benchmark.py

  control/
    context_broker.py
    token_budget.py
    scope_guard.py
    git_guard.py

  models/
    task.py
    result.py
    evaluation.py
    state.py

frontend/
  index.html
  app.js
  style.css

config/
  projects.example.yaml
  plan.example.yaml
  budget.yaml

schemas/
  work-order.schema.json
  evaluation.schema.json

state/
  .gitkeep

logs/
  .gitkeep

tests/

prompts/
  architect.md
  evaluator.md
  triage.md

requirements.txt
```

Minor changes are allowed if technically justified.

Avoid unnecessary abstraction.

## Dashboard

Create one main dashboard.

Top area must display:

```text
Week 1
Day 3 / 7

Overall Progress 58%
Day Progress 63%
```

Overall and Day progress must be visually distinct.

Current task must show separately:

```text
PC-014 Evidence Grounding
Task Progress 18 / 22 82%
Retry 1 / 2
```

Also display:

### Agent Activity

```text
Architect
Gate
Codex
Tests
Evaluator
```

### Daily Result Summary

```text
PASS
FAIL
REVIEW
```

### Evaluation Metrics

Metrics must be data-driven. Mock values may include:

- Groundedness
- Process Consistency
- Instruction Fit
- Information Capacity

### Codex Token Usage

Display:

- Input
- Cached Input
- Output
- Task Total
- Day Total
- Budget %

Make token use prominent.

### Day Progress

Display Day 0 through Day 7.

The current validation day must be obvious.

Day means Validation Day, not necessarily calendar day.

The model should be able to display both when available:

```text
Calendar Day 5
Validation Day 3
```

### Detail Areas

Provide sections or tabs for:

```text
Timeline
Codex
Evaluation
Tests
Diff
Tokens
Git
```

For v0.1 these may use mock/local state data where backend functionality is not complete.

## Progress Model

Maintain three independent values:

```text
overall_progress
day_progress
task_progress
```

All use 0..100.

Overall progress is based on plan/task completion, not wall-clock elapsed time.

## Timeline

Store structured audit events and render them in the dashboard.

Example:

```text
12:01:02 PC-014 test FAIL
12:01:02 Gate classified CODE_FIX
12:01:03 Context package built
12:01:04 Codex started
12:02:14 evaluator.py modified
12:02:17 pytest PASS
12:02:25 Evaluator PASS
12:02:25 Task COMPLETE
```

Do not rely only on text logs internally.

## Codex Runner

Implement Codex execution behind:

```text
backend/runners/codex.py
```

Design it to eventually execute:

```powershell
codex exec --json
```

The parser should support capturing, when available:

- input_tokens
- cached_input_tokens
- output_tokens

For v0.1, provide a mock runner so tests and dashboard work without Codex.

## External AI

Do not require API credentials to launch v0.1.

Architect, Evaluator, and Triage should be interfaces with mock implementations.

Secrets must never be committed.

Use environment variables for future credentials.

## Tests

Create useful tests for at least:

1. valid state transitions
2. forbidden state transitions
3. task token budget rejection
4. retry limit
5. allowed file validation
6. out-of-scope file detection
7. progress calculation
8. structured model validation

Tests must not require Codex or an OpenAI API key.

## Required v0.1 API Endpoints

At minimum:

```text
GET /api/status
GET /api/plan
GET /api/tasks
GET /api/timeline
GET /api/token-usage
POST /api/run/mock
```

## Acceptance Criteria

This command must start the server:

```powershell
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8765
```

Opening:

```text
http://127.0.0.1:8765
```

must display the dashboard.

The dashboard must display mock or persisted values for:

- Week
- Validation Day
- Overall progress
- Day progress
- Task progress
- Current state
- Agent activity
- PASS / FAIL / REVIEW
- Evaluation metrics
- Codex token usage
- Retry usage
- Day-by-day progress
- Timeline

The complete local test suite must pass without Codex and without API credentials.

## Implementation Discipline

Before modifying code:

1. inspect the repository
2. read `AGENTS.md`
3. read `docs/ARCHITECTURE.md`
4. inspect only files relevant to the current phase

Do not perform a broad repository rewrite.

Do not add speculative features.

Do not implement GitHub Actions yet.

Do not implement automatic PR creation yet.

Do not implement production authentication yet.

Do not integrate LocalLLM-Lab directly yet.

Build the Control Center skeleton first.

## Token-conscious Codex Behavior

Your own implementation process must follow this project's philosophy.

Prefer:

- targeted file inspection
- targeted search
- bounded command output
- small diffs
- focused tests

Avoid:

- repeatedly reading large files
- dumping complete logs into context
- restating the full requirements after they have been read
- broad repository-wide exploration after the relevant files are known

If a test fails, investigate the relevant failure first.

## Final Verification

Before stopping:

1. run the complete local test suite
2. verify imports
3. verify FastAPI startup
4. verify static frontend serving
5. verify the mock workflow
6. inspect `git diff`
7. check for accidental secrets
8. confirm no unrelated files changed

Do not push.
Do not merge.
Do not create a pull request.

## Final Response Format

Return only:

```text
STATUS:
IMPLEMENTED / PARTIAL / BLOCKED

TESTS:
<result>

SERVER:
<startup result>

FILES_CHANGED:
<list>

KNOWN_LIMITATIONS:
<short list>

NEXT_RECOMMENDED_STEP:
<one item>
```
