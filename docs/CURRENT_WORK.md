# Current Work

## Current checkpoint — G6 PR-00 bounded repair validated for resubmission (2026-10-01)

Reviewer rejected `G6-PR00-COMPLETION-20261001-001` at reviewed commit
`8dad7084e146dd1d1e9305e3f7c4ae3b888753af`. The isolated defect is that
`bind_day_evidence()` relabelled a source record without first checking an existing
run/criterion binding and its Day/contract identity.

The minimum repair and one non-mutation assertion are complete: nullable
legacy records are accepted only when both bindings are absent; bound records must
match the exact run, criterion and product configuration; every source must match
the active Day and contract version. Under
`AUTH-G6-PR00-VALIDATION-RETRY-20261001-001`, the one authorized additional
execution of `python -m pytest -q tests/test_run_execution_composition.py` passed
all 13 tests. No further execution is authorized. Fix and publish a revision 002
completion pack, then stop for its review; do not begin PR-01 before acceptance.

## Current checkpoint — G6 PR-00 fixed for review (2026-10-01)

Under `AUTH-G6-PRODUCT-RUN-RECONCILIATION-20261001-001`, PR-00 strict
Day-to-product Evidence binding is implemented at fixed commit
`8dad7084e146dd1d1e9305e3f7c4ae3b888753af`. The focused command was used twice:
the first run exposed a criterion-selection defect (`11 passed, 1 failed`), and the
bounded correction passed the final run (`12 passed`). Historical nullable Evidence
is unchanged; new completion Evidence is bound to the exact run, criterion and
contract fingerprint.

Review pack `G6-PR00-COMPLETION-20261001-001` was published at pack commit
`269a02615a356fabfcffda6dbb8dabcc461c814b`; remote readback matched. Stop for the
matching PR-00 review. Do not begin PR-01 before acceptance; do not operate
service/browser, Day/Go, model, Watcher, G7/G8 or product acceptance.

## Current checkpoint — product-run reconciliation plan accepted; implementation authority pending (2026-10-01)

Reviewer accepted `G6-PRODUCT-RUN-RECONCILIATION-PLAN-20261001-001` at reviewed
commit `73cfcafd85f285cdc5db6afba5d322d48af7d304`. PR-00 through PR-03 are the
accepted minimum G6 repair plan. Acceptance record commit
`dd14debfb43a55e94b77dd0c523d53c338f6312c` was pushed and read back.

Stop for a separate explicit G6 implementation decision by 広瀬剛. Do not modify
source, execute fixtures, issue another Go, run a model, operate Watcher, begin G8
or claim product acceptance. A02/A05/A06 remain failed until implementation and
subsequent validation.

## Current checkpoint — G7 return accepted; product-run reconciliation plan under review (2026-10-01)

Reviewer accepted `G7-PRODUCT-E2E-20261001-007` at reviewed commit
`91423c2e45fa5c4b35ee589c003adcdd3f39ac13`. Preserve product run
`run-8b9fb7cac4c948098af3e9aa7dfeaf8d`, its artifacts and raw evidence. A01 is
`PASS`; A02/A05/A06 are `FAIL`; A03/A04-current are `NOT_EVALUABLE`. Do not rerun
Day 6 merely to reproduce the accepted discrepancies.

The minimum G6 plan is fixed at
`73cfcafd85f285cdc5db6afba5d322d48af7d304`; review pack
`G6-PRODUCT-RUN-RECONCILIATION-PLAN-20261001-001` is published at remote head
`0e4b9d1291e9a6d82160e9d26aa12f8ec9444cd5`, with readback matched. It limits
work to strict run/criterion Evidence binding, terminal same-run state projection,
actual attempt/token/budget-warning/cost-availability telemetry, and an integrated
deterministic fixture. Await plan review. Do not implement, test, issue another Go,
run a model, operate Watcher, begin G8 or claim product acceptance.

## Current checkpoint — real Day 6 completed, G7 product composition discrepancies fixed for review (2026-10-01)

Under `AUTH-G7-DAY6-REAL-MODE-RETRY-20261001-002`, the service verified the exact
managed `CODEX_SQLITE_HOME`, admitted one Day 6 Go and ran Codex exactly once. Run
`run-8b9fb7cac4c948098af3e9aa7dfeaf8d` produced the four allowed temporal-state
artifacts; the deterministic postcheck passed 6 tests and Day state reached 4/4
`COMPLETE`.

G7 nevertheless returns to G6 at the product boundary. The same durable RunRecord
and dashboard remain `PREFLIGHT`; the completion Evidence Records have null run and
criterion IDs; and actual task token usage plus `TASK_BUDGET_EXCEEDED` are not
projected into run telemetry. Classify A01 `PASS`, A02/A05/A06 `FAIL`, and A03/A04
current `NOT_EVALUABLE`. The service is stopped. Preserve and review the fixed
evidence; do not rerun Day 6, start G8 or claim product acceptance.

## Current checkpoint — Day 6 real-mode retry 2 authorized (2026-10-01)

広瀬剛 authorized `AUTH-G7-DAY6-REAL-MODE-RETRY-20261001-002`: create a new
isolated product worktree and add one Day 6 Go. Before browser action, bind and
verify the exact existing Control Center-managed
`CODEX_SQLITE_HOME=C:\AI-Control-Center\state\codex-sqlite` in the service process.

Retain the fixed product build `3e82626...`, LocalLLM baseline `e33b0a4...`, exact
Grant/RunIntent `max_attempts: 2`, one actual model execution, 30 ACTIVE_WORK
minutes and 0 JPY. Reviewer Bus remains disabled. Stop on completion or the first
new failure/authority boundary; no Watcher, credential, G8 or product-acceptance
action is authorized.

## Current checkpoint — Day 6 real-mode retry blocked before Codex subprocess (2026-10-01)

The one additional Go authorized by
`AUTH-G7-DAY6-REAL-MODE-RETRY-20261001-001` created
`run-dbfa4263c3fd47709057548288a9468d`. Its corrected Grant
`max_attempts: 2` and prerequisite matched, and admission was `ADMISSIBLE`.

The Day then stopped at `EXTERNAL_ACTION_REQUIRED`. The actual runner error was
`CODEX_SQLITE_HOME_NOT_FOUND`: the new detached product worktree did not contain its
fallback `state/codex-sqlite`, and the existing Control Center-managed
`C:\AI-Control-Center\state\codex-sqlite` was not explicitly supplied. Codex never
started a subprocess, thread or turn; all token counters and cost stayed zero, and
LocalLLM-Lab remained clean. The surface `OPENAI_CREDENTIALS_MISSING` classification
is only the generic external-prerequisite mapping for this runner error.

The service is stopped and evidence is fixed. The authorized Go is consumed. Stop
for a new human authority decision before another Go. Any new run must use a fresh
isolated product worktree and verify the existing managed `CODEX_SQLITE_HOME` before
browser action; retain one actual model execution, 0 JPY and all existing exclusions.

## Current checkpoint — corrected Day 6 real-mode retry authorized (2026-10-01)

広瀬剛 authorized `AUTH-G7-DAY6-REAL-MODE-RETRY-20261001-001`: retain the first
blocked run and use a new clean product worktree. Match the fixed product RunIntent
with Grant `max_attempts: 2`, while the existing Day adapter continues to cap actual
Codex/model execution at one. One additional Go is allowed; all other prior limits
remain: Day 6, build `3e82626...`, LocalLLM baseline `e33b0a4...`, 30 ACTIVE_WORK
minutes, 0 JPY, Reviewer Bus disabled, and no Watcher, credentials, G8 or product
acceptance.

## Current checkpoint — Day 6 real-mode validation blocked before model; replacement authority pending (2026-10-01)

The one authorized Go created run `run-a64337972833404e9f5dcd4265f6765f`
but failed closed at `HUMAN_ACTION_REQUIRED / EFFECTIVE_PERMISSION_UNKNOWN` before
model execution. The prerequisite matched; the Grant used `max_attempts: 1` while
the immutable product RunIntent uses its fixed `max_attempts: 2`, so exact authority
matching correctly rejected it. Cost and model calls were zero; LocalLLM-Lab stayed
clean. The service is stopped and the blocked state is retained.

The one-model restriction belongs at the existing Codex execution boundary, which
already uses `max_codex_attempts=1`; the Grant must match the product RunIntent at
two attempts. A corrected run requires a new isolated worktree and one additional
Go. Stop for a separate human authority decision. Do not clear the old state, retry,
start a model, operate Watcher, start G8 or claim product acceptance.

## Current checkpoint — Day 6 real-mode product validation authorized (2026-10-01)

広瀬剛 authorized `AUTH-G7-DAY6-REAL-MODE-20261001-001`: validate the Day 6
real-model product path on fixed product build `3e82626...` and clean LocalLLM-Lab
baseline `e33b0a4...`. Use a separate clean product worktree, real mode only for this
run, 30 ACTIVE_WORK minutes, one Go, one real-model execution and 0 JPY.

Allow only Day 6 scoped output in an isolated engineering worktree and isolated
validation state/evidence. Evaluate A02 and only naturally reached A03/A04-current.
Stop on completion, failure, new authority/repair need or any limit. Do not inject a
failure, operate Watcher, alter credentials, start G8 or claim product acceptance.

## Current checkpoint — G7 product evidence accepted; REAL_MODE_REQUIRED decision pending (2026-10-01)

Reviewer accepted `G7-PRODUCT-E2E-20261001-006` at reviewed commit
`aed7922c20c375336f3c7aad8cd6b62cda088e25`. All eight fixed raw-evidence files
matched their manifest, and they establish one Go plus the same-run transition from
`PREFLIGHT` to `EXTERNAL_ACTION_REQUIRED / REAL_MODE_REQUIRED`.

Record A01 and A05 as limited product-path `PASS`, A06 as partial `PASS`, A02 as
`INPUT_BLOCKED`, and A03/A04-current as `NOT_EVALUABLE`. Stop G7 for a separate
human/runtime authority decision on `REAL_MODE_REQUIRED`. Do not enable real mode,
run a model, issue another Go, operate Watcher, start G8 or claim product acceptance.

## Current checkpoint — G7 revision 005 raw-evidence correction (2026-10-01)

Reviewer rejected `G7-PRODUCT-E2E-20260930-005` only because the fixed commit did
not contain the raw RunRecord, Day/API response and one-Go access log needed to
independently verify their hashes. The same review accepted `REAL_MODE_REQUIRED` as
a correct separate authority boundary.

Without restarting a service or issuing another Go, fixed the preserved original
RunRecord history/current files, Day snapshot, preflight fact and complete access
logs, plus GET-only API readbacks and a SHA-256 manifest under
`docs/review-evidence/G7-PRODUCT-E2E-20260930-006/`. A separate PowerShell check
verified every hash, the shared run ID, PREFLIGHT-to-EXTERNAL_ACTION_REQUIRED
transition, REAL_MODE_REQUIRED blocker and exactly one Go POST. Prepare revision 006
and stop; do not enable real mode, run a model, operate Watcher or start G8.

## Current checkpoint — G7 SP-00 product revalidation passed; review next (2026-09-30)

One authorized browser Go on fixed implementation `3e82626...` created
`run-7ea73560dbac4d27aebaad042022d61a`. Exact current-build authority and prerequisite
facts admitted the run. The early durable version was `PREFLIGHT`; after asynchronous
settlement the dashboard, Day API, run API and current RunRecord all converged on
`EXTERNAL_ACTION_REQUIRED / REAL_MODE_REQUIRED` for that same run.

The prior A05 projection gap is therefore closed by product-path evidence. G7 remains
blocked at the separate real-runtime authority boundary; no model ran, cost was 0 JPY,
Reviewer Bus stayed disabled and the service was stopped. Prepare fixed G7 review and
stop. Do not enable real mode, retry Go, start G8 or claim product acceptance.

## Current checkpoint — bounded G7 SP-00 product revalidation authorized (2026-09-30)

広瀬剛 authorized `AUTH-G7-SP00-PRODUCT-REVALIDATION-20260930-001` for fixed
implementation `3e82626faebab8e9722939b92267deb51075d93b`. Use an isolated clean
AI-Control-Center checkout and the approved clean LocalLLM-Lab baseline, Reviewer Bus
disabled, 30 ACTIVE_WORK minutes, one Day 6 Go and 0 JPY. Create only the exact
current-build Grant and fresh prerequisite observation required for admission.

Validate whether the early `PREFLIGHT` response later converges to the same durable
run at `EXTERNAL_ACTION_REQUIRED / REAL_MODE_REQUIRED` in dashboard, API and
RunRecord. Do not enable real mode, invoke a model, retry Go, repair source, operate
Watcher, start G8 or claim product acceptance. Stop after fixed evidence and review.

## Current checkpoint — SP-00 accepted; G7 product-revalidation decision pending (2026-09-30)

Reviewer accepted `G6-SP00-COMPLETION-20260930-001` at reviewed commit
`3e82626faebab8e9722939b92267deb51075d93b`. SP-00 is complete only for
implementation and deterministic fixtures: asynchronous worker settlement is saved
before one same-run guarded projection, with early/failure paths non-applying.

Stop for a separate direct G7 product-revalidation decision by 広瀬剛. Do not start a
service/browser, another Go/Day, real mode, model, Watcher, G7 rerun, G8 or product
acceptance from this fixture acceptance.

## Current checkpoint — SP-00 implemented and fixture-verified; fixed review next (2026-09-30)

SP-00 now emits one same-run notification per asynchronous Day worker execution
episode only after the worker is non-active and its final snapshot save succeeds.
Production routes the notification to the existing guarded `project_day_state()`;
early return, save failure, identity mismatch, projection rejection and exception are
non-applying and not retried.

Focused results: settlement fixtures `3 passed` then final `5 passed` (2/2 command
executions); product/projection/authority composition `18 passed` (1/2); scoped
compile exit 0 (1/2). Evidence: `docs/review-records/G6_SP00_2026-09-30.md`.
Prepare a fixed implementation commit and completion pack, then stop for review. Do
not run service/browser, actual Go/Day, real mode, model, Watcher, G7 rerun or G8.
Fixed implementation commit: `3e82626faebab8e9722939b92267deb51075d93b`.
Pack `G6-SP00-COMPLETION-20260930-001` is published at remote head
`1d570fe5c1ab6880e7bef766fd98feca9210b067` and was read back from GitHub.

## Current checkpoint — SP-00 implementation authorized (2026-09-30)

広瀬剛 explicitly authorized SP-00 implementation and focused fixture validation
under `AUTH-G6-SP00-IMPLEMENTATION-20260930-001`. Scope is limited to the accepted
post-save asynchronous Day-worker settlement notification and wiring to the existing
same-run projection. Limits are 30 ACTIVE_WORK minutes, at most two executions of
each named focused command and 0 JPY. No service/browser, actual Go/Day, real mode,
model, Watcher, G7 rerun or G8 is authorized.

## Current checkpoint — async SP-00 plan accepted; implementation authority pending (2026-09-30)

Reviewer accepted `G6-SAME-RUN-STATE-PROJECTION-PLAN-20260930-002` at reviewed
commit `c6b81eb779350f9f2ed1be47bcc6da1a23c3aa0b`. The accepted plan emits one
same-run projection notification per Day worker execution episode only after the
worker reaches a non-active state and its final snapshot save succeeds. Early return,
save failure, identity mismatch and projection rejection remain non-applying.

Stop for a separate direct implementation decision by 広瀬剛. Do not modify source,
run fixtures, start service/browser, Go/Day, real mode, a model, Watcher or G8, or
claim product acceptance from this plan acceptance.

## Current checkpoint — G6 projection plan rejected at async timing boundary (2026-09-30)

Reviewer rejected `G6-SAME-RUN-STATE-PROJECTION-PLAN-20260930-001` at
`575108e0a73d1d8ffdffb95724c0341e0e2ef108`. Revision 001 projected on executor
return, but `LocalLLMDayProgram.start()` launches `_execute` on another thread and
returns immediately, so that point can still observe `PREFLIGHT`.

Revise only SP-00's invocation boundary: after the Day worker exits into a non-active
state and successfully performs its final save, emit one same-run guarded projection
notification for that execution episode. Add an ordering fixture to prove early
return, save-before-notify and one notification. Stop for revised plan review; do not
implement, test, retry Go, enable real mode, run a model, operate Watcher or start G8.
Revised plan commit: `c6b81eb779350f9f2ed1be47bcc6da1a23c3aa0b`.
Pack `G6-SAME-RUN-STATE-PROJECTION-PLAN-20260930-002` is published at remote head
`6ea65ac0e14985870fa1736448a3ea2b1fb767bb` and was read back from GitHub.

## Current checkpoint — G7 return accepted; one G6 projection plan proposed (2026-09-30)

Reviewer accepted `G7-PRODUCT-E2E-20260930-004` at reviewed commit
`18be053bde907f646737bfd2f36753585d8e051d`. G7 therefore returns to G6 only
for the missing post-execution projection of the settled Day snapshot into the same
durable RunRecord. `REAL_MODE_REQUIRED` remains a separate human/runtime boundary.

Minimum plan:
`docs/ai-control-center-gates/2026-09/G6_SAME_RUN_STATE_PROJECTION_REPAIR_PLAN_2026-09.md`.
It reuses the existing guarded `project_day_state()` path and adds only its production
post-executor wiring plus focused proof. Stop for fixed plan review and then a
separate human implementation decision. Do not implement, test, retry Go, enable
real mode, run a model, operate Watcher, start G8 or claim product acceptance.
The plan is fixed at `575108e0a73d1d8ffdffb95724c0341e0e2ef108`; pack
`G6-SAME-RUN-STATE-PROJECTION-PLAN-20260930-001` is published at remote head
`c29fd540d18383560b1a548ab18de4914a70270b` and was read back from GitHub.

## Current checkpoint — G7 current-build revalidation returns one G6 gap (2026-09-30)

広瀬剛 authorized bounded Day 6 product revalidation under
`AUTH-G7-LIMITED-PRODUCT-REVALIDATION-20260930-001`. A new exact Grant and fresh
prerequisite observation admitted one browser Go for current build `7b84980...` and
run `run-b229e3cee8a347b5bd621b799b146cda`, closing the previous permission blocker.
The Day controller then stopped at `EXTERNAL_ACTION_REQUIRED / REAL_MODE_REQUIRED`
because the fixed runtime is mock. The same-run durable projection incorrectly stayed
`PREFLIGHT` with no blocker because production Go does not project the default
executor's returned Day state. Proposed G7 result is `RETURN` for that one G6
composition gap. Stop for fixed external review; do not enable real mode, retry Go,
repair code, start G8 or claim product acceptance.

## Current checkpoint — G6 authority-fact stage accepted; human decision required (2026-09-30)

Reviewer accepted `G6-AUTHORITY-FACT-STAGE-COMPLETION-20260930-001` at reviewed
commit `acd505f66ca66550e392f00922b94843243b26c4`. G6 authority-fact composition is
closed only for implementation and deterministic fixtures; AF-00 revision 001 stays
rejected, while AF-00 revision 002 and AF-01 are accepted. The historical Day 6
Grant is not valid authority for the current build. Stop pending 広瀬剛's separate
decision on bounded G7 product revalidation. Do not start service/browser, Go/Day,
model, Watcher or credential operations, spending, G8, or product acceptance.

## Current checkpoint — G6 authority-fact stage completion review pending (2026-09-30)

AF-01 was accepted at `0d94d74a218ed0a1d1e4155801e0095f03b3c761` with no
unresolved gap in its fixture scope. AF-00 and AF-01 are now reconciled against the
accepted authority-fact repair-plan DoD. The proposed G6 result is PASS for
implementation and deterministic fixtures only. Prepare the separate fixed G6
completion review and stop; live service/browser, real Go/Day, G7 product E2E, G8
and product acceptance remain unauthorized. Stage evidence commit:
`acd505f66ca66550e392f00922b94843243b26c4`; pack commit:
`217e79ec9e8953201620b58b43720cb06fbe75fb`. Report
`G6-AUTHORITY-FACT-STAGE-REVIEW-20260930-001` was published and read back as PR #1
comment `5903317499`.

## Current checkpoint — G6 AF-01 implementation complete; fixed review next (2026-09-30)

AF-00 revision 002 was accepted at
`bb111de0b7ef3425f99efa9b887378f96e3632d0`. AF-01 now composes the accepted
Grant/Observation/Fact boundary into Engine, RunCoordinator and read projection using
one immutable RunIntent. The actual FastAPI Go fixture proves exact admission and one
same-run injected effect; missing/stale authority and missing prerequisites fail
closed independently; restart, duplicate Go and legacy start do not duplicate the
effect. The focused suite passed 20 tests on execution 1. Fix and submit AF-01 for
review. Fixed implementation commit `0d94d74a218ed0a1d1e4155801e0095f03b3c761`
and pack commit `870556a08b7edfd646bebfc8b0ca89d6fec5db00` were pushed.
Report `G6-AF01-REVIEW-20260930-001` was published and read back as PR #1 comment
`5903193771`. Do not perform real product E2E or begin another gate pending the exact
matching response.

## Current checkpoint — G6 AF-00 expiry-boundary repair complete (2026-09-30)

Reviewer rejected `G6-AF00-COMPLETION-20260930-001` only because a Grant remained
valid at `now == expires_at`. The comparison now rejects at and after expiry, and a
focused assertion proves permission and all Grant provenance remain absent at exact
equality while prerequisite readiness stays independently evaluable. The new narrow
command passed once (`1 passed, 18 deselected`). Prepare revision 002 and stop for
review. Fixed repair commit `bb111de0b7ef3425f99efa9b887378f96e3632d0`
and pack commit `9140b41e68ebddf0fbb2ad6dc56ceb229bf352b5` were pushed.
Report `G6-AF00-REVIEW-20260930-002` was published and read back as PR #1 comment
`5903078963`. AF-01 and every product/runtime operation remain unstarted pending the
exact matching response.

## Current checkpoint — G6 AF-00 complete; fixed review pending (2026-09-30)

AF-00 now has strict create-only authority, prerequisite-observation and preflight-
fact contracts/stores plus an exact-RunIntent resolver. Exact grant and Day 6
observation provenance resolves independently; mismatch, missing, duplicate,
revoked and corrupt sources fail closed. The historical Day 6 authority companion
is pinned to its original product target and cannot authorize a later build.

The focused suite passed 22 tests on ordinary attempt 1, 23 on ordinary attempt 2,
and—after explicit one-run authority `AUTH-G6-AF00-ADDITIONAL-VALIDATION-20260930-001`
for the observation source-hash correction—23 on the additional execution. Prepare
the fixed AF-00 completion review and stop. Fixed implementation commit:
`2a42323b6999b6e79fc34c6c9ec08edaabe9fcd6`; pack commit:
`f5edfbb0ac822124fdceaf11f66aabcae29c6987`. Report
`G6-AF00-REVIEW-20260930-001` was published and read back as PR #1 comment
`5902887112`. AF-01, service/browser, real Go/Day, model, Watcher, credentials, G8
and product acceptance remain unstarted pending the exact matching response.

## Current checkpoint — G6 AF-00 implementation authorized (2026-09-30)

広瀬剛 explicitly authorized the fixed authority-fact composition plan with
`開始してください。`, recorded as
`AUTH-G6-AUTHORITY-FACT-IMPLEMENTATION-20260930-001` in
`docs/review-records/G6_AUTHORITY_FACT_IMPLEMENTATION_AUTHORITY_2026-09-30.md`.
Implement AF-00 only, within 30 ACTIVE_WORK minutes, at most two executions of each
focused command and 0 JPY. Fix and review AF-00 before AF-01. Do not start a service,
browser, real Go/Day, model, Watcher, credential change, G8 or product acceptance.

## Current checkpoint — G7 RETURN accepted; G6 authority-fact plan ready (2026-09-30)

`G7-PRODUCT-E2E-20260930-003` returned exact `ACCEPT` for reviewed commit
`ef93249eb238cbf52707e8ff4521e7d9f487a198`. G7 returns only for the missing
production authority/prerequisite-fact resolution path. Acceptance record:
`docs/review-records/G7_PRODUCT_E2E_003_ACCEPTANCE_2026-09-30.md`.

Minimum plan:
`docs/ai-control-center-gates/2026-09/G6_AUTHORITY_FACT_COMPOSITION_REPAIR_PLAN_2026-09.md`.
AF-00 adds strict versioned grants, prerequisite observations and create-only
preflight evidence; AF-01 wires the same-intent resolver into production and proves
it through a deterministic FastAPI fixture. Stop for 広瀬剛's implementation-authority
decision. Do not implement, run tests/service/browser/Go/Day/model, operate Watcher,
change credentials, start G8 or claim product acceptance.

## Current checkpoint — G7 clean baseline reaches permission-composition blocker (2026-09-30)

The directly approved clean LocalLLM-Lab baseline was exercised once through the
real loopback service and Chrome dashboard. Clean Git admission passed, but run
`run-a29217eb049447b68b83ce53a1df1054` stopped fail-closed at
`EFFECTIVE_PERMISSION_UNKNOWN`. Production composition defaults trusted preflight
facts to unknown and exposes no server-owned path from the recorded decision to
those facts. A second unchanged Go was not attempted. Evidence:
`docs/review-records/G7_CLEAN_BASELINE_PRODUCT_VALIDATION_2026-09-30.md`.

Proposed G7 result is `RETURN` to the minimum G6 authority/prerequisite-fact
composition repair. Stop for fixed review. Do not implement the repair, reuse the
remaining Go attempt, start G8, restart Watcher, change credentials, invoke a model
or claim product acceptance.

## Current checkpoint — G7 clean-baseline product validation authorized (2026-09-30)

広瀬剛 approved `AUTH-G7-CLEAN-BASELINE-VALIDATION-20260930-001`: preserve the
existing dirty `C:/LocalLLM-Lab` working tree, create a separate clean worktree at
`e33b0a410fb8647711f02ae4e6e0b66472e6eff0`, and resume Day 6 product-E2E in a
new 30-ACTIVE_WORK-minute window with at most two Go attempts and 0 JPY. Record:
`docs/review-records/G7_CLEAN_BASELINE_VALIDATION_AUTHORITY_2026-09-30.md`.

Action class is `VALIDATION`. Reviewer Bus stays disabled. No code repair, Watcher,
credential change, paid action, G8 or product acceptance is authorized. Fail closed
and stop for fixed evidence/review at the first blocking or completion boundary.

## Current checkpoint — G7 correction accepted; clean baseline decision pending (2026-09-30)

`G7-PRODUCT-E2E-20260930-001` was rejected because it confused the clean
AI-Control-Center managed worktree with the configured admission target. Existing
configuration and fixed code show that admission inspected `C:/LocalLLM-Lab` before
the RunRecord was persisted. The saved Go-time fingerprint matches the current
LocalLLM-Lab fingerprint, and its eight dirty paths predate Go. The generated
AI-Control-Center RunRecord is withdrawn as the cause; no G6 defect is established.

Corrected evidence:
`docs/review-records/G7_PRODUCT_E2E_ADMISSION_CORRECTION_2026-09-30.md`.
Revision pack: `docs/review-packs/G7-PRODUCT-E2E-20260930-002.md`.
The Reviewer accepted the corrected state as `INPUT_BLOCKED`; acceptance record:
`docs/review-records/G7_PRODUCT_E2E_CORRECTION_ACCEPTANCE_2026-09-30.md`.
The active boundary is one decision by 広瀬剛 on an approved clean LocalLLM-Lab
baseline that preserves existing work. Baseline selection alone does not reset the
exhausted two-attempt Go limit. Do not retry Go without a separately explicit new G7
validation window; do not start G8, operate the Watcher, change credentials, run a
model or claim product acceptance.

## Prior checkpoint — G7 product validation proposed G6 return (rejected) (2026-09-30)

The original evidence and `G7-PRODUCT-E2E-20260930-001` remain immutable rejection
history. Their G6-return cause and target are superseded only by revision 002.

## Prior checkpoint — G6 runtime-composition complete; G7 decision pending (2026-09-30)

`G6-RUNTIME-COMPOSITION-COMPLETION-20260930-002` returned exact `ACCEPT` for
`a71ab7a30edad05a1b6310fb87548764fe5e17c1`. G6 runtime-composition implementation
and deterministic fixtures are complete with no unresolved gap in that scope.
Acceptance record: `docs/review-records/G6_RUNTIME_COMPOSITION_COMPLETION_ACCEPTANCE_2026-09-30.md`,
published at remote head `8497bb239c35003f212996e9d4d7afde0a57ffab`.

## Current checkpoint — G6 completion rejection repaired; revision 002 pending (2026-09-30)

`G6-RUNTIME-COMPOSITION-COMPLETION-20260930-001` was rejected only for invariant 5
snapshot-run Evidence binding and invariant 8 required-review completion blocking.
The bounded repair now checks snapshot run identity before Evidence mutation and uses
the persisted review blocker so reconstruction cannot bypass review. Both focused
runs passed 44 tests. Fixed repair commit:
`a71ab7a30edad05a1b6310fb87548764fe5e17c1`.

Revision pack:
`docs/review-packs/G6-RUNTIME-COMPOSITION-COMPLETION-20260930-002.md`, published at
remote head `4cc258d29b4acf4893a988719e3dd66f7071ed55`; readback matched. Stop for exact
review. Do not begin G7, a real service/browser/Day 6, model, Watcher, credentials,
spending or product E2E.

## Current checkpoint — G6 runtime-composition completion review pending (2026-09-30)

`G6-RI03-COMPLETION-20260930-001` returned exact `ACCEPT` for
`cc7976ddeded8e171d4ce9a668895b582bdb5987`. RI-00 through RI-03 now each have an
accepted fixed commit. Acceptance and the ten-invariant/DoD reconciliation are fixed
in `bff5990bf11b40892f1841f9ab72deda1a1bcb39`.

Separate completion pack:
`docs/review-packs/G6-RUNTIME-COMPOSITION-COMPLETION-20260930-001.md`, published at
remote head `98a31b6429c60a683ec5cb2d460a463ba42e88b9`; readback matched. Stop for its exact
review. Do not start G7 validation, a service/browser, Day 6, model, Watcher,
credentials, spending or product E2E before that boundary and applicable authority.

## Current checkpoint — G6 RI-03 fixed review pending (2026-09-30)

RI-02 acceptance is recorded for `81715589915d3739327847bb7f1895ad4abdd1d4`.
RI-03 now binds the accepted coordinator, same-run execution controls, telemetry and
read model in the production Engine and demonstrates the route through actual FastAPI
handlers with a deterministic injected executor. Fixed implementation/evidence commit:
`cc7976ddeded8e171d4ce9a668895b582bdb5987`. Immutable review pack:
`docs/review-packs/G6-RI03-COMPLETION-20260930-001.md`, published at remote head
`fe6eca251865d018d38d94d3c953478972274845`; remote readback matched.

Focused validation required one explicitly authorized additional execution after two
ordinary attempts and then passed 42 tests. Stop for exact RI-03 review. Do not start
real service/browser/Day 6 E2E, model, Watcher, credentials, spending, G7 or G8 from
this fixture result.

## Current checkpoint — G6 RI-00 fixture complete; fixed review pending (2026-09-29)

広瀬剛 directly authorized dependency-ordered RI-00 through RI-03 implementation in
`AUTH-G6-RUNTIME-COMPOSITION-IMPLEMENTATION-20260929-001`. RI-00 now persists the
initial same-run record before an injected Day effect, fails closed on admission and
identity mismatch, suppresses duplicate Go, guards the legacy start route and retains
versioned RunControl history. Focused validation passed 32 tests; the changed direct
controller compatibility fixture passed 2 tests. Evidence:
`docs/review-records/G6_RI00_2026-09-29.md`.

Stop after publishing the fixed RI-00 review pack. RI-01 is dependency-blocked until
the matching RI-00 response is read and accepted. No actual Day, model, service,
Watcher, credential, paid action, product E2E, G7 or G8 is authorized by this card.

## Prior checkpoint — G6 composition plan accepted; implementation authority pending (2026-09-29)

External review `G6-RUNTIME-COMPOSITION-PLAN-20260929-001` accepted the fixed plan
commit `12b93f7f2ff5d017ec38bd9fe5b14ed21a115c40`. Acceptance record:
`docs/review-records/G6_RUNTIME_COMPOSITION_PLAN_ACCEPTANCE_2026-09-29.md`.
The accepted scope is RI-00 through RI-03 only; no card has started. Stop for a
separate direct decision by 広瀬剛 on G6 implementation authority. Plan acceptance
does not authorize tests, service/browser operation, Day selection/Go, model use,
Watcher or credential changes, spending, G8, or product acceptance.

## Prior checkpoint — G7 returned; G6 composition-plan review (2026-09-29)

Latest human instruction: 「G7行きましょう。」, recorded as
`AUTH-G7-START-20260929-001` in
`docs/review-records/G7_START_AUTHORITY_2026-09-29.md`. G6 remains closed only at
the accepted implementation-and-fixture baseline
`a30ed2303a85ff00ebbb5b0721bea4fe5c66ad0f`.

Current objective: complete GV-03 evidence mapping and obtain review of the proposed
G7 result. The accepted plan separates deterministic fixtures, the fixed VC-11
actual-actor trace, and product E2E. Product UI/Day/telemetry E2E remains
`INPUT_BLOCKED`; do not start a service, browser flow, Watcher, Day/Go, model,
credential or paid action from the G7-start instruction alone. After publishing the
result pack, stop at the external review boundary.

Plan pack `G7-VERIFICATION-PLAN-20260929-001` was rejected only because GV-00 did
not define the production-path, answer-leakage and output/token/time/disconnect/failure
retention judgments. Revision 002 adds those criteria and their
`NOT_APPLICABLE`/`NOT_EVALUABLE`/`FAIL` boundaries. No test may run until the revised
plan receives an exact matching acceptance.

Plan revision 002 at `3b267223d507aefe113df671a9331be5c1fc0a13` returned exact
`ACCEPT`. GV-00 baseline/test-integrity classification passed without changing code
or tests; product wiring and real boundaries that fixtures do not traverse remain
explicitly `NOT_EVALUABLE`. GV-01 is now selected for the fixed Python and Node
commands only. Limits remain 30 ACTIVE_WORK minutes, two attempts per command and
0 JPY. GV-02 live operations remain unauthorized.

Pack `G7-GV00-GV01-COMPLETION-20260929-001` returned exact `ACCEPT` for the
deterministic boundaries at `7e28c55975a42985e10cfe4b2c9d2da3a194fb3a`.
GV-02's permitted read-only slice re-read the fixed VC-11 GitHub comments, isolated
SQLite turn/items and Watcher registry. IDs, raw/canonical hashes and the 4.321-second
sequence matched; one historical actor path is `PASS`. Current liveness, live
disconnect, product UI/Day/telemetry remain `NOT_EVALUABLE` or `INPUT_BLOCKED`.
`G7-GV02-COMPLETION-20260929-001` returned exact `ACCEPT` for the historical
actor-trace boundary at `61d8d10d0f899160033e3b84bab7f855c7b3dee1`.
GV-03 maps every A01–A06 requirement. All admitted fixture boundaries pass and one
historical A04 actor path passes, but current product UI, actual Day Evidence/repair,
current review liveness and real telemetry remain `INPUT_BLOCKED` or
`NOT_EVALUABLE`. `G7-STAGE-RESULT-20260929-001` returned exact `ACCEPT` for the
proposed `CONDITIONAL_PASS` at
`f5f86b39ae55276825630bfa6ca2d9847b83bf04`. This is not unconditional product
acceptance and does not itself close G7. Stop for 広瀬剛's G7 exit decision; do not
begin G8, satisfy the conditions or perform a live/product operation.

広瀬剛は `AUTH-G7-MUST-CLOSURE-20260929-001` で、条件付き結果を中間記録として
保持し、未評価Mustを解消するG7追加検証を承認した。live操作前の静的経路照合で、
UI Goがpreflight previewで停止して実Dayを開始せず、RunIntent、Evidence、修正／
レビュー、telemetry、read modelが一つの製品runへcomposeされていないことを確認した。
legacy direct-startで迂回しても要求証拠にならない。G7の新しい提案結果は`RETURN`で、
G6の限定integration planへ戻す。次境界はこの差戻し結果の外部レビュー。サービス、
ブラウザー、Day/Go、モデル、Watcher又はG8を開始しない。

`G7-MUST-CLOSURE-20260929-001` returned exact `ACCEPT` for G7 `RETURN` at
`b94b93bf1ad7accdf8a83fd4e40edd242529c787`. The return is recorded in
`docs/review-records/G7_MUST_CLOSURE_RETURN_ACCEPTANCE_2026-09-29.md`.
The minimum G6 repair plan is
`docs/ai-control-center-gates/2026-09/G6_RUNTIME_COMPOSITION_REPAIR_PLAN_2026-09.md`:
RI-00 durable run spine/guarded Go, RI-01 execution-Evidence-repair-review adapters,
RI-02 telemetry/read-model composition, RI-03 integrated product-boundary fixture.
Next boundary is plan review. Do not implement or run tests/live operations before
the matching response and separate human implementation authority.

## Current checkpoint — G6 closed; next boundary not authorized (2026-09-29)

The complete external response for `G6-STAGE-COMPLETION-20260929-001` exactly
matched `a30ed2303a85ff00ebbb5b0721bea4fe5c66ad0f` and returned `ACCEPT`.
G6 is closed only as the implementation-and-fixture stage. Acceptance record:
`docs/review-records/G6_STAGE_COMPLETION_ACCEPTANCE_2026-09-29.md`, published in
commit `8d47386f9be21ab69d2debb59b2a429813e5fa11`; remote readback matched.

Stop here. G7/G8, Day selection/Go, service/browser work, model execution,
credentials, spending and product E2E are not authorized. Selected-Day product E2E
remains `INPUT_BLOCKED`. Await a separate human instruction for the next boundary.

## Current G6 checkpoint — WC-10 accepted; VC-11 evidence prepared (2026-09-29)

The complete external response for `G6-WC10-COMPLETION-20260929-002` exactly
matched commit `b041bf7bce51023a3de9067b7a3e80460adb3a0b` and returned `ACCEPT`.
Record: `docs/review-records/G6_WC10_COMPLETION_ACCEPTANCE_2026-09-29.md`.

VC-11 is selected. The fixed real-actor evidence reuses the already-observed
`G6-ACC-WC01-CONFIRM-20260928-002` path: report comment `5865122824`, sole matching
response `5865174825`, exact authority/target correlation, Watcher `APPLIED`, and the
original wait's persisted `RESOLVED_BY_CONFIRMATION` effect. GitHub readback confirmed
both comments and found exactly one matching reply. This validates one real-actor
delivery/application path without creating another report or restarting a service.

The saved Watcher JSON currently says `running=true`, but no localhost:8000 listener
was observed, so that flag is stale state rather than current liveness proof. The
human suspension remains controlling. Selected-Day product E2E remains
`INPUT_BLOCKED`: no Day, product Go, new-run environment/owner, limits or required
live-auth authority is currently supplied. Evidence commit:
`c1758faa9f8ce8b8a7018d828d97fcb90b4bd35b`. Review pack:
`docs/review-packs/G6-VC11-COMPLETION-20260929-001.md`, published at head
`9a7ad1b4f8c359ddaa5511084ecee2825038b8f0`; remote readback matched. Await exact
acceptance. Do not start a Day, restart Watcher/service, or claim G6/product
completion before the matching review.

The first VC-11 pack was rejected because its reviewed commit did not fix the
Watcher rows and continuation envelope used by the record. Read-only extraction from
the isolated Codex SQLite history and Watcher registry fixed source hashes, exact
turn/item identities, the final `NO_REPORT` envelope, `APPLIED` and
`RESOLVED_BY_CONFIRMATION` entries, and their shared correlation. Evidence commit:
`8d4e6bda66d283ffcc8f2fe1b6d7eaba9b66f254`. Resubmission pack:
`docs/review-packs/G6-VC11-COMPLETION-20260929-002.md`, published at head
`b69da542a5ffb1721e1efc5cdc86d8c2051f8d74`; remote readback matched. No delivery,
restart or state rewrite occurred. Await exact acceptance.

VC-11 resubmission returned exact `ACCEPT` for
`8d4e6bda66d283ffcc8f2fe1b6d7eaba9b66f254`. Acceptance record:
`docs/review-records/G6_VC11_COMPLETION_ACCEPTANCE_2026-09-29.md`. The G6 dependency
matrix now binds WC-00 through VC-11 to their accepted fixed commits and preserves
fixture, actual-actor and product-E2E boundaries. Stage evidence commit:
`a30ed2303a85ff00ebbb5b0721bea4fe5c66ad0f`. Completion pack:
`docs/review-packs/G6-STAGE-COMPLETION-20260929-001.md`, published at head
`cfb3b1895faea9c2827250b75ce29565f2f7307b`; remote readback matched. G6 is
`G6_COMPLETION_REVIEW_PENDING`. Do not begin G7/G8 or a Day before exact acceptance
and the applicable subsequent authority.

## Current G6 checkpoint — WC-10 dashboard fixture verified (2026-09-29)

The complete external response for `G6-WC09-COMPLETION-20260929-002` exactly matched
commit `02fbfbe6db894c822adb3292082f4fb591ac1add` and returned `ACCEPT`. Record:
`docs/review-records/G6_WC09_COMPLETION_ACCEPTANCE_2026-09-29.md`.

WC-10 now renders the WC-09 GET-only projection without changing Go/backend behavior.
It keeps human response separate from Reviewer confirmation, labels approval subject
and allowed effect, preserves unknown/source telemetry, and labels history as noncurrent.
The first Node test-runner command was blocked before test execution by sandbox
`spawn EPERM`; the second/final single-process command passed four focused tests.
Evidence: `docs/review-records/G6_WC10_2026-09-29.md`. Fixed implementation/evidence
commit: `138cc2144ad8a820deec889e66a90ddfe0ca9903`. Immutable review pack:
`docs/review-packs/G6-WC10-COMPLETION-20260929-001.md`, published at head
`c7ca55b6311ed2770dc6e47fc282abbb0c29d31a`; remote readback matched. Await exact
acceptance. The first pack was rejected only because the fixture did not assert the
rendered sourced-zero relay/cost values and attempt actual/limit. Three assertions are
prepared without production-code change. The human explicitly authorized exactly one
additional `node tests/run_status_ui.test.js` run; it passed all four tests, including
the three new exact display assertions. Evidence and authority:
`docs/review-records/G6_WC10_2026-09-29.md`. Fixed test/evidence commit:
`b041bf7bce51023a3de9067b7a3e80460adb3a0b`. Resubmission pack:
`docs/review-packs/G6-WC10-COMPLETION-20260929-002.md`, published at head
`fc5314682d661cfcd88cde6958d0936ad33aa99e`; remote readback matched. Await exact
acceptance. Do not begin VC-11, actual Day/Go, service/browser E2E, or claim product
acceptance.

## Current G6 checkpoint — WC-09 fixture verified; external gate preparation (2026-09-29)

WC-08 acceptance exactly matched pack `G6-WC08-COMPLETION-20260929-002` and commit
`502550c487afc52844f8ec3011b4914e85f7822d`. WC-09 read-only projection was
implemented. Attempt 1 exposed only a short fixture fingerprint; attempt 2 passed 25
tests. Artifact review then found the state-rich checks bypassed the HTTP endpoint.

A minimal endpoint-to-read-model binding and HTTP PREFLIGHT assertion were then added.
The human explicitly authorized one additional focused run beyond the original two-run
limit; it passed 25 tests in 3.59s with six dependency deprecation warnings. Evidence:
`docs/review-records/G6_WC09_2026-09-29.md`. Fixed implementation/evidence commit:
`b9d16674de3c7be35c82bc24f279d7b67e3a4809`. Immutable review pack:
`docs/review-packs/G6-WC09-COMPLETION-20260929-001.md`, published at head
`af68b21a96d8f75b71cbf2e3ac233cce28a1df19`; remote readback matched. The first pack
was rejected only because the evidence omitted the direct human authority provenance
for the third run. Record the exact text, target, one-run scope and chat source, then
resubmit without code change or rerun. Authority/evidence commit:
`02fbfbe6db894c822adb3292082f4fb591ac1add`. Resubmission pack:
`docs/review-packs/G6-WC09-COMPLETION-20260929-002.md`, published at head
`91315dd591744501725775ca4685b960aaab5712`; remote readback matched. Await exact
acceptance. Do not start WC-10, run a service/Day/model, or claim product/E2E
acceptance from this fixture result.

## Current G6 checkpoint — WC-08 rejection evidence repaired; resubmission pending (2026-09-29)

The complete response for `G6-WC07B-COMPLETION-20260929-002` exactly matched
commit `6103fdb605b93a8ac8271ddc9a7746564f54d772` and returned `ACCEPT`.
Record: `docs/review-records/G6_WC07B_COMPLETION_ACCEPTANCE_2026-09-29.md`.

WC-08 now provides immutable run-bound telemetry for manual relay, reasoned
interventions, attempts/limits, tokens, cost, source and observation time. Unknown
values remain null with a reason; known values require provenance. Create-only JSON
storage prevents existing-run telemetry replacement. Focused model/store validation
passed 16 tests in 0.35s.

Pack `G6-WC08-COMPLETION-20260929-001` was rejected because the implementation's
duplicate-intervention guard lacked a direct assertion. A bounded test now submits two
same-run interventions with the same ID and a consistent relay count, isolating the
duplicate-ID rejection. The focused repair run passed 17 tests in 0.36s; production
code did not change.

Evidence: `docs/review-records/G6_WC08_2026-09-29.md`. Fixed evidence commit:
`502550c487afc52844f8ec3011b4914e85f7822d`. Resubmission pack:
`docs/review-packs/G6-WC08-COMPLETION-20260929-002.md`, published at head
`765f722c301b08c00e6a4108f4f76cb09f77aceb`; remote readback matched. Await exact
acceptance. Do not start WC-09, a live run, Day/model/service work or product E2E
before exact WC-08 acceptance.

## Current G6 checkpoint — WC-07B rejection repaired; resubmission pending (2026-09-29)

The complete response for `G6-WC07A-COMPLETION-20260929-001` exactly matched
commit `2881f8e6a58dfbaca68baf0355f111986b31b6a4` and returned `ACCEPT`.
Record: `docs/review-records/G6_WC07A_COMPLETION_ACCEPTANCE_2026-09-29.md`.

WC-07B distinguishes Reviewer-proposal endorsement, artifact acceptance, gate
exit and implementation authority. Human text is preserved but has no effect until
subject/revision/commit/effect are fixed and a matching Reviewer confirmation,
successful continuation and effect evidence are present. H01–H08 and existing
confirmation/file fixtures passed twice: 45 tests, final in 3.84s.

Pack `G6-WC07B-COMPLETION-20260929-001` was rejected because a confirmation reply
could omit `RESPONSE_ID`. The bounded repair now rejects a missing or blank response
ID before applying any effect; a direct assertion keeps pending state and empty
response, effect and evidence fields. Focused repair validation passed 46 tests in
4.32s.

Evidence: `docs/review-records/G6_WC07B_2026-09-29.md`. Fixed repair commit:
`6103fdb605b93a8ac8271ddc9a7746564f54d772`. Resubmission pack:
`docs/review-packs/G6-WC07B-COMPLETION-20260929-002.md`, published at head
`46ccaa82cd4bcf5d7e30ec030b4962e7061cac36`; remote readback matched. Await exact
acceptance. Do not start WC-08, Watcher/live delivery, a Day, service/model work,
or product E2E before exact WC-07B acceptance.

## Current G6 checkpoint — WC-07A fixed and externally reviewable (2026-09-29)

WC-07 acceptance exactly matched pack `G6-WC07-COMPLETION-20260929-001` and
commit `091343d45fea907f6015be997930cdb040c29c91`. WC-07A now distinguishes
received, applying, applied, verified and failure states with IDs, timestamps,
envelope outcome, downstream effect and actor/auth availability. Exit 0 alone is
not application or verification. Final focused validation passed 25 tests.

Implementation: `2881f8e6a58dfbaca68baf0355f111986b31b6a4`.
Pack: `docs/review-packs/G6-WC07A-COMPLETION-20260929-001.md`; published head
`306c766dcd4f6d449eca211ccfe84b062c1a0c78`, remote readback matched.
Await exact acceptance before WC-07B; no live Watcher/delivery/Day action.

## Historical G6 checkpoint — WC-07 fixed and externally reviewable (2026-09-29)

The response for `G6-WC06-COMPLETION-20260929-001` exactly matched reviewed
commit `7ff69297eedfa5f3f549e8060a544b34a774a51b` and returned `ACCEPT`.
Record: `docs/review-records/G6_WC06_COMPLETION_ACCEPTANCE_2026-09-29.md`.

WC-07 now provides Day-independent Review Control fixture states and guards for
single outstanding report, exact response correlation, duplicate suppression,
Watcher availability and deadline expiry. Terminal history and active outstanding
identity are separate. Two focused commands passed 20 tests each; no live delivery
or Day-state mutation occurred.

Fixed implementation commit: `091343d45fea907f6015be997930cdb040c29c91`.
Pack: `docs/review-packs/G6-WC07-COMPLETION-20260929-001.md`, published at
`3d0152a35defb0a19d1b5d1d9241b0dc1d529d2a`; remote readback matched.
Await exact acceptance before WC-07A. Do not restart Watcher, deliver a live report,
start a Day, or claim product E2E acceptance.

## Historical G6 checkpoint — WC-06 fixed and externally reviewable (2026-09-29)

The manually relayed response for `G6-WC05-COMPLETION-20260928-001` exactly
matched reviewed commit `5f45bfc8dcfbe7fa5fe73854ca549a72fa99e9ae` and returned
`ACCEPT`. Record: `docs/review-records/G6_WC05_COMPLETION_ACCEPTANCE_2026-09-29.md`.

WC-06 is selected and fixture-implemented. The guard binds attempts to one
RunRecord and checks run/Day, scope, Git, active-work and attempt limits. The
second same failure enters `HUMAN_ACTION_REQUIRED`; a third attempt is forbidden.
Only an exactly correlated review returns the same run/Day to `PREFLIGHT`, without
resetting attempt history. First focused validation passed `11 passed in 0.40s`.

Fixed implementation/evidence commit:
`7ff69297eedfa5f3f549e8060a544b34a774a51b`. Manual external-gate pack:
`docs/review-packs/G6-WC06-COMPLETION-20260929-001.md`, published in branch head
`9bf727a1bc51d12d9386cc2654d7840336544d23`; remote readback matched.
Await the exact external response before WC-07. Do not run a real repair, Day,
review transport, service/browser E2E, or claim product acceptance.

## Historical G6 checkpoint — WC-05 fixed and externally reviewable (2026-09-28)

The manually relayed response for `G6-WC04-COMPLETION-20260928-001` exactly
matched reviewed commit `76a1c9c7dada47239a8a5f8ccb4b6431dc1d4fda` and
returned `ACCEPT`. Record:
`docs/review-records/G6_WC04_COMPLETION_ACCEPTANCE_2026-09-28.md`.

WC-05 is selected and fixture-implemented within the approved G6 dependency
order. The strict Result Adapter binds accepted Evidence to the RunIntent run ID,
criterion ID, Evidence type, provider/validator versions and fingerprints. Wrong
types, empty output, exit 0 alone and run mismatch remain incomplete. The first
fixture attempt exposed a test-data criterion mismatch; after correcting only the
fixture mapping, the second/final attempt passed `6 passed in 1.97s`. Evidence:
`docs/review-records/G6_WC05_2026-09-28.md`.

Fixed implementation/evidence commit:
`5f45bfc8dcfbe7fa5fe73854ca549a72fa99e9ae`. Manual external-gate pack:
`docs/review-packs/G6-WC05-COMPLETION-20260928-001.md`, published in branch head
`08e9017d7961c8f941ced5e93508708195620bfb`; remote readback matched.
Next: correlate a complete external response by PACK_ID and REVIEWED_COMMIT.
Do not start WC-06, an actual Day, service/browser E2E, or claim product acceptance
before a matching acceptance is applied.

## Historical G6 checkpoint — WC-04 fixed and externally reviewable (2026-09-28)

The manually relayed response for `G6-WC03-COMPLETION-20260928-001` exactly
matched reviewed commit `0bda133b20f834f8316be6f8084a240d3034a947` and
returned `ACCEPT`. Record:
`docs/review-records/G6_WC03_COMPLETION_ACCEPTANCE_2026-09-28.md`.

WC-04 is selected and implemented within the approved G6 dependency order.
Selection is browser-local with no POST; Go accepts only selected Day, creates a
server-owned immutable RunIntent, keeps the same run ID through admission, and
reaches at most PREFLIGHT without starting a Day. Focused validation passed 27
tests with six existing dependency warnings; `node --check frontend/app.js`
also passed. Evidence: `docs/review-records/G6_WC04_2026-09-28.md`.

Fixed implementation/evidence commit:
`76a1c9c7dada47239a8a5f8ccb4b6431dc1d4fda`. Manual external-gate pack:
`docs/review-packs/G6-WC04-COMPLETION-20260928-001.md`, published in branch head
`10ea88bf99cbc03085f26dd64c824ee0341e34e5`; remote readback matched.
Next: correlate a complete external response by PACK_ID and REVIEWED_COMMIT.
Do not start WC-05, reload the service, select/Go an actual Day, or claim product
E2E acceptance before a matching acceptance is applied.

## Current G6 checkpoint — WC-03 fixture passed; external gate preparation (2026-09-28)

The manually relayed external response for
`G6-WC02-COMPLETION-20260928-001` exactly matched reviewed commit
`3eb601ac1bbb45d8d126401d853e0b1caaa9afc6` and returned `ACCEPT`.
WC-02 is therefore complete only at deterministic-fixture level. Acceptance
record: `docs/review-records/G6_WC02_COMPLETION_ACCEPTANCE_2026-09-28.md`.

WC-03 was selected under the already-authorized G6 dependency order. It now exposes
each configured Day 1–14 as read-only catalog data containing contract version,
required Evidence, authoritative source scope, required preflight inputs, and an
`ADMISSIBLE` or concrete `INPUT_BLOCKED` result. Missing Day-specific inputs must
block only that Day and must not be inferred or repaired. One fresh-process command
passed: `18 passed, 6 warnings in 2.71s`; the warnings are existing dependency
deprecations. Evidence: `docs/review-records/G6_WC03_2026-09-28.md`.

Fixed implementation/evidence commit:
`0bda133b20f834f8316be6f8084a240d3034a947`. Manual external-gate pack:
`docs/review-packs/G6-WC03-COMPLETION-20260928-001.md`, published in branch head
`67a01ec02c1ceef52bcb3499f103405dede7e180`; remote readback matched.
Do not select/Go a Day, run a model, mutate LocalLLM-Lab, restart services, or
begin WC-04 until the fixed WC-03 gate response is applied.

## Current G6 checkpoint — WC-02 repair fixture passed; external gate pending (2026-09-28)

The latest human instruction resumed work under the new Control Tower/manual
external-gate regime. The bounded WC-02 change now rejects requested limits over
1800 active-work seconds or two attempts, and focused assertions cover both
boundaries. The first newly authorized fresh-process fixture command stopped at
collection because the new test initially omitted `import pytest`; no target
assertion ran. After the human explicitly authorized one additional run, the
corrected focused suite passed `8 passed in 4.06s`.

Evidence: `docs/review-records/G6_WC02_BOUNDED_REPAIR_2026-09-28.md`.
Fixed implementation/evidence commit:
`3eb601ac1bbb45d8d126401d853e0b1caaa9afc6`. Manual external-gate pack:
`docs/review-packs/G6-WC02-COMPLETION-20260928-001.md`, published in branch head
`6a45da2ea8704c07b87fdd01b64c9127454fde98`. Remote readback matched that head.
Next boundary: receive and correlate the external response by `PACK_ID` and
`REVIEWED_COMMIT`. Do not treat the deterministic fixture pass as product/E2E
acceptance. WC-03, Day/Go, model/service work and later gates remain out of scope
until the WC-02 review boundary is resolved.

## Runtime override — reviewer Watcher suspended (2026-09-28)

Latest human instruction: 「Watcher、止めても良いんじゃない？」, following
the separate Control Tower manual external-gate review-pack pilot.
The old reviewer Watcher is suspended; do not automatically restart it or treat
its outstanding reports as accepted, closed, or migrated to the manual pilot.
Dashboard was restarted with `AI_CONTROL_CENTER_DISABLE_REVIEWER_BUS=1`;
live status confirmed `running=false`, `available=false`,
`last_error=DISABLED_BY_ENV`. Dashboard remains available on localhost:8000.
This is a process-local environment setting, not a persistent change to the
launcher: preserve the same setting on subsequent starts while suspended.
Existing pending report records remain; no WC-02 work or reviewer response was
applied by this operation. External ChatGPT event tasks were not changed.
See the 2026-09-28 Watcher suspension entry in `ENGINEERING_WORK_HISTORY.md`.

## Current G6 checkpoint — WC-02 bounded repair confirmation (2026-09-28)

Human chose the bounded repair option in `AUTH-G6-WC02-REPAIR-20260928-001`,
recorded at `docs/review-records/G6_WC02_REPAIR_AUTHORITY_2026-09-28.md`.
The existing foreground Codex edit route is named and limited; the only intended
source change is fail-closed rejection of `active_work_seconds > 1800` or
`max_attempts > 2`, followed by one new focused fixture attempt.

First send a new exact confirmation report for the existing
`G6-ACC-WC02-IMPLEMENTATION-20260928-001` `HUMAN_REQUIRED` response. Do not
patch or run the new fixture until its matching positive confirmation is applied.
Then perform only the bounded repair, publish its fixed commit for review, and
stop. WC-02 is not yet accepted; WC-03, Day selection/Go, model/service work,
credential actions, paid work, and destructive Git remain excluded.

## Current maintenance — rejection recovery (2026-09-28)

Human explicitly requested implementation and design update of the missing
post-rejection path. Scope: G4 §15.1 deterministic transport recovery, bounded
create-only replacement request/trigger, readback, response/application tracking,
persistent dashboard escalation. No WC-02 source execution in this maintenance.
Record: docs/review-records/REVIEWER_REJECTION_RECOVERY_2026-09-28.md.
On the matching review of this maintenance, record the checkpoint with NO_REPORT;
deployment/restart and live recovery proof are distinct from fixture results.

## Current G6 checkpoint — WC-02 new work-window review (2026-09-28)

The matching foreground route review has been applied, but the former 30-minute
G6 window had only about five active minutes remaining before WC-02 source or
fixture work.  Human now explicitly approved one new window with
「新しい作業枠を承認します。」.  Record and exact limits:
docs/review-records/G6_WC02_BUDGET_AUTHORITY_2026-09-28.md.
The first delivery `G6-ACC-WC02-WINDOW-20260928-001` was retained fail-closed:
its PR trigger omitted `AUTHORITY_RECORD` and the Watcher recorded
`REQUEST_BINDING_MISMATCH_AUTHORITY_RECORD`.  Do not alter that fixed request.
Replacement `G6-ACC-WC02-WINDOW-20260928-002` carries the complete same binding;
await its full matching positive response before patching.  It is the same
decision `AUTH-G6-WC02-WINDOW-20260928-001`, not a new request to the human.
The new window is 30 ACTIVE_WORK minutes, starts at zero only after that response,
and retains the existing 0/2 fixture cap and WC-02 scope.

The Watcher child may only record this window-review checkpoint (NO_REPORT on a
positive result); it is not the approved source-writing actor and must not retry
the failed WC-02 patch.  Foreground chat owns the minimal implementation and
fresh-process fixtures after review.  No service reload, Day/model work, new host
writer, or broader card begins.  The old budget HUMAN_REQUIRED entry lacks
`REVIEWED_COMMIT`; retain it as unbound historical bookkeeping without inventing
confirmation or hand-editing state.  Maintenance replies below remain limited to
their own IDs and cannot start WC-02.

## Current maintenance — reviewer progress visibility (2026-09-28)

Human requested visible progress in the dashboard or this chat. Implement a read-only
dashboard projection of the existing persisted report registry: pending/human waits,
processed records, exact file/comment links, timestamps, and explicit stale/offline
status. Record: docs/review-records/REVIEWER_PROGRESS_UI_2026-09-28.md.
No Watcher/state contract changes, restart, replay, chat automation or WC02 work.
On acceptance of REVIEWER-PROGRESS-UI-20260928-001, record this UI-only checkpoint
and return NO_REPORT; do not begin another stage. Concrete review gaps remain scoped
to this display. Older maintenance instructions below are historical checkpoints.

## Current maintenance — file-response reader (2026-09-28)

### Live deployment verified; completion-review checkpoint

Human said "おけ。進めてください。" after the full matching file review
FILE-WATCHER-REVIEW-20260928-001 (blob 3a1919ad241691cb8a751cab91b021e9a8be4fae)
requested deployment of 5447427 and live/restart verification. The foreground
chat completed these checks: the review was APPLIED by one live continuation;
FILE-WATCHER-LIVE-ACK-20260928-001 became ACKNOWLEDGED without another continuation;
both survived a restart without replay. Evidence is appended to the record below.
Completion report FILE-WATCHER-DEPLOYMENT-20260928-001 requests acceptance of this
transport maintenance only. On matching acceptance, read the full response and
record only that bounded checkpoint with `{"action":"NO_REPORT"}`; no duplicate
deployment/test/report, WC02, or next-stage start. Rejection must retain its concrete
gap. Do not edit watcher state by hand. The separate WC02 authority wait remains.

Human requested design and implementation of file replies in the existing Watcher.
Scope/DoD: explicitly opted-in new reports, immutable request/response correlation,
pending-file revalidation, informational ACK without execution, restart deduplication
and unchanged legacy comment handling. Record:
`docs/review-records/FILE_RESPONSE_WATCHER_2026-09-28.md`.
Deliver source and focused fixture evidence for review. Runtime reload and live
continuation are separate deployment evidence, not implied by passing fixtures.
WC02's host source-write/reload handoff remains HUMAN_REQUIRED under reply
5867480489; this transport implementation does not grant that authority.

## Active engineering work — G6 dependency-order continuation (2026-09-28)

- Latest human instruction: 「では設計変更し、進めてください。」
  Decision `AUTH-G6-CONTINUITY-20260928-001`, recorded in
  `docs/review-records/G6_CONTINUITY_2026-09-28.md`.
- Objective: implement the approved G5 cards serially within G6. G4 §14,
  G5 §3.1 and WORKING_RULES define card selection and genuine stop boundaries.
- Current checkpoint: continuity design is being submitted under
  `G6-ACC-CONTINUITY-20260928-001`; await its matching response after publication.
  On positive review, consume WC-01 evidence at bf34b6a and review 5865174825,
  then begin WC-02 admission/preflight using isolated fixtures. Do not stop merely
  after recording the design review. If prerequisites fail, repair within the card.
- WC-02 DoD: contract/scope/Git/permission/budget/external-prerequisite admission
  returns only permitted preflight or a recorded blocker; no Day execution.
  Evidence must show valid admission and dirty Git, unknown permission, missing
  limits and contract mismatch rejection. See G5 WC-02 for target files/limits.
- On each card: record evidence, next eligible card and remaining work-window
  time/retry limits; retain the 30-minute ACTIVE_WORK ceiling and two-attempt cap.
  Review response resets only the progress counter, not the work-window budget.
- Stage DoD: G5 implementation cards have traceable evidence and required review;
  separately report VC-11 actor evidence and unavailable product-E2E inputs.
  G6 completion requires its own completion review. G7/G8 and product Day/Go,
  models, service operations, authentication and paid work remain separate.

## Historical checkpoint — chat approval handoff (2026-09-28)

The following card-only stopping instructions describe the earlier completed
handoff. The later continuity decision above supersedes their WC-02 restriction;
their original records and already-applied responses must not be replayed.

Human selected approval completion in this chat and instructed 「対応してください。」.
Apply WORKING_RULES' chat approval policy, deploy the bounded confirmation handling,
and send existing G6 authority for Reviewer confirmation under a new report ID.
Canonical decision/progress record: `docs/review-records/CHAT_APPROVAL_HANDOFF_2026-09-28.md`.
No repeat human approval is needed solely for cross-chat visibility. Once the
confirmation reply is applied, record only its allowed effect and the WC-01
review result. If necessary, reconcile the older G5 authority wait through the
same new-report confirmation path using its existing direct approval/acceptance
evidence; do not request a fresh human approval or replay its old response.
This maintenance authorizes reloading the existing local watcher implementation;
it does not select WC-02, another Day, or authorize model execution.

## Historical checkpoint — G6 WC-01 (2026-09-28)

- Human instruction: 「Reviewerからの返信を確認後、G6を開始してください。」
- G5 exit: accepted only at `4a2b7a2269adae8318903179b10bb59ef424b145`,
  Reviewer response `5864471565` to `G5-ACC-REVIEW-20260928-004`.
- Active card: G5 v2 WC-01, RunIntent/RunControl contract and isolated JSON tests.
  Select the first implementation card in the approved dependency order; reuse the
  already published WC-00 baseline. This is not permission to execute a Day.
- Record, scope, evidence and checkpoint:
  `docs/review-records/G6_WC01_2026-09-28.md`.
- DoD: versioned JSON round-trip, duplicate ID rejection, identity mismatch
  rejection, current/history separation, legacy snapshot compatibility.
- Stop: WC-01 implementation/self-check done, awaiting its matching review;
  do not automatically start WC-02, G7/G8, services, models or a research Day.

## Product operation (unchanged; no selected Day)

- **System:** AI Control Center Day Runner v1
- **Current scenario:** LocalLLM-Lab Day 1-14
- **Authoritative scenario/runbook:**
  `C:\LocalLLM-Lab\docs\runbooks\work-plan-day1-14.md`
- **Interaction model:** The human selects one Day and presses **Go**. Control
  Center executes that selected Day autonomously under
  the externally frozen `docs/DAY_RUNNER_EXECUTION_SPEC.md` and stops only at selected-Day completion
  or a genuine human/external authority boundary.
- **Active task-specific DoD:** The selected Day Contract and its completion
  criteria. Until a Day is selected, there is no active Day-specific DoD.
- **Next operational action:** Wait for the human to select a Day.

Do not automatically advance to another Day, implement scenario switching, or
start Day 5 or another research Day because maintenance work has finished.
