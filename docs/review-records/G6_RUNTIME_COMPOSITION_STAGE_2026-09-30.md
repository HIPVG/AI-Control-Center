# G6 runtime-composition return stage evidence

## Decision scope

This record evaluates only the accepted G6 return plan
`G6_RUNTIME_COMPOSITION_REPAIR_PLAN_2026-09.md`. It does not evaluate a running
service, browser interaction, actual Day 6, external model, current Watcher, or
product E2E.

## Accepted dependency chain

| Card | Accepted pack | Reviewed implementation commit | Result |
|---|---|---|---|
| RI-00 | `G6-RI00-COMPLETION-20260929-001` | `dcbc29870f5725ccc62f3f7e74293cac1b2bdac0` | `ACCEPT` |
| RI-01 | `G6-RI01-COMPLETION-20260929-002` | `964438152118d6877b95826ff6359f8131c51d00` | `ACCEPT` |
| RI-02 | `G6-RI02-COMPLETION-20260929-002` | `81715589915d3739327847bb7f1895ad4abdd1d4` | `ACCEPT` |
| RI-03 | `G6-RI03-COMPLETION-20260930-001` | `cc7976ddeded8e171d4ce9a668895b582bdb5987` | `ACCEPT` |

Rejected predecessor packs remain preserved and are not listed as accepted results.

## Required-invariant mapping

| # | Required invariant | Fixed evidence |
|---|---|---|
| 1 | One Go creates one immutable server-owned RunIntent | RI-00 coordinator fixture and RI-03 actual FastAPI Go fixture |
| 2 | Persist before effect; blocked admission has no Day effect | RI-00 store/coordinator assertions and RI-03 blocked-admission assertion |
| 3 | Trusted facts are server-resolved | RI-00 `RunPreflightFacts`; API request accepts only `selected_day` |
| 4 | One admitted identity reaches executor; legacy start cannot bypass | RI-00 accepted guarded alias and RI-03 one-call assertion |
| 5 | Evidence, repair/review, telemetry and reads use the same run ID | RI-01 adapters, RI-02 projection, RI-03 integrated same-run assertions |
| 6 | State evolution is durable and current/history stay distinct | RI-00 versioned store and RI-02 exact version-history validation |
| 7 | `/api/local-llm/runs` rebuilds from persisted sources | RI-02 read-time composition and RI-03 actual GET/restart readback |
| 8 | `COMPLETE` requires validator-owned Evidence | RI-01 completion guard and RI-03 all-declared-Evidence terminal assertion |
| 9 | Restart, duplicates and repeated data cannot create a second effect | RI-00 duplicate Go, RI-01 duplicate/stale response, RI-02 create-only telemetry/history, RI-03 restart readback |
| 10 | Existing dirty work is preserved | Every fixed commit used explicit path staging; unrelated dirty/untracked paths remain present and unadopted |

## Plan DoD evaluation

- Production composition root enforces the accepted components: `PASS` within the
  deterministic source/fixture boundary.
- RI-00 through RI-03 each have an exact accepted fixed commit: `PASS`.
- Integrated same-run API/admission/execution/Evidence/recovery-review/telemetry/read
  fixture: `PASS` at RI-03's in-process boundary.
- Direct-start and cross-run bypasses fail closed: `PASS`.
- Restart/current/history behavior is deterministic: `PASS`.
- `ARTIFACT_QUALITY_CHECK`: `PASS`.

The proposed G6 result is therefore `COMPLETE` only for the runtime-composition
implementation and deterministic fixture stage. Per the accepted plan, return to G7
would authorize validation planning only. It would not itself authorize the bounded
real service/browser/Day 6 E2E described as a later G7 boundary.

## No new execution evidence

This record is a fixed evidence reconciliation. No test was rerun, no service or
browser was started, no Day/Go/model/Watcher/credential operation occurred, and no
cost was incurred.

`ARTIFACT_QUALITY_CHECK: PASS`
