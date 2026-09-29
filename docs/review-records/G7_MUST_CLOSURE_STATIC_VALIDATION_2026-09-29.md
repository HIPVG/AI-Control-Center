# G7 unresolved-MUST closure — product-path static validation

## 1. Scope

- Action class: `VALIDATION`
- Authority: `AUTH-G7-MUST-CLOSURE-20260929-001`
- Intermediate result retained: `CONDITIONAL_PASS` for the already accepted fixture
  and historical-actor boundaries
- Candidate live case: Day 6, not started
- Operations performed: current source/config/Git readback only
- Operations excluded: service/browser start, Day selection/Go, model, Watcher,
  delivery, credential change, spending, LocalLLM-Lab modification and test rerun
- Cost: `0 JPY`; token/model use: `NOT_APPLICABLE`

The first supplemental check asks whether the product route can, without bypassing
its safety boundary, carry one selected run through Go, execution, Evidence,
repair/review, telemetry and dashboard readback. A missing connection is an observed
implementation gap, not an input-blocked E2E.

## 2. Observed product-path discontinuities

### 2.1 Go stops before execution and does not persist selection

- `frontend/app.js` binds the Go button only to `requestGoPreview()`.
- That function calls only `POST /api/local-llm/day/go` and explicitly renders
  `Day execution was not started.` It does not call the existing
  `/api/local-llm/day/{day}/start` route.
- `backend/app.py` maps `/api/local-llm/day/go` to
  `ControlCenterEngine.prepare_local_llm_day_go()`.
- `LocalLLMDayProgram.prepare_go()` documents and implements preflight without Day
  start, returns `execution_started: false`, and returns `self.view()` without
  assigning the new RunIntent to the saved Day snapshot.
- The public API supplies only the Day. Trusted permission and external prerequisite
  facts default to unknown, so the public Go route cannot obtain an admissible product
  transition merely from browser input.

This proves that A01's product Go-to-execution path is absent. Starting the separate
legacy `/start` route would bypass the new immutable RunIntent/admission chain rather
than validate it, so it is not an acceptable workaround.

### 2.2 The dashboard read model is not fed by Go or Day runtime

- `backend/app.py` constructs `run_read_model` once with
  `empty_run_read_model(at=started_at)`.
- Repository search finds no production assignment or update of that object after
  startup; `/api/local-llm/runs` only calls `run_read_model.read()`.
- The Go result renders the older Day snapshot, while WC-09/WC-10's richer current,
  history, admission, criteria, review, telemetry and human-decision projection is
  not composed from the live Day controller.

Therefore A05 cannot be verified by an actual browser/readback under the same run ID.
It would continue to show the empty read-model projection independently of the Go
preview or legacy Day controller.

### 2.3 G6 contract components are not composed into one runtime run

Repository reference search finds the production definitions of
`CompletionEvidenceEvaluator`, `RepairRecoveryController`, `ReviewControl`,
`ReviewContinuationControl`, `HumanDecisionControl` and `JsonRunTelemetryStore`, but
no production orchestration reference that composes those components with the Go
RunIntent and `LocalLLMDayProgram` execution. Their accepted tests call the contract
classes directly.

Consequently:

- A02 typed Evidence completion is not attached to the actual product run;
- A03 repair/revalidation state is not attached to that run;
- A04 review continuation/human decision state is not attached to that run;
- A06 telemetry persistence is not attached to that run; and
- no product E2E can demonstrate A01–A06 under one run ID with the current wiring.

### 2.4 Current LocalLLM-Lab baseline is not silently normalized

Read-only Git inspection observed `C:/LocalLLM-Lab` at
`e33b0a410fb8647711f02ae4e6e0b66472e6eff0`, ahead of `origin/main` by 11 with
tracked modifications and untracked files. This work is preserved. No reset, clean,
checkout, staging, commit or Day action was performed. Even after reconciliation or
explicit scope admission, the product-path gaps above would still prevent the
required same-run proof.

## 3. Requirement result

| Requirement | Prior intermediate evidence | Supplemental product result |
|---|---|---|
| A01 | fixture `PASS` | `FAIL`: product Go ends at preview/preflight and is not connected to governed Day execution. |
| A02 | fixture `PASS` | `FAIL`: typed completion evaluator is not composed with the actual run. |
| A03 | fixture `PASS` | `FAIL`: repair/revalidation controller is not composed with the actual run. |
| A04 | fixture plus one historical actor path `PASS` | `FAIL` for the required current same-run product composition; historical delivery cannot fill the missing runtime link. |
| A05 | API/projection/DOM-contract fixture `PASS` | `FAIL`: the live API read model is initialized empty and is not updated from Go/Day state. |
| A06 | telemetry fixture `PASS` | `FAIL`: telemetry store is not composed with the actual run. |

These are implementation-path failures, not test-harness failures and not missing
human inputs. Running a live Day or browser flow cannot cure them and would create
external effects without the required evidence chain.

## 4. G7 disposition and return point

- The accepted `CONDITIONAL_PASS` remains valid only as an intermediate statement
  about deterministic fixtures and one historical actor trace.
- The proposed G7 exit disposition is now `RETURN`.
- Return to G6 for a bounded integration plan that connects one immutable RunIntent
  and RunRecord through admission, safe Day execution, typed Evidence, repair/review
  state, telemetry persistence and the read-only dashboard projection.
- Do not use the legacy direct-start route as proof unless it is placed behind the
  same admission/run identity and preserves all required controls.
- After a fixed G6 implementation is reviewed, rerun only the smallest G7 product
  E2E necessary to cover A01–A06. Day 6 and its limits remain subject to a fresh
  admission check; dirty LocalLLM-Lab work must remain preserved.
- A control-design contradiction returns to G4. None is asserted by this static
  validation; the observed defect is missing G6 runtime composition.

`ARTIFACT_QUALITY_CHECK: PASS` for this read-only static validation. Next boundary is
review of the `RETURN` decision. No live operation may begin from this record.
