# G7 Day 6 real-mode retry 2 result — 2026-10-01

## Authority and execution identity

- Decision: `AUTH-G7-DAY6-REAL-MODE-RETRY-20261001-002`
- Product build: `3e82626faebab8e9722939b92267deb51075d93b`
- LocalLLM baseline: `e33b0a410fb8647711f02ae4e6e0b66472e6eff0`
- Product run: `run-8b9fb7cac4c948098af3e9aa7dfeaf8d`
- Isolated engineering run/worktree: `a8dce10961cf44bfb38ef75e92d7ff2c`
- Go requests: exactly one
- Codex/model executions: exactly one
- Reviewer Bus: disabled
- Service: stopped after terminal readback

The service process verified before Go that configured and resolved
`CODEX_SQLITE_HOME` both equal the existing
`C:\AI-Control-Center\state\codex-sqlite` directory. Grant and prerequisite facts
matched the immutable RunIntent and admission was `ADMISSIBLE`.

## Observed execution result

The actual Codex execution completed once with exit code 0 and changed only the four
allowed files in the isolated LocalLLM engineering worktree:

- `schemas/temporal-state.json`
- `scripts/eval/temporal_state.py`
- `tests/test_temporal_state.py`
- `docs/architecture/temporal-state.md`

The postcheck ran `pytest -q tests/test_temporal_state.py` and recorded `6 passed`.
Day state then reported all four criteria satisfied and `COMPLETE / DAY_COMPLETE`.

Observed Codex usage was 528,695 gross input tokens, including 474,112 cached and
54,583 uncached input tokens, plus 8,131 output tokens. The task record retained
`TASK_BUDGET_EXCEEDED`; it did not retroactively invalidate the completed task.
The authority's 0 JPY condition was not exceeded, but the product RunRecord has no
run-bound cost telemetry, so cost remains unavailable as product telemetry rather
than inferred from the limit.

## Product-boundary discrepancies

1. The Day snapshot and UI report `COMPLETE`, 4/4 criteria and 100%, while the same
   product run's durable RunRecord and read-only dashboard projection remain
   `PREFLIGHT`, with runtime `UNKNOWN` and the pre-execution next action.
2. The five persisted Day Evidence Records used for completion have `run_id: null`
   and `criterion_id: null`. Their artifact hashes and validators are present, but
   they are not bound to the product run and criterion identity required by A02.
3. Actual token usage is retained in the task/Day state, including the budget
   warning, but the product run projection has `telemetry: null`; attempts, tokens
   and cost display as not recorded. A06 cannot reconcile them under the same run ID.

No retry, failure injection, repair, current Reviewer operation, Watcher action,
credential change, G8 action or product-acceptance claim was made.

## G7 A01–A06 classification

| Requirement | Product result |
|---|---|
| A01 selected-Day Go/admission | `PASS`: selection was side-effect free; one Go created one exactly admitted Day 6 run. |
| A02 plan, Evidence and judgment | `FAIL`: artifacts and validators passed, but the Evidence Records consumed for completion are not run/criterion-bound. |
| A03 repair and revalidation | `NOT_EVALUABLE`: the first permitted engineering execution and postcheck succeeded; no repair episode occurred. |
| A04 current review/stop/recovery | `NOT_EVALUABLE`: no review was required and Reviewer Bus remained disabled. |
| A05 actual-state dashboard | `FAIL`: Day `COMPLETE` and durable same-run `PREFLIGHT` disagree. |
| A06 outcome, attempts, tokens and cost | `FAIL`: task usage exists, but run telemetry is null and cannot be reconciled under the product run ID. |

## Proposed return

G7 should return to G6 only for the minimum product composition needed to:

1. bind accepted Day Evidence to the immutable product run and criterion IDs;
2. project terminal Day completion to that same durable RunRecord; and
3. persist/project actual attempt, token, budget-warning and cost-availability
   telemetry under the same run.

Reuse the existing artifacts and this one execution. Do not rerun Day 6 merely to
reproduce the discrepancies. Real repair/revalidation and current review operation
remain unevaluated unless a later authorized path naturally exercises them.

## Artifact quality

`ARTIFACT_QUALITY_CHECK: PASS` for this verification record and evidence package:
the fixed run identity, exact authority, startup binding, access log, Day state,
RunRecord, token observation and four output artifacts are retained with byte lengths
and SHA-256 values. This does not mean the product or G7 passed.
