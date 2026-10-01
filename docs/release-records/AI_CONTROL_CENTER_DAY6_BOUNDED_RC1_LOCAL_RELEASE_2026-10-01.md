# AI Control Center Day 6 Bounded Local Release

## Decision identity

- **Release ID:** `AI-Control-Center-Day6-Bounded-RC1`
- **Decision ID:** `D8-LOCAL-BOUNDED-RELEASE-20261001-001`
- **Decision owner / sole intended user:** 広瀬剛
- **Decision text:** `1。限定ローカルでリリースします`
- **Decision source:** `RECORDED_DIRECT_CONVERSATION`
- **Message ID / receipt time:** `UNKNOWN`
- **Release state:** `RELEASED_LOCAL_BOUNDED`
- **Decision date:** `2026-10-01`
- **Decision-review closure:** `ACCEPT`, pack
  `G8-LOCAL-BOUNDED-RELEASE-DECISION-20261001-002`, reviewed commit
  `12dc4c322c410bfc06dda10711ac8c19a97e4f29`, applied `2026-10-02`

The decision selects option 1 from the immediately preceding RG-06 explanation:
release the fixed candidate only as a Day 6 demonstration for local use by 広瀬剛,
with every listed limitation retained. It does not authorize external distribution,
continuous unattended operation or broader product acceptance.

## Released identity

- **Artifact:** `AI-Control-Center-Day6-Bounded-RC1`
- **Source commit:** `656711367ed837ddbb75e6df65234a955e44900d`
- **Source tree:** `fb22e40933c49b336b70599bd7e559d2caa7a841`
- **Archive bytes:** `288116`
- **Archive SHA-256:**
  `6453a213b0a48b827bbbc83ec2bdf1036515e6d857451473402cae3fb79f6714`
- **Local archive:**
  `C:\AI-Control-Center\state\release-artifacts\AI-Control-Center-Day6-Bounded-RC1\AI-Control-Center-Day6-Bounded-RC1.zip`
- **Local candidate root:**
  `C:\AI-Control-Center\state\release-candidates\AI-Control-Center-Day6-Bounded-RC1`
- **Default mode:** `mock`
- **Bind boundary:** `127.0.0.1:8000`

The archive was read back immediately before recording this decision. Its size and
SHA-256 matched the accepted RG-01 identity, the existing local candidate root was
present, and its runtime configuration retained `mode: mock`. No archive generation,
extraction or service start was required or performed for this decision.

## Accepted operating scope

- local Windows operation on the host managed by 広瀬剛;
- sole intended operator/user and stop authority: 広瀬剛;
- Day 6 bounded demonstration only;
- loopback access only; no external network exposure;
- state and logs remain under the fixed local candidate/control-center paths;
- zero-JPY spend ceiling; unavailable measured cost remains `UNKNOWN`;
- no paid API, paid model or paid external service;
- existing credentials are not changed, copied or embedded;
- evidence, state, logs, manifest and acceptance records are retained until the
  candidate is explicitly replaced or retired; and
- stop/rollback uses the accepted RG-03 exact-process boundary and preserves
  evidence.

## Retained limitations and fail-closed treatment

1. Day 1–5 and Day 7–14 are outside this release scope; their product E2E behavior
   is not accepted.
2. A03 actual automatic repair remains occurrence-level `NOT_EVALUABLE`. If a real
   repair case occurs, do not infer success from fixture evidence; retain state and
   stop at the applicable review/human boundary.
3. A04 product-run review intervention remains occurrence-level `NOT_EVALUABLE`.
   RG-04 proves one bounded no-effect reviewer round trip, not continuous review
   availability or a product repair/review cycle.
4. Continuous Watcher operation and all reviewer failure paths are not claimed.
5. Measured JPY cost is `UNKNOWN`, not zero; the zero-JPY value is an operating
   ceiling.
6. RG-03 proves bounded exact-process stop/rollback but does not claim graceful
   shutdown or native OS-audit provenance.
7. The released default is `mock`. Real mode, another Day/Go, another model run,
   credential change, external exposure or additional user requires a separate
   explicit authority.
8. The archive is a local source ZIP. No GitHub Release, installer, remote copy,
   external publication or update channel is created by this decision.

## Effect

This decision completes RG-06 as `COMPLETE_ACCEPTED_LIMITATIONS` and replaces
`NO_RELEASE` only for the exact bounded local identity and scope above. Every broader
release state remains `NOT_RELEASED`.

The candidate is not started by this record. Starting or resuming the local service,
Watcher, Day/Go or a model remains an operational action governed by the retained
limits and any applicable separate execution authority.
