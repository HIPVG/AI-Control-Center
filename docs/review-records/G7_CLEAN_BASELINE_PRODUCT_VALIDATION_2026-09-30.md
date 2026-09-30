# G7 clean-baseline product validation — 2026-09-30

## 1. Scope and authority

- Action class: `VALIDATION`
- Decision: `AUTH-G7-CLEAN-BASELINE-VALIDATION-20260930-001`
- Authority record:
  `docs/review-records/G7_CLEAN_BASELINE_VALIDATION_AUTHORITY_2026-09-30.md`
- Target: Day 6 product path
- Product baseline: `c2b06c5c6fdbe7f84a42b1d72fa203934cb2517a`
- Approved LocalLLM-Lab baseline:
  `e33b0a410fb8647711f02ae4e6e0b66472e6eff0`
- Window: 30 minutes ACTIVE_WORK, at most two Go attempts, 0 JPY
- Actual use: one Go attempt, 0 JPY; no model invocation
- Reviewer Bus: disabled by `AI_CONTROL_CENTER_DISABLE_REVIEWER_BUS=1`

The existing `C:/LocalLLM-Lab` working tree and its eight pre-existing dirty paths
were not changed. Validation used a new detached worktree at
`C:/AI-Control-Center/state/g7-local-llm-clean-20260930`.

## 2. Fixed preconditions

The LocalLLM-Lab validation worktree had the approved HEAD and empty
`git status --porcelain=v1 -z -uall` before Go. A separate AI-Control-Center
worktree at the fixed product baseline was used. Its only pre-Go tracked difference
was `config/projects.yaml`, changed locally to point `local_llm_lab.path` to the
approved clean worktree. This is a validation input, not a product-code repair.

The loopback service started on `127.0.0.1:8019`. Health readback showed
`HEALTHY`; Reviewer Bus readback showed `running=false`, `available=false` and
`last_error=DISABLED_BY_ENV`. Before Go, `/api/local-llm/runs` showed no selected
run or history. The catalog classified Day 6 as `ADMISSIBLE` to deterministic
preflight.

In the real Chrome dashboard, selecting Day 6 displayed:
`Day 6 selected locally. No run or external action was created.` The read-only run
panel remained `UNSELECTED` with no run ID. The Go control was enabled.

## 3. One product Go and observed result

The browser invoked Go once. The access log contains exactly one
`POST /api/local-llm/day/go` with HTTP 200. The dashboard and API then agreed on:

- run ID: `run-a29217eb049447b68b83ce53a1df1054`
- selected Day: 6
- state: `HUMAN_ACTION_REQUIRED`
- admission: `BLOCKED`
- reason: `EFFECTIVE_PERMISSION_UNKNOWN`
- next action: `Confirm the execution actor's effective permission without changing credentials.`
- runtime observation: `UNKNOWN`
- execution/model/telemetry: not started or produced

The generated RunRecord preserves the approved limits and the clean-source Git
fingerprint. Its SHA-256 is
`6853444DCAED406FE406300F94CEAEEA67C0E84014F49CB5258633BAEFAF41E5`.
The LocalLLM-Lab validation worktree remained clean after Go. No second Go was
performed because no trusted input changed; repeating the same request would be a
blind retry.

## 4. Cause and boundary classification

This is not a missing human decision: the exact Day 6 authority and limits were
recorded before execution. It is a production composition gap between that trusted
authority and the server-owned admission facts.

At the fixed product baseline, `ControlCenterEngine` constructs `RunCoordinator`
with the default resolver `lambda _day: RunPreflightFacts()`. Both
`effective_permission` and `external_prerequisite` therefore remain `None` in the
real composition. The public API correctly refuses browser-supplied permission, and
there is no existing production input path that turns the recorded authority into
the trusted facts required for `PREFLIGHT`.

The fail-closed result is correct for unknown facts; the product path is incomplete.
No G7 code repair is authorized. The return point is G6 runtime composition: add the
minimum deterministic, auditable server-owned authority/prerequisite resolution and
prove that the recorded decision is scoped to the matching Day, baseline and limits;
unknown, stale or mismatched authority must remain blocked.

## 5. Requirement result and disposition

| Requirement | Result |
|---|---|
| A01 selected-Day Go and state | `FAIL`: clean Git admission passed, but the real Go cannot reach `PREFLIGHT` because trusted permission is never resolved in production composition. |
| A02 plan, Evidence and judgment | `NOT_EVALUABLE`: execution did not start. |
| A03 repair and revalidation | `NOT_EVALUABLE`: no admitted run began. |
| A04 review, stop and recovery | `NOT_EVALUABLE` for this run; Reviewer Bus was intentionally disabled and the stop occurred before review. |
| A05 actual-state dashboard | Partial product `PASS`: selection, same-run blocker and exact next action were displayed and matched the API. |
| A06 outcome, relay and cost | `NOT_EVALUABLE`; no telemetry or model output exists, actual spend was 0 JPY. |

- G7 product result: `RETURN` to a bounded G6 authority-fact composition repair.
- The previously accepted fixture and historical-actor evidence retain their limited
  scopes; they are not promoted to product E2E.
- The second authorized Go attempt remains unused and is not carried across this
  blocking return without a later explicit validation decision.
- G8 and product acceptance remain prohibited.

## 6. Evidence preservation and shutdown

- RunRecord path:
  `state/g7-acc-clean-20260930/state/runs/8b01dddf080c2fb5eb1f514961f4bf0eee8081d333dd902b2f61df784309c282.json`
- Service stdout SHA-256:
  `A5B2F82FC8383D4580FE44E252FA359922FAB3BD276B6419F5B40261FB760B0B`
- Service stderr SHA-256:
  `3F50BC31C7B70AEBF008FB266F907CA0E5BE04E9FE18C66E8DEA6AF5FA54C2FB`
- Service was stopped after readback; port 8019 no longer answered.
- Both validation worktrees and the blocked RunRecord were preserved.
- Existing user work was not reset, cleaned, restored, staged or committed.
- `ARTIFACT_QUALITY_CHECK: PASS`.
