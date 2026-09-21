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
| M27 | Zero-Touch Control Loop | M20–M26 | one goal/start → complete or genuine escalation, with no routine relay/PowerShell | ZERO_TOUCH_EXTERNAL_VALIDATION | COMPLETE |
| M28 | Japanese Dashboard / UX simplification + runtime readiness | M27 | localize Dashboard, remove redundant controls, and make approved local runtime dependencies such as Ollama preflight/startup part of normal Zero-Touch readiness while preserving English API/state/audit identifiers | JAPANESE_UI_AND_RUNTIME_READINESS_VALIDATION | COMPLETE |
| M29 | Week 1 Day 4-7 autonomous execution | M28 | drive the remaining LocalLLM-Lab Week 1 runbook through trusted next-action/Zero-Touch orchestration without repeated Goal entry or authority expansion | WEEK1_DAY4_7_AUTONOMOUS_VALIDATION | IN_PROGRESS |

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


M28 should also simplify the Dashboard after M27 proves the Zero-Touch flow.
Controls that are no longer needed for normal daily operation should be removed
from the primary UI or demoted to a clearly separated diagnostic/advanced area.
The goal is not to delete capabilities from the backend, but to remove routine
operator clutter and make the autonomous path visually dominant.

Candidates for removal/demotion include validation-only buttons, duplicate manual
run controls, and controls superseded by Recommended next action / Continue
autonomously. Exact removal decisions should be based on the post-M27 workflow
and must preserve recovery, diagnostics, and authority-boundary access where
still operationally necessary.

M27 implementation is ready for external validation:
- one bounded Dashboard Goal can plan and execute through the existing trusted
  policy without a separate proposal/execute relay;
- each run records concise terminal COMPLETE or ATTENTION evidence, while raw
  Goal text remains outside the aggregate result;
- existing retry/replan, external-action, next-action, and agent-branch Git
  completion policies are reused unchanged rather than bypassed;
- the Dashboard renders the latest Zero-Touch terminal status and exposes a
  bounded close-next-action path without browser-supplied authority.


External M27 Zero-Touch validation passed on 2026-09-22:
- a bounded LocalLLM goal completed through the Zero-Touch flow;
- final status: COMPLETE;
- outcome: RESULT_RECORDED;
- human attention: none;
- LocalLLM execution remained on the trusted configured path.

The first attempt exposed Ollama not running and correctly stopped as ATTENTION with
engine_unavailable. After Ollama was started, the same bounded flow completed.
This validates the M27 control loop while also exposing a remaining daily-operation
friction point: approved local runtime readiness should be automated.

This closes M27 and advances development to M28.


M28 runtime-readiness scope:
- preflight approved local dependencies before Zero-Touch execution;
- if the configured Ollama runtime is installed but not running, start only that
  already-approved local runtime through a fixed trusted mechanism, wait within
  a bounded timeout, then continue;
- never download/install a model or runtime, never enable cloud fallback, and
  never accept browser-supplied executable paths or commands;
- if the approved runtime cannot be started, surface EXTERNAL_ACTION_REQUIRED;
- keep runtime readiness visible in the simplified Japanese Dashboard;
- remove or demote manual controls made redundant by automatic readiness and
  Zero-Touch operation.

M28 implementation is ready for external validation:
- Japanese Dashboard copy makes Recommended next action / Zero-Touch operation
  primary, while detailed manual Day, validation, and Git controls are demoted
  to a closed diagnostic section;
- before a trusted LocalLLM execution, the server checks the fixed approved
  Ollama runtime and, only when it is installed but unavailable, starts its
  fixed local service and waits within the bounded policy;
- readiness is shown as bounded Japanese Dashboard evidence; failure produces
  `EXTERNAL_ACTION_REQUIRED` without installation, model download, cloud
  fallback, browser-supplied command/path, experiment retry, or Builder work.

M29 implementation is ready for external validation:
- Recommended next action advances the persisted Week 1 Day 4-7 sequence
  without another Goal entry;
- Day 4/5 missing model or benchmark capabilities stop with typed
  `EXTERNAL_ACTION_REQUIRED`; Day 6 preserves the runbook's preparation-only
  context policy; Day 7 produces a bounded advisory and
  `HUMAN_DECISION_REQUIRED`;
- all capabilities are read from fixed LocalLLM-Lab configuration and no model,
  benchmark, context, or cloud authority is added.


External M28 validation passed on 2026-09-22:
- the Dashboard is Japanese and Zero-Touch-first;
- manual/validation controls are demoted under diagnostics;
- the trusted LocalLLM Zero-Touch flow completed successfully;
- latest LocalLLM outcome: RESULT_RECORDED;
- engine/model: ollama / qwen3-8b-q4:latest;
- responses: 4/4 success, 0 failed;
- Builder invoked: false;
- approved local Ollama readiness was active and the trusted flow completed without manual runtime/model installation or cloud fallback.

The displayed runtime card may show READY after a later preflight even when an
earlier bounded preflight started Ollama, because runtime_readiness stores the
latest readiness result. The control loop behavior and successful post-stop flow
validate the runtime-readiness path.

This closes M28 and completes the current M0-M28 development roadmap.


M29 opens the next operational phase after the M0-M28 platform roadmap.
The authoritative scope is defined in `docs/WEEK1_DAY4_7_AUTONOMOUS.md` and
LocalLLM-Lab `docs/week1-runbook.md`.

Day 4-7 execution must reuse existing approved LocalLLM-Lab capabilities and
must stop rather than downloading models, installing benchmark tools, or
changing context conditions without explicit approval.


M29 first external validation on 2026-09-22:
- Dashboard correctly stopped Day 4 with typed EXTERNAL_ACTION_REQUIRED;
- observed reason: CROSS_FAMILY_RUNNER_NOT_CONFIGURED;
- no authority expansion occurred.

Follow-up investigation found LocalLLM-Lab already has the generic trusted
`scripts/run_experiment.py` orchestration path and cross-family model-matrix
entries. Therefore M29 should reuse that existing runner rather than introduce a
second cross-family runner. However, the current Gemma/Llama candidates remain
design-only/unreviewed and have no configured runtime_model_name, so execution
must still stop at the approved-runtime/approval boundary until an already
installed model is explicitly approved and configured.

M29 remains IN_PROGRESS until the Day 4 adapter uses the existing trusted runner
and the external gate demonstrates either a real approved cross-family run or the
correct approved-runtime missing boundary.
