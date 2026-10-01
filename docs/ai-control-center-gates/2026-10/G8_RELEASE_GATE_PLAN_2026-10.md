# G8 GA-03 — Local Release-Gate Plan

- **Plan ID:** `G8-GA03-RELEASE-GATE-PLAN-20261001-001`
- **Status:** `RELEASED_LOCAL_BOUNDED`
- **Authority:** `AUTH-G8-GA03-RELEASE-GATE-20261001-001`
- **Candidate product build:** `656711367ed837ddbb75e6df65234a955e44900d`
- **Operating owner:** 広瀬剛
- **Policy:** `docs/WORKING_RULES.md` at
  `60c0fe7dcf8935fad4c6d3818256a94e95965501`

## 1. Purpose and original planning boundary

When created, this plan defined the evidence and explicit future authority required
to decide whether the bounded Day 6 demonstration might become a local release
candidate. The planning authority itself did not release, distribute, deploy, start
a service or Watcher, execute a Day/Go, run a model, test a product path, alter
credentials or spend funds.

Before the later release decision, the accepted claim was
`ACCEPT_BOUNDED_DAY6_DEMONSTRATION`; that earlier acceptance was not all-Day
acceptance, continuous operation or a release decision. The current state after the
later human decision is stated immediately below.

## Applied local release decision

広瀬剛 selected option 1 with the direct instruction
`1。限定ローカルでリリースします`. Decision
`D8-LOCAL-BOUNDED-RELEASE-20261001-001` releases only the fixed
`AI-Control-Center-Day6-Bounded-RC1` identity for Day 6 demonstration use by
広瀬剛 on the named local Windows/loopback environment. It accepts the RG-06
limitations below and does not start a service, Watcher, Day/Go or model.

The former `NO_RELEASE` state is superseded only for that exact bounded local scope.
All-Day, multi-user, externally accessible, continuously unattended, real-mode and
externally distributed release states remain `NOT_RELEASED`.

## 2. Fixed inputs and retained limitations

| Fixed input | Gate use | Limitation retained |
|---|---|---|
| Candidate build `656711...` | Identifies the source build whose Day 6 evidence was accepted. | It is now the named bounded local release RC1; it is not an externally distributable or broader product release. |
| G8 bounded acceptance record | Establishes the accepted Day 6 scope. | Does not accept Days 1–14, distribution or continuous operation. |
| G7 Day 6 product evidence | Supports the Day 6 selection/Go, bound Evidence, terminal state and telemetry facts. | A03 actual repair and A04 current review are occurrence-level `NOT_EVALUABLE`. |
| Current Reviewer Bus state | Establishes the intended review mechanism. | One bounded current happy-path cycle is accepted; continuous Watcher liveness and all failure paths are not proven. |
| Cost record | Retains run token/attempt/budget facts. | Measured JPY cost remains `UNKNOWN`, not 0 JPY. |

## 3. Required release-gate conditions

All conditions must be shown by fixed, current evidence before any future release
authority may be requested. A plan is not evidence that a condition is met.

| Gate ID | Required condition | Evidence needed | Current status |
|---|---|---|---|
| RG-01 | Exact artifact and version are identified. | Immutable distributable artifact/version, source commit, content hash and provenance. | `RELEASED_LOCAL_BOUNDED` — `AI-Control-Center-Day6-Bounded-RC1`, source commit `656711...`, 288,116 bytes and SHA-256 `6453a213...`, accepted by `G8-RG01-ARTIFACT-COMPLETION-20261001-002`, is released only for the named bounded local scope. It has not been externally distributed or published as a broader release. |
| RG-02 | The accepted operating scope is explicit. | Named environment, bind address, data locations and permitted users. | `COMPLETE_POLICY_BOUNDARY` — accepted in `G8-OPERATING-ENVELOPE-COMPLETION-20261001-001`; no deployment claim. |
| RG-03 | Stop and rollback are usable. | Tested or otherwise approved stop/rollback procedure for the named artifact, with evidence preservation. | `COMPLETE_LIMITED` — revision 002 was accepted at reviewed commit `b1dc48e...`. One isolated mock start/stop returned the candidate to no process/listener/service/task with evidence retained. The accepted trace remains a post-execution transcription, not native OS audit evidence, and graceful shutdown is not claimed. |
| RG-04 | Review path is current and bounded. | Current Reviewer Bus/Watcher condition or an explicitly approved alternative, correlation and escalation path. | `COMPLETE_LIMITED` — `G8-RG04-REVIEW-PATH-COMPLETION-20261001-002` accepted one exactly correlated report/response, one Watcher application/stop and one `NO_REPORT` continuation with zero matching post-stop registrations. Continuous liveness and all failure paths are not claimed. |
| RG-05 | Cost and credential conditions are safe. | Explicit spend limit, credential owner/change rule and treatment of unavailable cost. | `COMPLETE_POLICY_BOUNDARY` — zero-spend, unknown-cost and credential rules accepted in the operating envelope. |
| RG-06 | Scope limitations are accepted. | Human decision whether A03/A04 and all-Day gaps are acceptable for the named release scope. | `COMPLETE_ACCEPTED_LIMITATIONS` — decision `D8-LOCAL-BOUNDED-RELEASE-20261001-001` accepts A03/A04 as occurrence-level `NOT_EVALUABLE` and excludes all other Days, continuous operation and broader release claims. |
| RG-07 | Ownership and recovery are assigned. | Operating owner, escalation contact, data/evidence retention and stop authority. | `COMPLETE_POLICY_BOUNDARY` — owner, stop authority, retention and escalation accepted in the operating envelope. |

## 4. Future authority boundary

Only after RG-01 through RG-07 are evidenced or explicitly dispositioned may a new
human authority propose an actual release. That authority must name:

1. the immutable artifact/version and intended local audience;
2. the operating environment and bind address;
3. the approved stop/rollback procedure and evidence-retention location;
4. the current reviewer-transport condition and fallback/escalation policy;
5. the cost, credential and time limits; and
6. exactly which G8 limitations remain accepted, deferred or rejected.

That authority now exists only as decision
`D8-LOCAL-BOUNDED-RELEASE-20261001-001` for the exact bounded local identity.
Every broader release remains prohibited.

## 5. Original GA-03 deliverables and stop condition

GA-03 was complete for its planning authority when this plan and its review pack
identified every future release input without pretending that an input was
satisfied. Its original stop required a separately authorized gate-input collection
or human release decision. Decision `D8-LOCAL-BOUNDED-RELEASE-20261001-001`
subsequently satisfied that boundary only for the exact bounded local identity.

At planning review, `ARTIFACT_QUALITY_CHECK: PASS` required the candidate identity,
local boundary, owner, reviewer/Watcher limitation, cost/credential limitation,
stop/rollback need and then-current `NO_RELEASE` condition to be traceable. The
current bounded release state is governed by the later applied decision section and
gate table above.
