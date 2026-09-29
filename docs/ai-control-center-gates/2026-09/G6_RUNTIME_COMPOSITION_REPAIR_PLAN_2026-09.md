# G6 return plan — same-run runtime composition

## 1. Identity, cause and boundary

- Status: `PLAN_ACCEPTED`; human implementation authority pending
- Plan acceptance: `G6-RUNTIME-COMPOSITION-PLAN-20260929-001`
- Reviewed plan commit: `12b93f7f2ff5d017ec38bd9fe5b14ed21a115c40`
- Return source: accepted `G7-MUST-CLOSURE-20260929-001`
- Return evidence: `b94b93bf1ad7accdf8a83fd4e40edd242529c787`
- Implementation baseline: `a30ed2303a85ff00ebbb5b0721bea4fe5c66ad0f`
- Design baseline: `G4_AI_CONTROL_CENTER_FUNCTIONAL_CONTROL_DESIGN_v2_2026-09.md`
- Existing implementation plan: `G5_AI_CONTROL_CENTER_IMPLEMENTATION_PLAN_v2_2026-09.md`
- Action class after separate human implementation authority: `IMPLEMENTATION`

G7 confirmed an implementation-composition gap, not a new requirement or control
design gap. G4 already requires one run identity from Go through admission, execution,
Evidence, repair/review, telemetry and dashboard. G6 implemented and fixture-tested
the individual contracts but did not compose them into the product runtime.

This plan adds only that missing composition. It reuses `RunIntent`, `RunControl`,
`RunRecord`, `JsonRunStore`, `CompletionEvidenceEvaluator`,
`RepairRecoveryController`, `ReviewControl`, `ReviewContinuationControl`,
`HumanDecisionControl`, `JsonRunTelemetryStore`, `RunReadModel` and
`LocalLLMDayProgram`. It does not replace their accepted contracts, add a framework,
change G4 state semantics, or execute a real Day.

## 2. Required invariants

1. One browser Go creates exactly one server-owned immutable `RunIntent`.
2. The initial `RunRecord` is persisted before any Day effect. A blocked admission
   persists the same run and blocker but starts no Day.
3. Trusted permission, Git, limits and external prerequisites are resolved server
   side. Browser input never supplies them.
4. An admissible run reaches the Day executor only through the same RunIntent and
   admission decision. The legacy direct-start route cannot bypass this path.
5. Every control, Evidence, repair/review, telemetry and read-model item carries the
   same run ID. Mismatch fails closed before state or external effects.
6. Run state evolution is durable and auditable. Existing state is not overwritten
   as if history never happened; current and historical projections remain distinct.
7. `/api/local-llm/runs` reconstructs current state from persisted sources at read
   time. A startup-time empty singleton is not current state.
8. `COMPLETE` still requires all validator-owned Evidence and any required review;
   execution end, exit code 0 or UI state alone cannot complete a run.
9. Restart, duplicate Go, duplicate response and repeated telemetry cannot create a
   second effect for the same identity.
10. Existing dirty work in AI-Control-Center and LocalLLM-Lab is not reset, cleaned,
    moved, broadly staged or silently adopted.

## 3. Dependency-ordered repair cards

### G6-RI-00 — durable run spine and guarded Go

Status: `ACCEPTED`; pack `G6-RI00-COMPLETION-20260929-001`, implementation commit
`dcbc29870f5725ccc62f3f7e74293cac1b2bdac0`.

| Field | Plan |
|---|---|
| Purpose | Compose the existing RunIntent/admission/RunRecord contracts into one server-owned Go transaction. |
| Primary paths | `backend/orchestrator/engine.py`, `backend/app.py`, `backend/control/run_store.py`, one small composition module if needed, and focused tests. |
| Required behavior | Go creates/persists one run; admission failure stores blocker/no Day effect; admission success delegates once to the Day controller under the same identity. Trusted facts are injected/resolved server-side. |
| Legacy route | `/api/local-llm/day/{day}/start` must delegate to the same guarded coordinator or fail closed. It may not remain an unguarded product bypass. |
| Persistence | Extend the JSON store behind its interface only as needed for append/versioned RunControl evolution and current/history selection. Preserve create-only identity and reject stale/mismatched updates. |
| Focused proof | blocked Go, admissible Go, duplicate Go, identity mismatch, restart readback, no-effect-before-persist, and no direct-start bypass. |
| Stop | If the existing Day controller cannot be bound without changing G4 semantics, stop and return to G4 with the exact contradiction. |

### G6-RI-01 — execution result, Evidence, recovery and review adapters

Status: `REJECTION_REPAIRED_AND_FOCUSED_VALIDATION_PASSED`; revised fixed review pending.

| Field | Plan |
|---|---|
| Purpose | Translate the existing Day controller's states/results into the accepted run-bound contracts without creating a second execution state machine. |
| Primary paths | composition module, existing Evidence/repair/review/human-decision components, minimal adapter tests. |
| Required behavior | Day state becomes RunControl for the same ID; provider results pass through `CompletionEvidenceEvaluator`; repair/revalidation and reviewer/human-decision state retain the same run/Day and return target. |
| Review boundary | Use injected deterministic review events in G6. Do not restart or redesign the real Watcher. Current actor behavior remains a G7 validation boundary. |
| Failure proof | wrong run/criterion/config, invalid Evidence, exhausted retry, stale/duplicate review and absent downstream effect remain non-completing with no cross-run mutation. |
| Stop | A required adapter that can only be achieved by weakening Evidence or review correlation returns to G4; otherwise implementation defects remain in this card. |

### G6-RI-02 — telemetry and live read-model composition

| Field | Plan |
|---|---|
| Purpose | Persist telemetry and build `/api/local-llm/runs` from the same stored run rather than the startup-time empty singleton. |
| Primary paths | `backend/app.py`, `backend/control/run_read_model.py`, `backend/control/run_telemetry_store.py`, composition module and API tests. |
| Required behavior | current/history, admission, criteria, review, human decision, runtime observation and telemetry are joined only by exact run ID; unknown stays unknown with source/reason. |
| UI effect | Existing dashboard consumes the composed read API. Go response and subsequent reads show the same run ID and authoritative next state; selection alone still has no effect. |
| Failure proof | Partial, corrupt or mismatched persisted data fails closed and never becomes current/complete. Restart readback retains one current run and history. |

### G6-RI-03 — integrated product-boundary fixture and handoff

| Field | Plan |
|---|---|
| Purpose | Demonstrate the complete in-process product route before returning to G7, without starting a real Day. |
| Required fixture | Actual FastAPI endpoints plus production composition root and a deterministic injected Day executor. No monkeypatch that bypasses the coordinator under test. |
| Success path | Selection has no effect; Go creates one run; admission starts the injected executor once; Evidence completes declared criteria; telemetry and read model expose the same run; terminal state is evidence-based. |
| Failure path | Blocked admission, invalid Evidence, controlled repair/revalidation, human/reviewer wait, matching continuation, retry exhaustion and restart readback preserve the same run and prohibit unauthorized effects. |
| Regression | Run the smallest existing A01–A06 tests affected by the wiring plus this integration fixture. Preserve warnings, attempts, full commands and outputs. |
| Handoff | If accepted, return to G7 for one bounded real service/browser/Day 6 E2E. G6 fixture success is not product E2E or G7 acceptance. |

## 4. Files, compatibility and migration

- Prefer a small composition module rather than adding behavior to models or
  duplicating logic across API handlers.
- Preserve existing persisted Day snapshots and reviewer ledgers. Do not migrate or
  rewrite them during implementation tests.
- New run data uses a dedicated versioned JSON directory behind the existing store
  interfaces. Tests use disposable directories.
- If an existing production state cannot be read under the new composition, report
  `INPUT_BLOCKED` with recovery instructions; do not infer or overwrite fields.
- API compatibility may retain the legacy start endpoint only as a guarded alias.
  Existing callers receive a deterministic rejection when required RunIntent or
  authority is absent.

## 5. Execution limits and review cadence

- Plan review is blocking; no implementation begins from this document alone.
- After human implementation authority, execute cards serially in dependency order.
- Default per-card window: 30 ACTIVE_WORK minutes, at most two executions of each
  declared focused command, 0 JPY. Reviewer wait is excluded.
- Token values are recorded only when actually measured; unknown is not zero.
- Each card receives a fixed commit and review before its result is consumed by the
  next card. A review correction within the same card does not authorize broader
  refactoring.
- No service/browser, real Day/Go, model, credential change, Watcher restart,
  destructive Git action, `main` modification or product acceptance occurs in G6.

## 6. DoD and return to G7

G6 repair is ready to return to G7 only when:

- the production composition root, not a test-only alternate path, enforces the ten
  invariants;
- G6-RI-00 through RI-03 have accepted fixed commits;
- one integrated fixture shows the same run ID through API, admission, execution,
  Evidence, recovery/review, telemetry and read model;
- direct-start and cross-run bypasses fail closed;
- restart/current/history behavior is deterministic; and
- `ARTIFACT_QUALITY_CHECK: PASS` is recorded.

Return to G7 authorizes validation planning only. Real Day 6, service/browser and
current actor operations still require the applicable G7 execution authority and
admission inputs.
