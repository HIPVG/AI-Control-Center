# G6 repair plan — same-run Day-state projection after execution

## 1. Identity and boundary

- Status: `PLAN_PROPOSED`; human implementation authority pending
- Return source: accepted `G7-PRODUCT-E2E-20260930-004`
- Reviewed evidence commit: `18be053bde907f646737bfd2f36753585d8e051d`
- Product implementation baseline: `7b849803de140454b9f67beca98c52132a7bdb6f`
- Existing design: G4 v2 and the accepted G6 runtime-composition plan
- Action class after explicit authority: `IMPLEMENTATION`

This repair closes one already-designed composition invariant: after the Day
executor has settled, the durable RunRecord must reflect the trusted Day snapshot
for the same run. The existing `RunExecutionComposition.project_day_state()` owns
identity, contract, Evidence and required-review checks. The gap is that production
`RunCoordinator.go()` returns the executor result without invoking that projection.

The repair does not change the state model, create a second state machine, enable
real mode, retry the Day, execute a model or reinterpret `REAL_MODE_REQUIRED`.

## 2. Selected approach and rejected shortcuts

Selected: inject one post-execution projection callback into `RunCoordinator` from
the existing production `RunProductComposition.execution.project_day_state` path.
After the executor has finished and its returned run ID exactly matches the immutable
RunIntent, the coordinator invokes the callback once for that run and includes the
projection outcome in the Go response. The callback reads the persisted Day snapshot;
the executor result does not directly set RunControl fields.

Rejected shortcuts:

- duplicating Day-to-RunControl mapping in `RunCoordinator`: it would create a second
  projection implementation and bypass the accepted guards;
- accepting state or blocker values from browser or executor response fields: those
  inputs are not the authoritative Day snapshot;
- projecting before executor completion or by polling from the request handler: the
  Day state may not yet be settled and duplicate application becomes possible;
- converting projection failure into a successful Go: identity or persistence
  failure must remain explicit and fail closed;
- changing `codex.mode`, granting runtime authority or issuing another Go: those are
  separate G7 inputs and are outside this implementation defect.

## 3. Single repair card

### SP-00 — post-execution same-run projection

Primary scope:

- add the narrow projection callback boundary to `RunCoordinator`;
- wire it in `ControlCenterEngine` to the already-created
  `RunProductComposition.execution.project_day_state` instance;
- preserve the current callback-free behavior only for deliberately isolated unit
  construction, or require an explicit fail-closed callback in production;
- add focused coordinator/product-composition assertions.

Required behavior:

1. Admission and initial RunRecord persistence still precede every Day effect.
2. Blocked admission never invokes the executor or projection callback.
3. After the executor returns, its run ID must exactly match the immutable intent
   before projection can be attempted.
4. Projection reads the settled `LocalLLMDayProgram.snapshot` and reuses all existing
   current-run, snapshot-run, Day, contract, Evidence and review guards.
5. A successful projection updates exactly the current RunRecord once and is exposed
   in the Go result; restart/readback shows the same state, blocker and resume target.
6. A rejected or failed projection remains explicit (`DAY_STATE_PROJECTION_FAILED` or
   the existing concrete rejection reason), leaves unrelated runs unchanged and is
   never described as applied.
7. The executor is not repeated, projection cannot create a second external effect,
   and existing admission/preflight evidence remains attached to the same run.

The current production executor is synchronous: it returns only after the Day
program has reached its current settled stop. If a future executor returns before
settlement, it must provide a separately reviewed completion event that invokes the
same idempotent projection boundary; this card does not add a poller or background
worker in anticipation of that future case.

## 4. Required focused proof

Use disposable stores and an injected deterministic executor; do not start a real
service or Day.

- `REAL_MODE_REQUIRED` path: the injected production-shaped executor settles the Day
  at `EXTERNAL_ACTION_REQUIRED`; the same Go response and persisted/read-back
  RunRecord expose that state, blocker and `PREFLIGHT` resume target for one run ID.
- ordinary settled path: a non-terminal Day state is projected once without a second
  executor call and remains after Engine reconstruction.
- blocked admission: neither executor nor projection is called.
- executor run-ID mismatch: projection is not called and the prior RunRecord is
  unchanged.
- snapshot/current-run mismatch: the existing projection rejects before mutation;
  a same-Day, same-contract other run remains unchanged.
- projection exception or rejected result: Go reports the failure distinctly and
  does not claim successful durable application.
- regression: retain the accepted runtime-composition and authority-fact focused
  tests; do not broaden to the full repository merely for confidence.

The exact focused commands must be named before execution. Default limit is 30
ACTIVE_WORK minutes, at most two executions of each named command and 0 JPY.

## 5. Files, compatibility and design impact

Expected source scope is limited to:

- `backend/control/run_composition.py`;
- `backend/orchestrator/engine.py` or the existing production composition wiring;
- existing focused tests in `tests/test_run_product_composition.py` and, only where
  needed, `tests/test_run_execution_composition.py` or the authority composition
  fixture.

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

G6 repair DoD is satisfied only when one production-composed Go projects the settled
trusted Day snapshot to the exact current RunRecord through the existing guarded
projection, failure paths remain non-applying, restart readback agrees, focused
regression passes, and `ARTIFACT_QUALITY_CHECK: PASS` is recorded.
