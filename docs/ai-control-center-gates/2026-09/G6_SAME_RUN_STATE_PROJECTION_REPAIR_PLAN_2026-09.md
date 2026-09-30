# G6 repair plan — same-run Day-state projection after execution

## 1. Identity and boundary

- Status: `PLAN_REVISED_AFTER_REJECTION`; human implementation authority pending
- Return source: accepted `G7-PRODUCT-E2E-20260930-004`
- Rejected revision: `G6-SAME-RUN-STATE-PROJECTION-PLAN-20260930-001` at
  `575108e0a73d1d8ffdffb95724c0341e0e2ef108`
- Reviewed evidence commit: `18be053bde907f646737bfd2f36753585d8e051d`
- Product implementation baseline: `7b849803de140454b9f67beca98c52132a7bdb6f`
- Existing design: G4 v2 and the accepted G6 runtime-composition plan
- Action class after explicit authority: `IMPLEMENTATION`

This repair closes one already-designed composition invariant: after the asynchronous
Day worker has settled and persisted its final current state, the durable RunRecord
must reflect the trusted Day snapshot for the same run. The existing
`RunExecutionComposition.project_day_state()` owns identity, contract, Evidence and
required-review checks. The gap is that no post-settlement notification invokes it.

Revision 001 incorrectly treated the default executor's return as settlement.
`LocalLLMDayProgram.start()` starts `_execute` on another thread and returns
immediately, so a coordinator return-time projection can only observe `PREFLIGHT`.

The repair does not change the state model, create a second state machine, enable
real mode, retry the Day, execute a model or reinterpret `REAL_MODE_REQUIRED`.

## 2. Selected approach and rejected shortcuts

Selected: add one post-settlement notification boundary to the existing Day worker.
The thread target becomes a narrow wrapper around `_execute`. After `_execute` exits,
the wrapper verifies the captured expected run ID, requires a non-active Day state,
performs one final successful `_save`, creates an immutable settlement notification,
and invokes the injected callback once for that execution episode. Production wires
the callback to the existing
`RunProductComposition.execution.project_day_state` path.

The callback revalidates the current RunRecord and persisted Day snapshot under the
same run ID before mutation. The asynchronous Go response continues to mean only that
execution started; it must not claim final projection. Subsequent read API calls show
the projected state after the settlement notification has completed.

Rejected shortcuts:

- duplicating Day-to-RunControl mapping in `RunCoordinator`: it would create a second
  projection implementation and bypass the accepted guards;
- accepting state or blocker values from browser or executor response fields: those
  inputs are not the authoritative Day snapshot;
- projecting on `RunCoordinator.go()` or executor return: `start()` has only launched
  the worker and normally still exposes `PREFLIGHT`;
- polling from the request handler or a new background watcher: it introduces races,
  duplicate application and a second lifecycle owner;
- converting projection failure into a successful Go: identity or persistence
  failure must remain explicit and fail closed;
- changing `codex.mode`, granting runtime authority or issuing another Go: those are
  separate G7 inputs and are outside this implementation defect.

## 3. Single repair card

### SP-00 — post-settlement same-run projection

Primary scope:

- add the narrow settlement callback boundary to `LocalLLMDayProgram`'s worker
  lifecycle without changing its state machine;
- wire it in `ControlCenterEngine` to the already-created
  `RunProductComposition.execution.project_day_state` instance;
- keep callback-free construction available for isolated legacy/unit fixtures, while
  production supplies the callback explicitly;
- add focused worker-ordering and product-composition assertions.

Required behavior:

1. Admission and initial RunRecord persistence still precede every Day effect.
2. Blocked admission never invokes the executor or projection callback.
3. `start()` and the default executor return without projecting; this return is not a
   settlement or completion signal.
4. Each worker captures the expected run ID when created. Only after `_execute`
   exits, the Day state is non-active and a final `_save` succeeds may that worker
   emit one settlement notification.
5. The notification and current Day snapshot must both exactly match the immutable
   current RunIntent before projection can be attempted.
6. Projection reads the settled `LocalLLMDayProgram.snapshot` and reuses all existing
   current-run, snapshot-run, Day, contract, Evidence and review guards.
7. A successful notification updates exactly the current RunRecord once for that
   execution episode; later readback and restart show the same state, blocker and
   resume target. The initial Go response does not claim this later effect.
8. A rejected or failed projection remains explicit (`DAY_STATE_PROJECTION_FAILED` or
   the existing concrete rejection reason), leaves unrelated runs unchanged and is
   never described as applied.
9. The executor is not repeated, projection cannot create a second external effect,
   and existing admission/preflight evidence remains attached to the same run.

The one-time guarantee is per worker execution episode. A later explicitly authorized
Resume may create a new worker and therefore a new settlement notification for the
same run; it must still pass the same guards. SP-00 adds no Resume authority or retry.

## 4. Required focused proof

Use disposable stores and an injected deterministic executor; do not start a real
service or Day.

- deterministic ordering fixture: hold the worker before its terminal save and prove
  that `start()`/Go returns while RunRecord remains `PREFLIGHT`; release it, then prove
  the terminal snapshot save occurs before exactly one projection callback.
- `REAL_MODE_REQUIRED` path: the worker settles at `EXTERNAL_ACTION_REQUIRED`; after
  notification, persisted/read-back RunRecord exposes that state, blocker and
  `PREFLIGHT` resume target for the same run ID.
- ordinary settled path: one non-active Day state is projected once without a second
  executor call or notification and remains after Engine reconstruction.
- blocked admission: neither executor nor projection is called.
- captured worker run-ID or notification mismatch: projection is not called and the
  prior RunRecord is unchanged.
- snapshot/current-run mismatch: the existing projection rejects before mutation;
  a same-Day, same-contract other run remains unchanged.
- final Day snapshot save failure: no notification is emitted; projection exception
  or rejected result is audited distinctly and never claimed as durable application.
- regression: retain the accepted runtime-composition and authority-fact focused
  tests; do not broaden to the full repository merely for confidence.

The exact focused commands must be named before execution. Default limit is 30
ACTIVE_WORK minutes, at most two executions of each named command and 0 JPY.

## 5. Files, compatibility and design impact

Expected source scope is limited to:

- `backend/control/local_llm_day_program.py`;
- `backend/orchestrator/engine.py` or the existing production composition wiring;
- existing focused tests in `tests/test_local_llm_day_program.py` and
  `tests/test_run_product_composition.py`, and only where needed
  `tests/test_run_execution_composition.py`.

No persisted schema migration is planned. Existing RunRecord, preflight facts,
telemetry and Day snapshots remain readable. No G4 or G5 semantic change is required:
G4 and the accepted G6 runtime-composition plan already require durable same-run
state after execution. This is an implementation wiring defect, not a new contract.

## 6. Stop, review and return

- This plan does not authorize implementation or test execution.
- After separate human implementation authority, implement only SP-00 and its focused
  proof, then publish one fixed completion pack and stop for review.
- No service/browser, Go, real Day, model, real-mode/config change, Watcher,
  credentials, spending, G8 or product acceptance occurs in G6.
- Accepted SP-00 returns to a separately authorized G7 product revalidation. It does
  not consume or recreate product execution authority by itself.

G6 repair DoD is satisfied only when a production-composed asynchronous Day worker
persists its settled trusted snapshot before emitting exactly one same-run notification
for its execution episode, the existing guarded projection updates the exact current
RunRecord, early-return and failure paths remain non-applying, restart readback agrees,
focused regression passes, and `ARTIFACT_QUALITY_CHECK: PASS` is recorded.
