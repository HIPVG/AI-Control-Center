# G7 product-path validation — 2026-09-30

## 1. Scope and authority

- Action class: `VALIDATION`
- Authority record: `docs/review-records/G7_EXECUTION_AUTHORITY_2026-09-30.md`
- Accepted G7 plan: `G7-VERIFICATION-PLAN-20260929-002`
- Accepted G6 runtime composition: `G6-RUNTIME-COMPOSITION-COMPLETION-20260930-002`
- G6 reviewed commit: `a71ab7a30edad05a1b6310fb87548764fe5e17c1`
- Executed product baseline: `8497bb239c35003f212996e9d4d7afde0a57ffab`; the G6 reviewed commit is its ancestor and no product code was changed for G7.
- Target: Day 6
- Limits: 30 minutes ACTIVE_WORK, at most two Go attempts, 0 JPY
- Reviewer Bus: explicitly disabled by `AI_CONTROL_CENTER_DISABLE_REVIEWER_BUS=1`; no Watcher restart, review delivery or Codex continuation occurred.

The purpose of this supplemental validation was to exercise the smallest real service/browser path needed to close the product-facing Must conditions left after the accepted fixture and historical-actor evidence. It did not authorize a G7 repair.

## 2. Execution and retained facts

### 2.1 Existing working tree — protected stop

The first local service used the existing working tree and the real Go API once. It created run `run-80a0f7b8f630483d9dddf9bdcb5e725f` and correctly failed closed with `DIRTY_GIT_BASELINE`. `execution_started` was false. Existing modified and untracked work was preserved. This attempt established that product admission did not bypass a dirty baseline, but it could not evaluate the downstream product path.

### 2.2 Clean managed worktree — actual browser path

A managed worktree was created from `origin/agent/g0-g5-baseline-publication` at `8497bb239c35003f212996e9d4d7afde0a57ffab`. Before Go:

- `git status --porcelain` was empty;
- the service reported `HEALTHY` on loopback port 8018;
- Reviewer Bus reported `running=false` and `last_error=DISABLED_BY_ENV`;
- `/api/local-llm/runs` reported `selected=false`, `current=null`, and no history;
- the actual Chrome dashboard displayed `IDLE` and `UNSELECTED`;
- selecting Day 6 displayed `Day 6 selected locally. No run or external action was created.` and did not create a RunRecord;
- the Go control was enabled.

The browser then invoked Go once. The access log contains one successful HTTP request to `POST /api/local-llm/day/go`. The dashboard readback showed:

- run ID `run-048d552b085a4c4e816ccf02ed1a0a1f`;
- selected Day 6;
- state `HUMAN_ACTION_REQUIRED`;
- admission `BLOCKED — DIRTY_GIT_BASELINE`;
- runtime observation `UNKNOWN`;
- next action `Preserve the dirty Git state and obtain a clean approved baseline.`

No Day executor, model, repair, reviewer transport or paid action began.

### 2.3 Admission-state inconsistency

Immediately before the browser Go, the managed worktree was clean. Immediately after the one Go request, `git status --short --untracked-files=all` listed exactly one path:

`state/runs/0a7a83c1c6fffbdac23bf5c67f2dc628b9f7bed6a9fb843de7a2782eaa8ba3ca.json`

That file is the newly persisted RunRecord for the blocked run and has SHA-256
`CC3C9686EFEB0C548A62B952997893EF528C50712D9D270D230B73964CA6692D`.

The product therefore reports a dirty baseline after a Go that began from a verified clean baseline, while the only retained Git change is its own generated RunRecord. The exact internal interleaving is not claimed from black-box evidence. The observable contract failure is sufficient: product-generated runtime persistence can make or leave the admission boundary indistinguishable from user source dirtiness, so a clean product Go cannot reach `PREFLIGHT`.

The two permitted Go attempts are exhausted. Repeating the same action would not add evidence and is prohibited by the accepted G7 limit.

## 3. Requirement result

| Requirement | Previously accepted boundary | Supplemental product result |
|---|---|---|
| A01 selected-Day Go and state | fixture `PASS` | `FAIL`: actual selection is side-effect free, but a clean-baseline Go stops at `DIRTY_GIT_BASELINE` instead of `PREFLIGHT`. |
| A02 plan, Evidence and judgment | fixture `PASS` | `NOT_EVALUABLE`: execution and Evidence collection did not begin because A01 admission failed. |
| A03 repair and revalidation | fixture `PASS` | `NOT_EVALUABLE`: no product failure episode could begin past admission. |
| A04 review, stop and recovery | fixture plus historical actor `PASS` | Current product-run path `NOT_EVALUABLE`; Reviewer Bus was intentionally disabled and no review was required before the admission failure. |
| A05 actual-state dashboard | fixture `PASS` | Partial product `PASS` for unselected, Day 6 selection, persisted blocked state and same run ID readback; product Go-to-`PREFLIGHT` remains `FAIL`. |
| A06 outcome, relay and cost | fixture `PASS` | `NOT_EVALUABLE`: no actual run telemetry was produced; token/cost values were not inferred. Actual cost incurred was 0 JPY. |

The prior fixture and historical-actor acceptances remain valid within their stated boundaries. They are not promoted to product E2E.

## 4. Disposition and return point

- G7 result: `RETURN`.
- Return target: G6 runtime admission/persistence integration.
- Minimum repair objective: preserve the clean-source decision across RunIntent creation and generated RunRecord persistence, or otherwise exclude approved generated runtime state from source-dirty admission, while continuing to reject actual modified or untracked user source.
- Required focused proof: a clean production-equivalent Go reaches `PREFLIGHT`; actual user source dirtiness still returns `DIRTY_GIT_BASELINE`; generated `state/runs` persistence does not create a false dirty result; selection remains side-effect free; exactly one RunRecord is retained for one Go.
- After reviewed G6 repair, rerun only this bounded product admission/browser slice before attempting downstream Evidence, repair/review, telemetry and completion checks.

This G7 result does not authorize the repair, another Go attempt, G8, product acceptance, Watcher operation, credential change or paid execution.

## 5. Quality and preservation

- Existing dirty work was not reset, cleaned, restored, staged or committed.
- The managed worktree and its blocked RunRecord remain available as evidence.
- The first-start harness logs were moved, not deleted, to `C:/Temp/ai-control-center-g7-evidence-worktree-first-start`.
- The live service log is retained at `C:/Temp/ai-control-center-g7-e2e-live`.
- G7 did not modify product code or acceptance expectations.
- `ARTIFACT_QUALITY_CHECK: PASS`.
