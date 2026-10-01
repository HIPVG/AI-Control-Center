# AI-Control-Center-Day6-Bounded-RC1 Manifest

## Identity

- **Artifact name/version:** `AI-Control-Center-Day6-Bounded-RC1`
- **Artifact type:** deterministic local-only source ZIP
- **Source commit:** `656711367ed837ddbb75e6df65234a955e44900d`
- **Source tree:** `fb22e40933c49b336b70599bd7e559d2caa7a841`
- **Generated at:** `2026-10-01T07:36:30.8772999Z`
- **Local managed path:**
  `C:\AI-Control-Center\state\release-artifacts\AI-Control-Center-Day6-Bounded-RC1\AI-Control-Center-Day6-Bounded-RC1.zip`
- **Archive bytes:** `288116`
- **Archive SHA-256:**
  `6453a213b0a48b827bbbc83ec2bdf1036515e6d857451473402cae3fb79f6714`
- **File count:** `124`
- **Sorted relative-inventory SHA-256:**
  `9d12fd7f2ae2fdc96f246162762922656130d2dbbab94394397023ca2aa3a8c8`

The inventory hash is calculated from UTF-8 without BOM, one sorted relative path
per LF-terminated line.

## Packaging boundary

Included content is drawn directly from the fixed commit and is limited to runtime
source, frontend assets, schemas, safe tracked configuration, the loopback launchers,
bounded role prompts and essential operating documents. The archive prefix is
`AI-Control-Center-Day6-Bounded-RC1/`.

Explicitly excluded:

- working-tree changes and all untracked content;
- `tests/`, `output/`, `poc/`, `.git/` and development caches;
- runtime state and logs other than their `.gitkeep` placeholders;
- `docs/review-evidence/`, `docs/review-records/` and other historical review files;
- `config/preflight-authorities/` and previous human grants;
- `config/external-review.json`; and
- binary release publication or GitHub Release metadata.

The tracked `config/runtime.yaml` remains `mode: mock`. This is a source candidate,
not an operational or externally distributed release.

## Reproduction

Run `git archive --format=zip` against the fixed commit with prefix
`AI-Control-Center-Day6-Bounded-RC1/` and these exact source selections:

```text
AGENTS.md
README.md
requirements.txt
backend
frontend
schemas
scripts/start.ps1
scripts/start_dev.ps1
prompts/architect.md
prompts/evaluator.md
prompts/triage.md
config/budget.example.yaml
config/budget.yaml
config/discovery.example.yaml
config/discovery.yaml
config/experiments.yaml
config/faults.yaml
config/local-llm-day-actions.json
config/local-llm-repair-catalog.json
config/local_llm_day_program.yaml
config/model_profiles.yaml
config/orchestration.yaml
config/plan.example.yaml
config/plans.yaml
config/projects.example.yaml
config/projects.yaml
config/runtime.example.yaml
config/runtime.yaml
config/tasks.example.yaml
config/tasks.yaml
docs/ARCHITECTURE.md
docs/AUTONOMOUS_DAY.md
docs/DAILY_OPERATION.md
docs/DAY_RUNNER_EXECUTION_SPEC.md
docs/GOAL_TO_PLAN.md
docs/MODEL_ROUTING.md
docs/WORKING_RULES.md
logs/.gitkeep
state/.gitkeep
```

## Exact file inventory

```text
AGENTS.md
backend/__init__.py
backend/agents/__init__.py
backend/agents/architect.py
backend/agents/day_providers.py
backend/agents/evaluator.py
backend/agents/triage.py
backend/app.py
backend/control/__init__.py
backend/control/config_layers.py
backend/control/context_broker.py
backend/control/daily_operation.py
backend/control/day_action_executor.py
backend/control/day_action_registry.py
backend/control/day_git.py
backend/control/day_research.py
backend/control/day_state_machine.py
backend/control/evidence_completion.py
backend/control/evidence_registry.py
backend/control/experiments.py
backend/control/external_review.py
backend/control/faults.py
backend/control/git_completion.py
backend/control/git_guard.py
backend/control/goal_policy.py
backend/control/human_decision.py
backend/control/local_llm_day_program.py
backend/control/local_ollama_repair.py
backend/control/local_runtime.py
backend/control/model_router.py
backend/control/next_action.py
backend/control/orchestration.py
backend/control/plans.py
backend/control/preflight_authority.py
backend/control/projects.py
backend/control/repair_recovery.py
backend/control/retained_evidence.py
backend/control/review_continuation.py
backend/control/review_control.py
backend/control/reviewer_bus.py
backend/control/reviewer_files.py
backend/control/reviewer_recovery.py
backend/control/run_composition.py
backend/control/run_execution_composition.py
backend/control/run_product_composition.py
backend/control/run_projection_composition.py
backend/control/run_read_model.py
backend/control/run_store.py
backend/control/run_telemetry_store.py
backend/control/scope_guard.py
backend/control/solution_catalog.py
backend/control/task_discovery.py
backend/control/tasks.py
backend/control/token_budget.py
backend/control/week1_program.py
backend/models/__init__.py
backend/models/audit.py
backend/models/day.py
backend/models/evaluation.py
backend/models/experiment.py
backend/models/git_completion.py
backend/models/goal.py
backend/models/local_llm_day.py
backend/models/local_runtime.py
backend/models/model_routing.py
backend/models/next_action.py
backend/models/orchestration.py
backend/models/result.py
backend/models/runtime.py
backend/models/state.py
backend/models/task.py
backend/models/week1.py
backend/models/zero_touch.py
backend/orchestrator/__init__.py
backend/orchestrator/day_runner.py
backend/orchestrator/engine.py
backend/orchestrator/progress.py
backend/orchestrator/state_machine.py
backend/runners/__init__.py
backend/runners/benchmark.py
backend/runners/codex.py
backend/runners/pytest_runner.py
config/budget.example.yaml
config/budget.yaml
config/discovery.example.yaml
config/discovery.yaml
config/experiments.yaml
config/faults.yaml
config/local_llm_day_program.yaml
config/local-llm-day-actions.json
config/local-llm-repair-catalog.json
config/model_profiles.yaml
config/orchestration.yaml
config/plan.example.yaml
config/plans.yaml
config/projects.example.yaml
config/projects.yaml
config/runtime.example.yaml
config/runtime.yaml
config/tasks.example.yaml
config/tasks.yaml
docs/ARCHITECTURE.md
docs/AUTONOMOUS_DAY.md
docs/DAILY_OPERATION.md
docs/DAY_RUNNER_EXECUTION_SPEC.md
docs/GOAL_TO_PLAN.md
docs/MODEL_ROUTING.md
docs/WORKING_RULES.md
frontend/app.js
frontend/index.html
frontend/reviewer-status.js
frontend/run-status.js
frontend/style.css
logs/.gitkeep
prompts/architect.md
prompts/evaluator.md
prompts/triage.md
README.md
requirements.txt
schemas/evaluation.schema.json
schemas/work-order.schema.json
scripts/start_dev.ps1
scripts/start.ps1
state/.gitkeep
```

## Validation result

- two independent `git archive` generations produced the same SHA-256;
- ZIP open and extraction succeeded;
- extracted file count: `124`;
- archive-prefix violations: `0`;
- forbidden-file matches: `0`;
- credential-pattern matches: `0`; and
- tracked runtime mode: `mock`.

No application, service, Watcher, Day/Go, model or product test was run. The manifest
proves RG-01 artifact identity and content reproducibility only.
