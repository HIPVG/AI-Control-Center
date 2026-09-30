# G6 authority-fact composition stage completion evidence

## Fixed inputs and accepted cards

- Accepted repair plan:
  `G6-RUNTIME-AUTHORITY-FACT-PLAN-20260930-001`
- Plan commit: `3f7352eece4b6fd986b169d94de678fa7a57080d`
- Human implementation authority:
  `AUTH-G6-AUTHORITY-FACT-IMPLEMENTATION-20260930-001`
- AF-00 accepted pack: `G6-AF00-COMPLETION-20260930-002`
- AF-00 accepted commit: `bb111de0b7ef3425f99efa9b887378f96e3632d0`
- AF-01 accepted pack: `G6-AF01-COMPLETION-20260930-001`
- AF-01 accepted commit: `0d94d74a218ed0a1d1e4155801e0095f03b3c761`

Revision 001 of AF-00 remains preserved as rejected history. Revision 002 is the
accepted boundary; no rejected artifact is treated as acceptance evidence.

## Repair-plan DoD reconciliation

| DoD obligation | Fixed evidence | Result |
|---|---|---|
| Resolve exact, traceable permission and prerequisite facts | AF-00 Grant, Observation and Fact contracts/stores; exact binding and provenance assertions | PASS |
| Use the same immutable intent | AF-01 `prepare_intent` and coordinator fixture bind resolver, admission, RunRecord, effect and readback to one run ID | PASS |
| Fail closed for mismatch, missing, duplicate, stale, revoked, expired or corrupt inputs | AF-00 unit fixtures, exact-expiry repair, and AF-01 missing/stale authority and missing-prerequisite API fixtures | PASS |
| Keep permission and external prerequisites independent | AF-00 and AF-01 assertions retain one valid fact while the other remains unknown | PASS |
| Persist create-only auditable provenance | Fact records retain run/fingerprint identity, decision/grant ID, source hashes, observation IDs/hashes, timestamps and reasons | PASS |
| Compose production Engine, coordinator, read model and legacy guard | AF-01 fixed implementation and FastAPI fixture | PASS |
| Prove one same-run effect at product boundary | Actual Go endpoint reaches one deterministic injected executor; restart, duplicate Go and legacy start produce no second effect | PASS |
| Prevent fact evidence from completing work | AF-01 remains `PREFLIGHT` with unmet criteria; Fact projection is read-only | PASS |
| Preserve compatibility and user state | Existing RunRecord format remains readable; disposable stores were used; no persisted user/reviewer state was migrated | PASS |
| Artifact quality | AF-00 accepted after its bounded correction; AF-01 focused suite passed 20 tests and scoped static checks | PASS |

## Evidence limits

- AF-00 proves deterministic contract/store/resolver behavior.
- AF-01 proves in-process production composition through actual FastAPI handlers with
  an injected executor.
- Neither proves live service/browser behavior, a real Day, current external
  prerequisites, actual model execution or G7 product E2E.
- The historical Day 6 Grant is deliberately stale for the current product build;
  G6 does not create a new product-execution grant.

## Completion proposal and stop

Within the repair-plan scope, all DoD obligations above are satisfied and both cards
have matching acceptance. Proposed G6 result: `PASS` for implementation and
deterministic fixture composition only.

No return to G7, service/browser, real Go/Day, model, Watcher, credentials, spending,
G8 or product acceptance is authorized by this record. A matching G6 completion
review must accept this boundary before any later authority decision.

`ARTIFACT_QUALITY_CHECK: PASS`
