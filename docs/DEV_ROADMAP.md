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
| M20 | Real continuous Codex-Core Day | M18 | trusted multi-task Day completes end-to-end without per-task human action | REAL_CODEX_CORE_CONTINUOUS_VALIDATION | COMPLETE |
| M21 | Exception-driven escalation | M20 | auto-resolve/retry/replan routine failure classes; human only for true authority/external boundaries | BATCH_WITH_M22_EXTERNAL_VALIDATION | COMPLETE |
| M22 | Real LocalLLM experiment integration | M21 implementation | run an existing trusted LocalLLM-Lab experiment through Control Center, preserve experiment-vs-code semantics, capture artifacts/telemetry | ESCALATION_AND_REAL_LOCAL_LLM_VALIDATION | COMPLETE |
| M23 | PowerShell-free daily operation | M18, M22 | auto-start/service behavior and dashboard start/resume/stop/health controls | ZERO_COMMAND_DAILY_OPERATION_VALIDATION | COMPLETE |
| M24 | Goal-to-Plan | M21, M22 | bounded goal intake → Codex plan → deterministic policy validation → execution | GOAL_TO_PLAN_EXTERNAL_VALIDATION | COMPLETE |
| M25 | Self-repair, bounded replan, and autonomous next action | M21, M24 | recover/replan failures within limits and continue the obvious trusted success path without another typed Goal | AUTONOMOUS_RECOVERY_AND_CONTINUE_VALIDATION | COMPLETE |
| M26 | Automated Git completion | M25 | verified work can commit/push agent branch and prepare PR; no automatic main merge | AUTO_GIT_PR_VALIDATION | COMPLETE |
| M27 | Zero-Touch Control Loop | M20–M26 | one goal/start → complete or genuine escalation, with no routine relay/PowerShell | ZERO_TOUCH_EXTERNAL_VALIDATION | IN_PROGRESS |
| M28 | Japanese Dashboard / UX polish | M27 | localize Dashboard labels/messages while preserving English API/state/audit identifiers | JAPANESE_UI_EXTERNAL_VALIDATION | ROADMAP |

M10 is deliberately non-blocking: a real semantic task must not be invented.

The strategic target is defined in `docs/ZERO_TOUCH_CONTROL_LOOP.md`.
Autonomous success-path continuation is defined in `docs/AUTONOMOUS_NEXT_ACTION.md`; free-form Goal entry is now an exception path for changing direction rather than the normal continuation mechanism.
Real LocalLLM experiment integration is defined in `docs/REAL_LOCAL_LLM_INTEGRATION.md` and is intentionally prioritized immediately after M21 so autonomy is exercised against real experiment behavior early.
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


External Real Continuous validation passed on 2026-09-22:
- resumed the trusted Codex-Core Day from 33.33% without rerunning PC-001-A;
- completed PC-001-C and PC-002-A as COMPLETE_NO_CHANGE;
- reached COMPLETE / 100%;
- Architect calls: 3 total;
- Builder calls: 0;
- Independent Evaluator calls: 0;
- Human Review: none;
- three deterministic tasks avoided Builder AI work;
- Architect input: 55,344; uncached input: 37,168; output: 236.

This closes M20 and advances development to M21 Exception-driven escalation.


To reduce human relay work, M21 external validation is intentionally batched with
M22 external validation. M21 implementation may proceed into M22 without waiting
for a separate human stop. The combined external validation should verify both:

- controlled transient Architect recovery and typed external-action escalation;
- one trusted real LocalLLM experiment executed through Control Center.

This batching does not waive either acceptance criterion; it only removes an
unnecessary intermediate human interruption.


External combined M21/M22 validation passed on 2026-09-22:
- isolated transient Architect validation completed successfully on the normal server;
- isolated missing-runtime validation showed HUMAN_REVIEW state with typed EXTERNAL_ACTION_REQUIRED, retry count 0, action "No retry", and normal Day unchanged;
- trusted LocalLLM experiment completed through the existing LocalLLM-Lab runner;
- engine/model: ollama / qwen3-8b-q4:latest;
- responses: 4, successes: 4, failures: 0;
- result artifact reference was recorded under LocalLLM-Lab results/process-consistency;
- Builder invoked: false;
- classification: completed.

This closes M21 and M22 and advances development to M23 PowerShell-free daily operation.


M23 retry implementation is ready for external validation:
- the Dashboard reports bounded server health and user-local automatic-start state;
- it can explicitly enable the fixed, non-overwriting Windows logon task without
  accepting browser-supplied commands or paths;
- Dashboard controls cover configured Day start, continuous resume, stop, and
  trusted state refresh;
- the automatic-start choice is audit-recorded and fails closed if Windows Task
  Scheduler is unavailable;
- the external check requires only Dashboard interaction plus one normal
  Windows sign-in to observe automatic server startup.

The first M23 external attempt found a launcher working-directory defect: a
Scheduled Task starts PowerShell outside the repository root, so Uvicorn could
not import `backend.app`. The first retry then exposed multiple `python.exe`
candidates being returned as an array at the launch boundary. The next retry
resolves the root from the launcher path, deterministically selects one verified
Python 3.12 executable, and records bounded startup codes/reason/type fields
for browser/log inspection.


External M23 validation is accepted as PASSED for daily operation:
- after one-time Windows Task Scheduler bootstrap, the Control Center starts at user sign-in;
- http://127.0.0.1:8000 is available without manually launching PowerShell;
- normal Day start/resume/stop and health remain Dashboard-driven.

Known residual defect / non-blocking backlog:
- the Dashboard "Enable automatic startup" registration path did not reliably create the Windows task on this machine;
- one-time manual Task Scheduler registration was used to bootstrap autostart;
- this does not block zero-command daily use, but the Dashboard registration path should be repaired later without delaying M24 Goal-to-Plan.


M24 implementation is ready for external validation. A browser goal is bounded,
digest-audited, policy-validated, and mapped only to the configured trusted
LocalLLM experiment. Proposal and execution are separate actions; no goal can
grant new authority or alter experiment configuration.


External M24 Goal-to-Plan validation passed on 2026-09-22:
- bounded goal "Run the trusted LocalLLM process consistency experiment" was accepted;
- proposal status was PROPOSED with TRUSTED_LOCAL_LLM_EXPERIMENT_MATCH;
- executing the proposed plan ran the configured trusted LocalLLM experiment;
- the LocalLLM result was recorded and Builder remained false;
- a forbidden authority-expanding goal requesting model download was rejected before execution.

This closes M24 and advances development to M25 Self-repair and bounded replan.


M25 implementation is ready for external validation:
- the Dashboard derives and displays a trusted next action from recorded state;
- **Continue autonomously** can execute only the configured LocalLLM experiment,
  without a new Goal or browser-supplied authority;
- runtime/environment outcomes require explicit external attention rather than
  being retried or routed to Builder;
- validation-only controls show one automatic Architect retry, one bounded
  invalid-task replan, and missing-runtime external action evidence without
  changing normal Day state.


External M25 validation passed on 2026-09-22:
- Architect retry validation completed with one automatic retry and no Human Review;
- bounded replan validation completed with one automatic replan, zero retry, no Human Review, and REPLAN_REQUIRED evidence;
- missing-runtime validation produced EXTERNAL_ACTION_REQUIRED with zero retry and normal Day unchanged;
- trusted LocalLLM experiment completed with result/artifact recorded and Builder=false;
- Recommended next action was displayed;
- Continue autonomously executed the trusted recommendation without a new Goal and completed with RESULT_RECORDED.

This closes M25 and advances development to M26 Automated Git completion.


M28 is a presentation-only milestone after Zero-Touch validation. Dashboard labels,
help text, buttons, and user-facing status messages may be localized to Japanese,
while API contracts, enum/state values, audit event identifiers, and internal
logic remain English and unchanged.

M26 implementation is ready for external validation:
- only a completed, deterministic-postcheck, scope-validated managed worktree
  on an `agent/` branch becomes a Git completion candidate;
- Python revalidates branch, configured base branch, origin, exact changed-file
  scope, diff whitespace, and commit identity before staging;
- it commits and pushes only the candidate agent branch, then prepares a local
  structured PR comparison; it never creates a PR or merges/pushes `main`;
- the normal **Continue autonomously** recommendation prioritizes this verified
  completion, so routine commit/push relay is not a separate human step;
- the Dashboard exposes bounded candidate/result evidence and an isolated local
  bare-remote validation flow with no configured-project or network mutation.


External M26 validation passed on 2026-09-22:
- Git completion evidence reported PR_READY;
- a commit SHA was produced;
- the validation branch was pushed under agent/m26-validation-*;
- the base branch remained unchanged;
- PR comparison was prepared as main...agent/m26-validation-*;
- validation-only mode remained true;
- no PR was created and main was neither merged nor pushed.

This closes M26 and advances development to M27 Zero-Touch Control Loop.
