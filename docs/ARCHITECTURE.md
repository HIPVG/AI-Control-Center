# AI Control Center v1.0 Architecture

## 1. Purpose

AI Control Center is a local, Windows-first web application that orchestrates AI-assisted engineering workflows while minimizing Codex token consumption and keeping human approval at the final decision boundary.

Primary goals:

1. Minimize Codex usage through deterministic gating.
2. Separate planning, building, evaluation, and approval responsibilities.
3. Support day-based autonomous validation workflows.
4. Prevent unbounded retries, scope expansion, and unsafe Git operations.
5. Make progress, token usage, decisions, and evidence visible in one dashboard.

The target operating model is:

```text
Plan
  ↓
Deterministic pre-check
  ↓
Codex only when needed
  ↓
Automated tests
  ↓
Independent evaluation
  ↓
Bounded repair loop
  ↓
Human approval
```

---

## 2. Core Design Principles

### 2.1 Deterministic First

Codex is not the default executor.

If Python, pytest, configuration validation, static checks, or deterministic rules can make the decision, use them first.

```text
Task
  ↓
Deterministic Check
  ├─ PASS → Complete
  └─ FAIL
       ↓
     Triage
       ↓
     CODE_FIX?
       ├─ NO → Human / deterministic path
       └─ YES → Codex
```

### 2.2 Strict Role Separation

The system separates responsibilities into distinct roles.

#### Architect

Responsibilities:

- decompose goals into tasks
- define acceptance criteria
- define allowed file scope
- decide whether Codex is required
- create structured work orders

The Architect must not modify source code.

#### Codex Builder

Responsibilities:

- implement only the requested change
- stay within allowed files
- make the smallest reasonable change
- run specified tests
- return a structured result

Codex must not:

- redefine project goals
- change Day plans
- modify unrelated files
- alter tests merely to obtain a PASS
- push directly to `main`
- make final acceptance decisions

#### Evaluator

Responsibilities:

- inspect deterministic test results
- inspect the relevant Git diff
- evaluate semantic quality
- return exactly one decision:
  - `PASS`
  - `REPAIR`
  - `HUMAN_REVIEW`

The Evaluator must not modify code.

#### Human

The human remains the final authority for:

- PR creation / merge approval
- schema changes
- plan changes
- test-definition changes
- data deletion
- budget overrides
- retry overrides

### 2.3 Structured Communication, Not Free-form Agent Chat

Agents exchange structured artifacts instead of large conversational histories.

```text
Architect
  ↓
work-order.json
  ↓
Codex
  ↓
execution-result.json
  ↓
Test Runner
  ↓
test-result.json
  ↓
Evaluator
  ↓
evaluation.json
```

This is a core control mechanism for role separation and token efficiency.

### 2.4 Enforce Rules in Code

Prompts and `AGENTS.md` guide behavior, but the Control Center must enforce critical rules in code.

Examples:

- state machine controls workflow transitions
- Scope Guard validates changed files
- Git Guard blocks unsafe commands
- Budget Manager blocks token overrun
- Retry Guard prevents endless repair loops
- test runner determines deterministic pass/fail

---

## 3. System Architecture

```text
                  ┌─────────────────────┐
                  │        Human        │
                  │   Approval / Goal   │
                  └──────────┬──────────┘
                             │
                  ┌──────────▼──────────┐
                  │ AI Control Center   │
                  │ FastAPI + HTML/JS   │
                  └──────────┬──────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
 Context Broker         State Manager        Budget Manager
        │                    │                    │
        └────────────────────┼────────────────────┘
                             │
                  ┌──────────▼──────────┐
                  │     Architect       │
                  └──────────┬──────────┘
                             │ WorkOrder
                             ▼
                  ┌─────────────────────┐
                  │ Deterministic Gate  │
                  │ Python / pytest     │
                  └──────────┬──────────┘
                             │ FAIL only
                             ▼
                  ┌─────────────────────┐
                  │    Codex Builder    │
                  │    codex exec       │
                  └──────────┬──────────┘
                             │
                             ▼
                  ┌─────────────────────┐
                  │     Test Runner     │
                  └──────────┬──────────┘
                             │
                             ▼
                  ┌─────────────────────┐
                  │      Evaluator      │
                  └──────────┬──────────┘
                       PASS / REPAIR /
                       HUMAN_REVIEW
```

---

## 4. Context Broker

The Context Broker is the primary token-control component.

Its responsibility is to assemble the smallest sufficient context package for Codex and evaluators.

A Codex context package should normally contain only:

- task ID
- goal
- acceptance criteria
- allowed files
- relevant error excerpt
- relevant diff
- necessary configuration
- test command
- retry number

Avoid routinely sending:

- the whole repository
- complete historical logs
- unrelated source files
- previous unrelated agent conversations
- large documentation files unless explicitly needed

Example task package:

```text
TASK: PC-014-FIX-01

Goal:
Fix missing evidence ID validation.

Allowed files:
- src/evaluator.py
- src/evidence_resolver.py

Forbidden:
- benchmark data
- schema changes
- unrelated refactoring

Failure:
PC-014 expected evidence_id >= 1
actual = 0

Relevant log:
<bounded excerpt only>

Test:
pytest tests/test_pc014.py

Return:
STATUS
FILES_CHANGED
TEST_RESULT
SUMMARY
```

Context size should be recorded when practical.

---

## 5. State Machine

Workflow state is centrally controlled.

Required states:

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

Only the State Manager may transition workflow state.

Typical flow:

```text
IDLE
 ↓
PLANNING
 ↓
PRECHECK
 ↓
RUNNING_TEST
 ├─ PASS → COMPLETE
 └─ FAIL
      ↓
    TRIAGE
      ├─ CONFIG / DATA / PLAN issue → HUMAN_REVIEW
      └─ CODE issue
           ↓
        CODEX_FIX
           ↓
        RUNNING_TEST
           ↓
        EVALUATING
          ├─ PASS → COMPLETE
          ├─ REPAIR → retry gate → CODEX_FIX
          └─ HUMAN_REVIEW
```

---

## 6. Token Budget Manager

Token use is a governed resource.

Initial default configuration:

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

Required budget decisions:

```text
ALLOWED
TASK_BUDGET_EXCEEDED
DAILY_BUDGET_EXCEEDED
RETRY_LIMIT_EXCEEDED
```

The system must never silently exceed configured limits.

Priority order for token reduction:

1. Do not call Codex.
2. Reduce context.
3. Reduce retries.
4. Reduce output verbosity.
5. Reuse cache where available.

Model downgrade is not the first optimization lever.

---

## 7. Codex Execution Strategy

Default policy:

```text
1 WorkOrder = 1 Codex execution
```

Do not use a long-lived Codex session by default.

Benefits:

- smaller context
- lower cross-task contamination
- easier token accounting
- better reproducibility
- easier auditability

A retry may reuse narrowly scoped context for the same task, but unrelated tasks should not share conversational history.

The Codex runner should isolate command construction in one component and eventually support:

```powershell
codex exec --json
```

When available, capture:

- input tokens
- cached input tokens
- output tokens
- task duration
- exit status
- structured result

---

## 8. Structured Contracts

### 8.1 WorkOrder

Example:

```json
{
  "task_id": "PC-014-FIX-01",
  "goal": "Restore evidence validation",
  "task_type": "code_fix",
  "priority": "normal",
  "allowed_files": [
    "src/evaluator.py",
    "src/evidence_resolver.py"
  ],
  "acceptance_tests": [
    "pytest tests/test_pc014.py"
  ],
  "max_retry": 2,
  "needs_codex": true
}
```

### 8.2 ExecutionResult

Example:

```json
{
  "status": "completed",
  "files_changed": [
    "src/evaluator.py"
  ],
  "tests_run": [
    "pytest tests/test_pc014.py"
  ],
  "test_result": "pass",
  "summary": "Added missing evidence ID validation."
}
```

### 8.3 EvaluationResult

Example:

```json
{
  "decision": "PASS",
  "score": {
    "groundedness": 4.8,
    "process_consistency": 4.7,
    "instruction_fit": 4.9
  },
  "blocking_issues": [],
  "repair_instruction": null
}
```

Evaluator decisions are limited to:

```text
PASS
REPAIR
HUMAN_REVIEW
```

No ambiguous final state such as "probably OK" is allowed.

---

## 9. Git Safety

AI Control Center is a separate repository from target repositories.

Expected layout:

```text
HIPVG/
├─ LocalLLM-Lab
└─ AI-Control-Center
```

Target repositories are configured, not hard-coded.

Example:

```yaml
projects:
  local_llm_lab:
    path: C:\LocalLLM-Lab
    default_branch: main

  manufacturing_app:
    path: C:\Manufacturing-App
    default_branch: main
```

Codex work must occur on a task branch:

```text
agent/<task-name>
```

Direct automated push to `main` is prohibited.

Forbidden destructive Git commands include:

```text
git reset --hard
git clean -fd
git branch -D
```

### Scope Guard

Before accepting a Codex result:

```text
WorkOrder.allowed_files
        vs
Actual Git changed files
```

Any out-of-scope change moves the task to:

```text
HUMAN_REVIEW
```

---

## 10. Day and Progress Model

Day number is a validation phase, not necessarily a calendar day.

Support both:

```text
Validation Day 3
Calendar Day 5
```

Progress is intentionally separated into three levels:

- Overall Progress
- Day Progress
- Current Task Progress

Do not collapse them into one percentage.

Example plan:

```yaml
plan:
  name: LocalLLM Week1 Validation
  week: 1

  days:
    0:
      title: Environment Setup
    1:
      title: Baseline
    2:
      title: Instruction Adaptability
    3:
      title: Process Consistency
    4:
      title: Information Capacity
    5:
      title: Model Comparison
    6:
      title: Integrated Scenario
    7:
      title: Review
```

Overall progress should be based on planned task completion, not elapsed time.

---

## 11. Dashboard Requirements

Main dashboard header:

```text
Week 1
Day 3 / 7

Overall Progress
█████████████████░░░░░░░░░ 58%

Day Progress
███████████████████░░░░░░░ 63%
```

Current Task section:

```text
PC-014 Evidence Grounding
Task Progress 18 / 22  82%
Retry 1 / 2
```

Agent Activity:

```text
Architect   DONE
Gate        DONE
Codex       RUNNING
Tests       WAITING
Evaluator   WAITING
```

Daily summary:

```text
PASS
FAIL
REVIEW
```

Evaluation metrics are data-driven and may include:

- Groundedness
- Process Consistency
- Instruction Fit
- Information Capacity

Codex usage panel must show:

- Input
- Cached Input
- Output
- Task Total
- Day Total
- Budget percentage

Day progress should display Day 0 through Day 7 and clearly identify the current Validation Day.

Detail sections / tabs:

- Timeline
- Codex
- Evaluation
- Tests
- Diff
- Tokens
- Git

---

## 12. Audit Timeline

Every meaningful event must be stored as structured data and rendered in a human-readable timeline.

Example:

```text
12:01:02 PC-014 test FAIL
12:01:02 Gate classified CODE_FIX
12:01:03 Context package created
12:01:04 Codex started
12:02:14 evaluator.py modified
12:02:17 pytest PASS
12:02:25 Evaluator PASS
12:02:25 Task COMPLETE
```

The system must preserve enough evidence to answer:

> Why did the system make this change?

---

## 13. Safety Guards

### Scope Guard

Reject or escalate out-of-scope file changes.

### Git Guard

Block unsafe Git operations and direct automated writes to `main`.

### Command Guard

Prefer explicit command allow-lists for automated execution.

### Budget Guard

Stop or escalate before configured token limits are exceeded.

### Retry Guard

Default maximum retry count:

```text
2
```

Beyond the limit:

```text
HUMAN_REVIEW
```

---

## 14. Technology Constraints

Backend:

- Python 3.12
- FastAPI
- Uvicorn
- Pydantic

Frontend:

- HTML
- CSS
- Vanilla JavaScript

Do not add React for v0.x.

Do not add Node.js unless technically unavoidable.

Do not add Docker for v0.x.

Initial persistence:

- JSON files behind a persistence interface

Future option:

- SQLite

Primary platform:

- Windows 11
- PowerShell 7

Default server binding:

```text
127.0.0.1
```

---

## 15. Repository Structure

Target structure:

```text
AI-Control-Center/
│
├─ backend/
│  ├─ app.py
│  ├─ orchestrator/
│  │  ├─ engine.py
│  │  └─ state_machine.py
│  ├─ agents/
│  │  ├─ architect.py
│  │  ├─ evaluator.py
│  │  └─ triage.py
│  ├─ runners/
│  │  ├─ codex.py
│  │  ├─ pytest_runner.py
│  │  └─ benchmark.py
│  ├─ control/
│  │  ├─ context_broker.py
│  │  ├─ token_budget.py
│  │  ├─ scope_guard.py
│  │  └─ git_guard.py
│  └─ models/
│     ├─ task.py
│     ├─ result.py
│     ├─ evaluation.py
│     └─ state.py
│
├─ frontend/
│  ├─ index.html
│  ├─ app.js
│  └─ style.css
│
├─ config/
│  ├─ projects.example.yaml
│  ├─ plan.example.yaml
│  └─ budget.yaml
│
├─ prompts/
│  ├─ architect.md
│  ├─ evaluator.md
│  ├─ triage.md
│  └─ CODEX_BOOTSTRAP.md
│
├─ schemas/
│  ├─ work-order.schema.json
│  └─ evaluation.schema.json
│
├─ state/
├─ logs/
├─ tests/
├─ docs/
│  └─ ARCHITECTURE.md
│
├─ AGENTS.md
├─ README.md
└─ requirements.txt
```

---

## 16. Implementation Phases

### v0.1: Control Center Skeleton

Implement:

- FastAPI server
- dashboard shell
- state manager
- mock Codex runner
- test runner abstraction
- Git diff abstraction
- token meter
- mock workflow

Goal:

```text
Run → Mock Codex → Test → Result
```

No OpenAI API credentials required.

### v0.2: Architect and Evaluator

Add:

- Architect interface
- Evaluator interface
- structured output schemas
- Context Broker
- real API adapters behind interfaces

Goal:

```text
Plan → Build → Evaluate → Repair
```

### v0.3: Autonomous Day Operation

Add:

- Day plan
- overall/day/task progress
- Budget Manager
- bounded auto-retry
- Scope Guard
- stronger Git Guard

### v1.0: GitHub and Multi-project

Add:

- GitHub PR workflow
- selective Codex review
- multiple target projects
- history comparison
- model comparison

---

## 17. v0.1 Acceptance Criteria

The following command must start the server:

```powershell
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8765
```

Opening:

```text
http://127.0.0.1:8765
```

must display the dashboard.

Required dashboard data:

- Week
- Validation Day
- Overall Progress
- Day Progress
- Task Progress
- Current State
- Agent Activity
- PASS / FAIL / REVIEW
- Evaluation metrics
- Codex token usage
- Retry usage
- Day-by-day progress
- Timeline

Required initial endpoints:

```text
GET /api/status
GET /api/plan
GET /api/tasks
GET /api/timeline
GET /api/token-usage
POST /api/run/mock
```

Tests must run without Codex and without an OpenAI API key.

---

## 18. Operating Principle

The system must preserve this division of responsibility:

```text
ChatGPT / Architect = Think and structure
Codex               = Build
Python / tests      = Determine objective facts
Git                  = Record
Human                = Decide
```

AI Control Center exists to govern who may do what, with what context, within what budget, and with what evidence.
