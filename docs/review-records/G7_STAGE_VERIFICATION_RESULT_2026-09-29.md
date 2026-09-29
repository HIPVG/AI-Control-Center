# G7 — evidence mapping and proposed stage result

## 1. Identity and decision boundary

- Action class: `VALIDATION`
- Implementation baseline: `a30ed2303a85ff00ebbb5b0721bea4fe5c66ad0f`
- Accepted G7 plan: `3b267223d507aefe113df671a9331be5c1fc0a13`
- Accepted GV-00/GV-01 evidence: `7e28c55975a42985e10cfe4b2c9d2da3a194fb3a`
- Accepted GV-02 evidence: `61d8d10d0f899160033e3b84bab7f855c7b3dee1`
- Policy: `docs/WORKING_RULES.md` at
  `60c0fe7dcf8935fad4c6d3818256a94e95965501`
- Proposed G7 result: `CONDITIONAL_PASS`

This result evaluates only the evidence already admitted by the accepted G7 plan.
No new test, delivery, service, browser, Watcher, Day/Go, model, credential or paid
operation was performed in GV-03. A fixture pass is not promoted to product E2E, and
the one historical actor trace is not promoted to current operational readiness.

## 2. A01–A06 evidence mapping

The `G7 classification` column uses the plan's required vocabulary. `PASS` is scoped
to the named proof boundary. A product requirement that still needs a live input is
shown as `INPUT_BLOCKED`; an observable product path that was not exercised is shown
as `NOT_EVALUABLE`.

| ID | Verified evidence | G7 classification | Condition / remaining gap | G8 effect |
|---|---|---|---|---|
| A01 selected-Day Go and state | WC-04/GV-01 prove, at deterministic fixture level, selection without a request, Go of only the selected Day, one run ID through RunIntent and admission, and a stop at `PREFLIGHT`. | Fixture boundary `PASS`; product boundary `INPUT_BLOCKED`. | Actual service/browser selection, Go and persisted same-run readback require a selected Day and explicit live-operation authority. | No product-path acceptance; G8 may not treat Go/UI as live-verified. |
| A02 plan, Evidence and judgment | WC-05/GV-01 prove typed Evidence, identity/fingerprint binding, validator use, and rejection of empty, wrong-type and wrong-run evidence. | Fixture boundary `PASS`; product boundary `INPUT_BLOCKED`. | No actual Day has produced and completed the typed Evidence set through the product orchestration path. | Criterion completion is contract-verified only. |
| A03 repair and revalidation | WC-06/GV-01 prove scope/Git/budget/attempt guards, the two-failure human boundary, no third attempt, and exact-response return to the same run/Day `PREFLIGHT`. | Fixture boundary `PASS`; product boundary `NOT_EVALUABLE`. | No real permitted repair and revalidation success was exercised. A live E2E must preserve the same guards and retry history. | Repair readiness remains conditional; a wiring mismatch returns to G6, not a new G7 patch. |
| A04 review, stop and recovery | WC-07/07A/07B and GV-01 prove correlation, duplicate/stale/timeout rejection, continuation state and human-decision guards. GV-02 independently verifies one historical actual actor path from unique reply through `NO_REPORT`, `APPLIED` and the named downstream effect. | Fixture boundary `PASS`; historical actor boundary `PASS`; current operation `NOT_EVALUABLE`. | Current Watcher liveness and real external-disconnect recovery were not tested and are not inferred from persisted `running=true`. | The historical path is usable evidence, but it is not current availability evidence. |
| A05 actual-state dashboard | WC-09/WC-10/GV-01 prove current/history separation, explicit unselected/`PREFLIGHT`/stop/decision states, sourced zero values and unknown values at API/projection/DOM-contract level. | Fixture boundary `PASS`; product boundary `INPUT_BLOCKED`. | No real browser display was compared with persisted state for the same actual run. | Dashboard product acceptance remains blocked. |
| A06 outcome, relay and cost verification | WC-08/GV-01 prove run-bound intervention, relay, attempts/limits, token/cost source and unknown handling, duplicate rejection, and create-only persistence. | Fixture boundary `PASS`; product boundary `INPUT_BLOCKED`. | No real Day result or actual telemetry was captured and reconciled under one run ID; zero relay/cost is not inferred. | Product telemetry and result acceptance remain blocked. |

No A01–A06 fixture or admitted historical-actor check is `FAIL`. The product-facing
Must boundaries are not all evaluated, so `PASS` for G7 as a whole would overstate
the evidence. `RETURN` is not selected because the available evidence does not show a
contract, implementation or validation failure requiring rework. The proportional
result is therefore `CONDITIONAL_PASS`.

## 3. Test-completeness result

| Completeness concern | Result | Evidence limit |
|---|---|---|
| Baseline and test provenance | `PASS` | G6 baseline ancestry, unchanged target code/tests, and preserved REJECT history were checked in GV-00. |
| Fixed input and production path | `PASS` for named shared functions; otherwise `NOT_EVALUABLE` | Stubbed endpoints and direct class calls remain lower-boundary evidence, not product orchestration evidence. |
| Answer leakage / case fixation | `PASS` | No inspected production branch used fixture-only IDs; valid and invalid generalized conditions are asserted. No model prompt was used. |
| Output, time and failures | `PASS` | Exact commands, UTC times, duration, exit code, warnings and output were retained for 96 Python and four Node tests, each run once. |
| Failure/disconnect preservation | Fixture `PASS`; real external boundary `NOT_EVALUABLE` | Invalid identity/evidence/envelope, duplicate, timeout and exhausted retry are retained without success promotion; no live disconnect was injected. |
| Independent actor evidence | Historical slice `PASS` | One fixed VC-11 path was independently reread; current liveness is not covered. |

## 4. Conditions attached to the proposed result

These are acceptance conditions, not authorization to execute them.

| Condition | Required evidence | Owner / authority | Deadline and failure state |
|---|---|---|---|
| C-G7-01 product path | One explicitly selected Day through actual service/browser selection and Go, with the same run ID in RunIntent, admission, persisted state and dashboard. | 広瀬剛 selects and authorizes the live boundary; CODEX executes; ChatGPT verifies. | Before G8 product-readiness acceptance. If absent, A01/A05 remain `INPUT_BLOCKED`. |
| C-G7-02 actual Evidence/repair behavior | The same actual run produces typed Evidence; any exercised repair preserves scope, Git, budget, attempts and return state. A repair need not be manufactured merely to pass. | Same roles; fault injection or repair authority requires a separate explicit decision. | Before claiming A02/A03 product E2E. A discovered wiring or contract mismatch returns to G6; a design mismatch returns to G4. |
| C-G7-03 current review operation | If current autonomous review is required by the selected run, capture exact correlation, delivery, continuation, application and downstream effect; do not substitute the historical trace for current liveness. | Existing delegated review roles within current authority; actual transport/auth failure returns to human authority. | Before claiming current A04 operational readiness. If not exercised, retain `NOT_EVALUABLE`. |
| C-G7-04 actual telemetry | Reconcile result, relay/intervention, attempts/limits, token and cost values with sources under the same actual run ID; unknown remains unknown. | CODEX records; ChatGPT verifies; 広瀬剛 decides product acceptance. | Before A06 product acceptance. If absent, A06 remains `INPUT_BLOCKED`. |

A single bounded product run may satisfy multiple conditions, but only when its
recorded evidence actually covers them. Missing conditions are not automatic
engineering tasks and do not authorize G8, Day/Go or external effects.

## 5. Return and stop rules

- A product wiring or implementation mismatch returns to G6 with the failing boundary
  and fixed evidence; G7 does not repair it.
- A requirement or control-design mismatch returns to G4.
- Missing Day, environment, authority, credential or product decision remains a human
  input boundary and is not guessed.
- G7 result review is blocking. Do not start G8, a Day/Go, live service/browser work,
  model execution, credential change, spending or product acceptance from this record.
- ChatGPT reviews this proposed result. After review, 広瀬剛 decides the G7 exit and
  any separate authority needed to satisfy the conditions.

## 6. Artifact quality

- Every A01–A06 row identifies the proof layer and prevents fixture-to-E2E promotion.
- Accepted commits and remaining gaps are explicit and traceable.
- No test count, exit code, file existence or self-report is used alone as acceptance.
- Conditions name their evidence, owner, deadline boundary and failure/return state.
- `ARTIFACT_QUALITY_CHECK: PASS`.

Next boundary: external review of this proposed G7 result. Stop after publishing its
review pack.
