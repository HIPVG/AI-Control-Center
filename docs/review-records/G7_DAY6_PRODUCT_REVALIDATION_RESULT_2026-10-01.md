# G7 Day 6 product revalidation result — 2026-10-01

## Authority and execution identity

- Decision: `AUTH-G7-DAY6-PRODUCT-REVALIDATION-20261001-001`
- Product build: `656711367ed837ddbb75e6df65234a955e44900d`
- LocalLLM baseline: `e33b0a410fb8647711f02ae4e6e0b66472e6eff0`
- Product run: `run-494056aceb824430be81da7507d949c9`
- Isolated engineering run/worktree: `de2d40441ed74de9a22c331a15147ac0`
- Service starts: one
- Browser Go requests: one
- Codex/model executions: one
- Reviewer Bus/Watcher: disabled by environment
- Service: stopped after terminal API and UI readback

The service startup record verifies the exact fixed build and the existing managed
`CODEX_SQLITE_HOME=C:\AI-Control-Center\state\codex-sqlite`. The Grant and
prerequisite observation matched the immutable RunIntent, so admission was
`ADMISSIBLE`.

## Observed product result

One Codex turn completed with exit code 0 inside the isolated engineering worktree.
Only the four Day 6 paths changed. The deterministic postcheck recorded `4 passed`.
The Day snapshot and durable RunRecord both reached `COMPLETE`; the API and visible
dashboard read back the same product run ID.

The six Evidence Records referenced by the four satisfied criteria all have the
exact product `run_id` and their respective `criterion_id`. Five historical nullable
source records remain retained but are not the completion references. This is the
intended non-destructive reconciliation behavior.

Run telemetry schema v2 is present for the same run and records:

- actual attempt count `1` and immutable attempt limit `2`;
- gross input `273,793`, cached input `239,104`, uncached input `34,689`, and
  output `4,792` tokens;
- budget decision `TASK_BUDGET_EXCEEDED` with terminal-task provenance;
- cost value unavailable with the explicit reason that terminal task records did
  not expose measured JPY cost.

The cost limit is not substituted for a measurement. No paid service or cost-bearing
operation was initiated by this validation.

## G7 A01–A06 classification for this product run

| Requirement | Product result |
| --- | --- |
| A01 selected-Day Go/admission | `PASS`: side-effect-free selection, one Go, exact admission and one actual execution. |
| A02 plan, Evidence and judgment | `PASS`: every completion reference is validated and bound to the exact run and criterion. |
| A03 repair and revalidation | `NOT_EVALUABLE`: the first execution and postcheck succeeded; no repair episode occurred. |
| A04 current review/stop/recovery | `NOT_EVALUABLE`: no review was required and Watcher remained disabled. |
| A05 actual-state dashboard | `PASS`: Day snapshot, durable RunRecord, API and UI all read `COMPLETE` for the same run. |
| A06 outcome, attempts, tokens and cost availability | `PASS`: result and actual usage are same-run telemetry; cost is retained as provenance-bearing unknown rather than inferred. |

No same-class cross-component composition deficiency recurred, so the human stop
rule requiring a G4/G5 return was not triggered. This limited result alone does not
promote A03/A04-current to product-path PASS and does not establish full product
acceptance or authorize G8.

## Evidence

Raw evidence and artifacts are fixed under
`docs/review-evidence/G7-DAY6-PRODUCT-REVALIDATION-20261001-001/` with byte lengths
and SHA-256 values in `manifest.json`. The package includes startup, authority,
preflight, initial and terminal RunRecords, full Day state, run API and UI readback,
service/access logs, telemetry, Control Center state and the four generated artifacts.

The runtime-relative authority file whose bytes were hashed into the Grant is fixed
separately as `authority-record-runtime.md`; its SHA-256 is
`2598e32f33266f9805daed5ec5cd396090efe1a3ba905b8becb43949f4879eab`.
The longer repository authority record preserves the exact human instruction and is
not the byte source of the Grant field. `manifest.json` retains capture-time Windows
bytes. `transport-manifest.json` maps those bytes to the Git-published blob bytes and
identifies CRLF-to-LF normalization explicitly.

`ARTIFACT_QUALITY_CHECK: PASS` for this bounded validation record and evidence
package. This is not a G7 exit decision, G8 authorization, or product acceptance.
