# G6 repair plan — product run reconciliation after real Day execution

## 1. Identity, cause and boundary

- Status: `PLAN_PROPOSED`; implementation not authorized
- Return source: accepted `G7-PRODUCT-E2E-20261001-007`
- Reviewed evidence commit: `91423c2e45fa5c4b35ee589c003adcdd3f39ac13`
- Affected product run: `run-8b9fb7cac4c948098af3e9aa7dfeaf8d`
- Product implementation baseline: `3e82626faebab8e9722939b92267deb51075d93b`
- Design baseline: G4 v2, G5 v2 and the accepted G6 runtime-composition/SP-00 plans
- Action class after separate human implementation authority: `IMPLEMENTATION`

The real Day 6 run proved three wiring defects in an otherwise completed execution:
validator-accepted Day Evidence was stored without product run/criterion identity;
the resulting terminal Day state could not pass the existing completion guard and
therefore stayed `PREFLIGHT` in the durable RunRecord; and actual attempt/token/
budget/cost-availability facts were not converted into run telemetry.

This is not a new state model or a reason to repeat the Day. G4 already requires
run-bound typed Evidence, evidence-based terminal state, and attempt/token/cost
telemetry with provenance and explicit unknowns. The repair composes the existing
Day output with those accepted contracts. Historical nullable Evidence remains
read-compatible but cannot complete a product run.

## 2. Required invariants

1. The immutable product `run_id`, selected Day, contract fingerprint and criterion
   identity are server-owned; no browser, model or artifact supplies them.
2. Each Evidence Record consumed by product completion has a non-null run ID and
   criterion ID matching the current RunIntent and the exact criterion being judged.
3. One validated observation may support multiple criteria only through separate
   criterion-bound records. It is not silently reused as an unbound record.
4. Malformed, nullable, stale, wrong-run, wrong-criterion, wrong-contract or
   wrong-configuration Evidence is retained only as historical input where
   applicable and cannot satisfy product completion.
5. The existing SP-00 post-save settlement notification remains the single product
   reconciliation boundary. It must not launch work, repeat the executor or create a
   second Day state machine.
6. `COMPLETE` reaches the durable RunRecord only after all criterion-bound Evidence
   passes the existing validators and any required review is verified.
7. Actual attempt count/limit, gross and cached input, derived uncached input,
   output tokens, budget decision/warning and cost value or explicit unavailability
   are captured from authoritative persisted Day/task facts for the same run.
8. Zero and unknown remain distinct. The 0 JPY authority limit is not fabricated as
   observed cost; unavailable measured cost is stored with reason and provenance.
9. Reconciliation is idempotent for an identical terminal snapshot. A conflicting
   second Evidence/telemetry/state value fails closed and does not overwrite the
   first durable fact.
10. Existing run, Day state, artifacts and review evidence remain immutable evidence;
    the implementation and fixtures use disposable state and never rewrite the
    accepted real-run package.

## 3. Dependency-ordered repair cards

### G6-PR-00 — strict Day-to-product Evidence binding

| Field | Plan |
|---|---|
| Purpose | Convert validator-accepted Day evidence into the existing strict product Evidence path under the current RunIntent and each criterion. |
| Reuse | `CompletionEvidenceEvaluator`, `EvidenceResultInput`, `EvidenceRecord`, the existing registry/validators and `RunExecutionComposition.evaluate_criterion()`. |
| Primary paths | `backend/control/local_llm_day_program.py`, `backend/control/run_execution_composition.py`, the smallest adapter/composition path required, and focused tests. |
| Required behavior | Server-owned settlement supplies current run/contract/criterion identity; provider output supplies only its measured value and provenance. Bound records replace nullable records only for product completion and use deterministic IDs. Shared evidence types create one record per criterion binding. |
| Fail closed | Null or mismatched identity, incompatible source/config fingerprint, validator failure and partial criterion evidence leave the criterion incomplete and the RunRecord non-terminal. No record is relabelled in place. |
| Focused proof | Day 6-shaped evidence binds to all four exact criteria; the shared `schema_contract` produces distinct criterion-bound records; wrong-run/criterion/config and nullable legacy records do not complete; restart readback preserves bindings. |

### G6-PR-01 — terminal run telemetry reconciliation

| Field | Plan |
|---|---|
| Purpose | Build one immutable `RunTelemetry` snapshot from the terminal persisted Day/task facts and attach it to the current product run. |
| Reuse | `RunTelemetry`, `TelemetryMetric`, `JsonRunTelemetryStore`, `RunProductComposition.record_telemetry()` and existing read projection. |
| Primary paths | telemetry model/store/composition, the Day settlement adapter, read-model tests, and only the minimal G5 WC-08 clarification required by a versioned telemetry extension. |
| Required behavior | Aggregate actual Codex attempts and token fields from the terminal task records; retain attempt limit from RunIntent; preserve the observed budget decision with source/time; record measured cost when available or explicit unknown reason when unavailable. |
| Compatibility | If an explicit budget-decision field requires telemetry schema v2, read schema v1 unchanged and write v2 only for new reconciled runs. Do not reinterpret old missing fields as zero or success. G4 semantics do not change. |
| Fail closed | Wrong-run task data, inconsistent totals, duplicate/conflicting telemetry, missing provenance or a known value without source is rejected before replacement. Exact replay is a no-op; conflicting replay is not. |
| Focused proof | Reconcile the accepted Day 6-shaped 528,695/474,112/54,583 input split, 8,131 output, one attempt, limit two, `TASK_BUDGET_EXCEEDED`, and unknown measured cost; confirm UI/read model shows values and sources under the same run. |

### G6-PR-02 — one terminal settlement and durable state projection

| Field | Plan |
|---|---|
| Purpose | At the existing post-save SP-00 boundary, reconcile strict Evidence and telemetry, then reuse `project_day_state()` to advance the same RunRecord. |
| Primary paths | existing settlement callback wiring, `RunProductComposition`/`RunExecutionComposition`, and focused composition tests. |
| Required order | terminal Day save → exact run/contract check → Evidence binding → telemetry reconciliation → existing guarded Day-state projection → readback. |
| Required behavior | A fully valid terminal snapshot becomes durable `COMPLETE`; partial or rejected reconciliation stays non-terminal with a concrete audited reason. No executor, Go, model, review or external effect is repeated. |
| Recovery semantics | An exact already-written telemetry snapshot does not block later state projection after a transient projection failure. Conflicting persisted facts remain fail-closed and require diagnosis rather than overwrite. |
| Focused proof | Early return remains `PREFLIGHT`; after terminal save, exact Evidence and telemetry appear before one `COMPLETE` projection; restart/API/dashboard agree. Evidence or telemetry failure prevents terminal projection and leaves prior RunRecord unchanged. |

### G6-PR-03 — integrated product-boundary fixture and G7 handoff

Use the production composition root, actual FastAPI Go/GET handlers, disposable JSON
stores and an injected deterministic Day executor. Do not start a service, browser,
real Day or model.

The success fixture must show one Go, one same-run executor effect, strict Evidence
for every declared criterion, terminal telemetry with provenance, one durable
`COMPLETE` RunRecord, and identical API/read-model state after reconstruction. The
failure fixture must cover cross-run Evidence/task data, incomplete Evidence,
conflicting telemetry, settlement before terminal save, and duplicate reconciliation
without a second effect. Retain the existing admission, required-review and SP-00
guards.

## 4. Expected source and document scope

Expected source scope is limited to the existing product-composition boundary:

- `backend/control/local_llm_day_program.py`;
- `backend/control/evidence_completion.py` only if its existing strict adapter needs
  a server-owned conversion entry point;
- `backend/control/run_execution_composition.py`;
- `backend/control/run_product_composition.py`;
- `backend/control/run_telemetry_store.py` and the telemetry/read-model models only
  where schema compatibility requires it;
- `backend/orchestrator/engine.py` only for production wiring;
- focused tests adjacent to those components.

No G4 state or role change is required. G5 WC-05 already requires bound typed
Evidence and WC-08 already requires same-run attempt/token/cost telemetry. If PR-01
adds a versioned budget-decision field, update only the WC-08 contract description
and its model/read compatibility table with the implementation; do not reopen G4 or
unrelated cards.

## 5. Execution limits and stop conditions

- Plan acceptance does not authorize implementation or tests.
- After separate human authority, execute PR-00 through PR-03 in dependency order.
- Default proposed limit: 30 ACTIVE_WORK minutes for the stage, at most two
  executions of each named focused command, and 0 JPY. Reviewer wait is excluded.
- Each card receives a fixed commit and review before its result is consumed by the
  next card, following the existing G6 continuity rule.
- Stop for a genuine G4 contradiction, new source/write authority, migration of
  accepted real evidence, exhausted limit or an unrecoverable conflicting fact.
- Do not issue another Go, run a model, start a service/browser, operate Watcher,
  change credentials, modify `main`, begin G8 or claim product acceptance.

## 6. DoD and return to G7

The repair is ready to return to G7 only when:

- every Evidence item used for completion is bound to the exact run and criterion;
- terminal Day state reaches the same durable RunRecord only after that Evidence and
  required review pass;
- actual attempts, token split, budget warning and cost availability are persisted
  and read back with provenance for that run;
- exact replay is non-duplicating and conflicting/cross-run input is fail-closed;
- production-composed deterministic fixtures survive reconstruction;
- focused regression passes and `ARTIFACT_QUALITY_CHECK: PASS` is recorded; and
- G6 receives a separate completion review.

Return to G7 permits a separately authorized product revalidation decision only. It
does not itself authorize another Day 6 Go, model execution, G8 or product acceptance.
