# G8 GA-03 — Local Release-Gate Plan

- **Plan ID:** `G8-GA03-RELEASE-GATE-PLAN-20261001-001`
- **Status:** `PLAN_FOR_REVIEW`
- **Authority:** `AUTH-G8-GA03-RELEASE-GATE-20261001-001`
- **Candidate product build:** `656711367ed837ddbb75e6df65234a955e44900d`
- **Operating owner:** 広瀬剛
- **Policy:** `docs/WORKING_RULES.md` at
  `60c0fe7dcf8935fad4c6d3818256a94e95965501`

## 1. Purpose and boundary

This plan defines the evidence and explicit future authority required to decide
whether the bounded Day 6 demonstration may become a local release candidate. It
does not release, distribute, deploy, start a service or Watcher, execute a Day/Go,
run a model, test a product path, alter credentials or spend funds.

The current accepted claim remains
`ACCEPT_BOUNDED_DAY6_DEMONSTRATION`. It is not all-Day acceptance, continuous
operation or a release decision.

## 2. Fixed inputs and retained limitations

| Fixed input | Gate use | Limitation retained |
|---|---|---|
| Candidate build `656711...` | Identifies the source build whose Day 6 evidence was accepted. | It is not yet a named distributable artifact or release version. |
| G8 bounded acceptance record | Establishes the accepted Day 6 scope. | Does not accept Days 1–14, distribution or continuous operation. |
| G7 Day 6 product evidence | Supports the Day 6 selection/Go, bound Evidence, terminal state and telemetry facts. | A03 actual repair and A04 current review are occurrence-level `NOT_EVALUABLE`. |
| Current Reviewer Bus state | Establishes the intended review mechanism. | Current Watcher liveness is not proven and `running: false` is not release-ready evidence. |
| Cost record | Retains run token/attempt/budget facts. | Measured JPY cost remains `UNKNOWN`, not 0 JPY. |

## 3. Required release-gate conditions

All conditions must be shown by fixed, current evidence before any future release
authority may be requested. A plan is not evidence that a condition is met.

| Gate ID | Required condition | Evidence needed | Current status |
|---|---|---|---|
| RG-01 | Exact artifact and version are identified. | Immutable distributable artifact/version, source commit, content hash and provenance. | `INPUT_REQUIRED` — current candidate is source-only. |
| RG-02 | The accepted operating scope is explicit. | Named environment, bind address, data locations and permitted users. | `PLANNED` — local Windows, `127.0.0.1` only. |
| RG-03 | Stop and rollback are usable. | Tested or otherwise approved stop/rollback procedure for the named artifact, with evidence preservation. | `INPUT_REQUIRED` — planning model exists; no operation was run. |
| RG-04 | Review path is current and bounded. | Current Reviewer Bus/Watcher condition or an explicitly approved alternative, correlation and escalation path. | `NOT_EVALUABLE` — current Watcher liveness is not claimed. |
| RG-05 | Cost and credential conditions are safe. | Explicit spend limit, credential owner/change rule and treatment of unavailable cost. | `PLANNED` — no spend, existing credentials unchanged, cost `UNKNOWN`. |
| RG-06 | Scope limitations are accepted. | Human decision whether A03/A04 and all-Day gaps are acceptable for the named release scope. | `INPUT_REQUIRED` — bounded Day 6 acceptance does not decide release scope. |
| RG-07 | Ownership and recovery are assigned. | Operating owner, escalation contact, data/evidence retention and stop authority. | `PLANNED` — owner is 広瀬剛; concrete operating record is still required. |

## 4. Future authority boundary

Only after RG-01 through RG-07 are evidenced or explicitly dispositioned may a new
human authority propose an actual release. That authority must name:

1. the immutable artifact/version and intended local audience;
2. the operating environment and bind address;
3. the approved stop/rollback procedure and evidence-retention location;
4. the current reviewer-transport condition and fallback/escalation policy;
5. the cost, credential and time limits; and
6. exactly which G8 limitations remain accepted, deferred or rejected.

Without that authority, `NO_RELEASE` remains in force.

## 5. GA-03 deliverables and stop condition

GA-03 is complete for this planning authority when this plan and its review pack
identify every future release input without pretending that an input is satisfied.
After review, stop. The next action may only be a separately authorized collection
of a named gate input or a separate human release decision; it is never automatic
from this plan.

`ARTIFACT_QUALITY_CHECK: PASS` requires the candidate identity, local boundary,
owner, reviewer/Watcher limitation, cost/credential limitation, stop/rollback need
and `NO_RELEASE` condition to be traceable in the plan.
