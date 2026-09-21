# Development roadmap

This is the authoritative implementation progression for the current task
branch. Status is tracked in `docs/DEV_PROGRESS.json`.

| ID | Title | Dependencies | Acceptance / tests | Human gate | Status |
| --- | --- | --- | --- | --- | --- |
| M0 | Core execution foundation | — | deterministic execution controls | no | COMPLETE |
| M1 | ModelRouter | M0 | policy, budgets, audit tests | no | COMPLETE |
| M2 | Router/provider binding | M1 | routed OpenAI model/reasoning request tests | no | COMPLETE |
| M3 | Deterministic no-AI path | M0 | no speculative Codex route | no | COMPLETE |
| M4 | Multi-task single-step | M0 | paused/complete progress tests | no | COMPLETE |
| M5 | Mock continuous Day | M4 | bounded continuous tests | no | COMPLETE |
| M6 | Real Architect readiness | M2–M5 | plan, mock request/parser/error tests, external checklist | REAL_ARCHITECT_SINGLE_STEP_VALIDATION | COMPLETE |
| M7 | Provider configuration validation | M2 | credentials fail closed; no mock fallback; telemetry matches route | no | COMPLETE |
| M8 | Runtime/source configuration separation | M0 | local-overrides-defaults precedence tests | no | COMPLETE |
| M9 | Development runtime experience | M0 | launcher binding/reload tests | no | COMPLETE |
| M10 | Real Evaluator readiness | M2 | safe semantic task inspection | WAITING_FOR_REAL_SEMANTIC_TASK | HUMAN_GATE |
| M11 | Persistent resume/crash safety | M4 | interrupted Day becomes explicit PAUSED state | no | COMPLETE |
| M12 | Human Review operational data | M4 | review includes routing/failure fields | no | COMPLETE |
| M13 | Observability/token efficiency | M1 | role/profile accounting and no-AI audit tests | no | COMPLETE |
| M14 | External validation checklist | M6 | concise proven/remaining checklist | no | COMPLETE |
| M15 | UI-readiness API data | M4 | Day state exposes task, routing, tokens, review queue | no | COMPLETE |
| M16 | Real provider structured-output compatibility | M2, M6 | strict DTO schema, request shape, output mapping, sanitized error tests | no | COMPLETE |
| M17 | Codex Core architecture | M0, M1, M4 | read-only structured Codex Architect/Reviewer roles, API-independent default plan, role telemetry tests | CODEX_ARCHITECT_SINGLE_STEP_VALIDATION | COMPLETE |
| M18 | Dashboard v2 | M17 external validation | real Day state, routing, tokens, queue visible and executable from UI | DASHBOARD_V2_EXTERNAL_VALIDATION | COMPLETE |
| M19 | Architect context efficiency | M17 validation telemetry | isolated non-repository role workspace, compact context, character telemetry | no | COMPLETE |
| M20 | Real continuous Codex-Core Day | M18 | trusted multi-task Day completes end-to-end without per-task human action | REAL_CODEX_CORE_CONTINUOUS_VALIDATION | IN_PROGRESS |
| M21 | Exception-driven escalation | M20 | auto-resolve/retry/replan routine failure classes; human only for true authority/external boundaries | ESCALATION_POLICY_EXTERNAL_VALIDATION | ROADMAP |
| M22 | PowerShell-free daily operation | M18 | auto-start/service behavior and dashboard start/resume/stop/health controls | ZERO_COMMAND_DAILY_OPERATION_VALIDATION | ROADMAP |
| M23 | Goal-to-Plan | M21 | bounded goal intake → Codex plan → deterministic policy validation → execution | GOAL_TO_PLAN_EXTERNAL_VALIDATION | ROADMAP |
| M24 | Self-repair and bounded replan | M21, M23 | classify failure → retry/repair/review/replan automatically within limits | AUTONOMOUS_RECOVERY_VALIDATION | ROADMAP |
| M25 | Automated Git completion | M24 | verified work can commit/push agent branch and prepare PR; no automatic main merge | AUTO_GIT_PR_VALIDATION | ROADMAP |
| M26 | Zero-Touch Control Loop | M20–M25 | one goal/start → complete or genuine escalation, with no routine relay/PowerShell | ZERO_TOUCH_EXTERNAL_VALIDATION | ROADMAP |

M10 is deliberately non-blocking: a real semantic task must not be invented.

The strategic target is defined in `docs/ZERO_TOUCH_CONTROL_LOOP.md`.
Autonomous development reasoning selection is governed by `docs/DEVELOPMENT_REASONING_POLICY.md`; Terra / Medium is the normal default, with bounded self-selected escalation/de-escalation.
Development priority is now autonomy, reliability, recovery, and observability.
Token optimization remains measured but is secondary unless it becomes an actual
operational constraint.

Codex Core remains the normal execution architecture. OpenAI Architect and
Evaluator adapters remain optional independent providers. Human attention is an
exception boundary, not a routine workflow stage.

External Dashboard v2 validation passed: the UI successfully executed the real
Codex-Core plan, displayed PAUSED progress at 33.33%, task state, ModelRouter
selection, token telemetry, and no Human Review item.
