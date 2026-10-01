# G8 — product acceptance and release-decision plan

- Plan ID: `G8-ACC-ACCEPTANCE-PLAN-20261001-001`
- Status: `PLAN_FOR_REVIEW`
- Human authority: `AUTH-G8-PLANNING-20261001-001`
- Decision owner: 広瀬剛
- Plan/implementation: Codex
- Review and verification: ChatGPT (the same ChatGPT role is not presented as two
  independent reviewers)
- Policy: `docs/WORKING_RULES.md` at
  `60c0fe7dcf8935fad4c6d3818256a94e95965501`

## 1. Purpose and boundary

G8 turns the fixed G0 purpose, G2 acceptance conditions and accepted G7 evidence
into one human product decision. Its output is an acceptance decision record, not an
automatic release. It distinguishes a bounded Day 6 product result from a claim that
all Day 1–14 contracts or every exceptional path are operationally accepted.

This plan creates no new product evidence. In particular, it does not manufacture an
A03 repair, a current A04 review round trip, a Watcher restart, a service run, a
browser action, another Go, a model call or a cost measurement.

## 2. Fixed input set

| Input | What it contributes | Limit retained |
|---|---|---|
| G0 purpose P01–P08 | Product value: one selected Day, evidence, bounded repair, review, dashboard and observable cost/attempts. | G0 is not implementation or acceptance evidence. |
| G2 A01–A06/NFR-02/NFR-03 | Acceptance expectations and responsibility boundaries. | A condition needs evidence at its named boundary. |
| G4/G5 control design and cards | Intended deterministic controls and non-overreach constraints. | Design/fixture evidence is not product acceptance by itself. |
| G7 stage result `PASS` | Accepted fixture, historical actor and bounded Day 6 product evidence. | A03 actual repair and A04 current review occurrence remain `NOT_EVALUABLE`. |
| Day 6 product evidence revision 009 | One Go, one model attempt, same-run `COMPLETE`, bound Evidence and telemetry, with reproducible public-byte provenance. | It is one authorized Day 6 run, not all Days or a release operation. |

## 3. G8 decision matrix

| ID | Decision question | Existing evidence | Required G8 treatment |
|---|---|---|---|
| D8-01 | Is the accepted product scope a bounded Day 6 demonstration or a releasable Day 1–14 product? | G7 proves one Day 6 product run; catalog/fixture coverage is broader but no all-Day product execution occurred. | The human must choose the claimed scope explicitly. Do not infer all-Day release. |
| D8-02 | Does A01/A02/A05/A06 support the chosen scope? | Accepted same-run Day 6 evidence covers selection/Go, typed completion Evidence, state/dashboard readback and telemetry. | Mark `SUPPORTED_FOR_DAY6` only. |
| D8-03 | Is A03 accepted for the chosen scope? | Guard and return behavior are fixture-verified; no actual repair was required. | Preserve `NOT_EVALUABLE` for actual repair. A claim requiring demonstrated repair success is not acceptable without a separately authorized case. |
| D8-04 | Is A04 accepted for the chosen scope? | Correlation controls and one historical actor path are accepted; the Day 6 run did not require review, and current Watcher operation is not claimed. | Preserve `NOT_EVALUABLE` for current review operation. A claim of live unattended review continuity is not acceptable without separately authorized current evidence. |
| D8-05 | Are safety, cost and operating limits acceptable? | The bounded run retained attempt/token/budget information and a reasoned unknown JPY cost; no paid cost was claimed. | Accept only the documented limits. Unknown cost remains unknown; it cannot be converted to 0 JPY. |
| D8-06 | Can distribution or continuous operation start? | No release artifact, operating owner handoff, current Watcher evidence or all-Day product acceptance has been established. | Default `NO_RELEASE` unless a later explicit decision supplies those inputs. |

## 4. Permitted human outcomes

| Outcome | Meaning | Consequence |
|---|---|---|
| `ACCEPT_BOUNDED_DAY6_DEMONSTRATION` | The human accepts the demonstrated Day 6 product boundary only. | Records value evidence; does not start distribution, continuous operation, other Days or a new Go. |
| `DEFER_PRODUCT_ACCEPTANCE` | The evidence is useful, but the intended acceptance claim requires A03 and/or current A04 evidence, all-Day coverage, release preparation or another stated condition. | Preserve evidence and create only the minimum next plan or authority needed for the named gap. |
| `REJECT_ACCEPTANCE_CLAIM` | The human does not accept the stated scope or value. | Record the reason and return to the earliest affected G4/G6/G7 boundary; no automatic repair. |

`ACCEPT_BOUNDED_DAY6_DEMONSTRATION` is deliberately not called product release or
all-Day acceptance. A separate, explicit authority is required for any service
operation, deployment, distribution, current Watcher operation or additional Day.

## 5. G8 execution cards (decision-only)

### GA-00 — evidence and scope ledger

Create an immutable ledger linking the G0/G2 requirements to the accepted G7
artifacts, their proof class, limitation and proposed decision scope. The ledger must
retain rejected revisions and cannot promote historical or fixture evidence to current
runtime evidence.

### GA-01 — acceptance recommendation

Codex prepares one concise recommendation using the decision matrix. ChatGPT reviews
whether claims exceed their proof boundary. The output must choose one of the three
human outcomes above or clearly state why a decision is not yet evaluable.

### GA-02 — human decision and record

広瀬剛 decides the explicitly named scope and outcome. The record preserves the exact
decision text, source class, scope, constraints and what it does not authorize.
No bare “approved” is inferred to mean release, additional execution or new scope.

### GA-03 — release gate (only if separately authorized)

This card is not authorized by this plan. Before release/distribution or continuous
operation, establish a new authority that names the target artifact/version, owner,
rollback/stop method, operating environment, current review transport condition and
cost/credential policy. If any is missing, retain `NO_RELEASE`.

## 6. Acceptance-quality and stop rules

- Every conclusion must cite a fixed artifact, run identity or direct human decision.
- G7 `PASS` must not be restated as all-Day product acceptance.
- Current Watcher liveness, real disconnect recovery and actual repair success remain
  evidence limitations, not failures hidden by a pass.
- `ARTIFACT_QUALITY_CHECK: PASS` for G8 planning means the matrix is traceable and
  does not overclaim. It is not product acceptance.
- After GA-01 review, stop for GA-02 human decision. Do not start GA-03 without new
  explicit authority.

## 7. Plan review request

Review whether this plan preserves the G0 product purpose and G2 A01–A06 while
preventing the G7 Day 6 evidence from being overextended to all-Day or release claims.
The plan is complete when its scope, outcomes, evidence limits, human decision and
release gate are clear; no product operation is needed to review it.
