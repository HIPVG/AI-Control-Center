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
| M6 | Real Architect readiness | M2–M5 | plan, mock request/parser/error tests, external checklist | REAL_ARCHITECT_SINGLE_STEP_VALIDATION | HUMAN_GATE |
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
| M18 | Dashboard v2 | M17 external validation | consume Day queue, role calls, routing, tokens, review, timeline | no | ROADMAP |

M10 is deliberately non-blocking: a real semantic task must not be invented.

Codex Core is the normal execution architecture. OpenAI Architect and Evaluator
adapters are retained as explicit optional independent providers. Session reuse
is deliberately deferred: current one-call-per-role/task execution preserves
reproducibility and audit boundaries until measured cache savings justify a
bounded, resettable session policy.
