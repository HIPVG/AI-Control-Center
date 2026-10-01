# G8 RG-02/RG-05/RG-07 — Local Operating Envelope

- **Envelope ID:** `G8-LOCAL-OPERATING-ENVELOPE-20261001-001`
- **Status:** `FIXED_FOR_REVIEW`
- **Authority:** `AUTH-G8-OPERATING-ENVELOPE-20261001-001`
- **Candidate:** `AI-Control-Center-Day6-Bounded-RC1`
- **Source commit:** `656711367ed837ddbb75e6df65234a955e44900d`
- **Archive SHA-256:**
  `6453a213b0a48b827bbbc83ec2bdf1036515e6d857451473402cae3fb79f6714`
- **Operating owner:** 広瀬剛
- **Policy commit:** `60c0fe7dcf8935fad4c6d3818256a94e95965501`

## 1. Purpose and proof boundary

This envelope fixes the intended local operating scope, cost/credential rules and
responsibility/retention rules for the RG-01 candidate. It is documentary release-gate
input. It does not prove deployment, runtime health, stop/rollback, current Reviewer
transport or release readiness.

## 2. RG-02 — accepted operating scope

| Item | Fixed condition |
|---|---|
| Host | One local Windows host managed by 広瀬剛. |
| Permitted user | 広瀬剛 only. No multi-user or remote audience. |
| Network | Loopback only: `127.0.0.1`. External exposure is prohibited. |
| Default port | `8000`. A different port requires a separately recorded decision. |
| Candidate archive | `C:\AI-Control-Center\state\release-artifacts\AI-Control-Center-Day6-Bounded-RC1\AI-Control-Center-Day6-Bounded-RC1.zip` |
| Prospective extraction root | `C:\AI-Control-Center\state\release-candidates\AI-Control-Center-Day6-Bounded-RC1` — named only; not created by this work. |
| Candidate runtime state | `<extraction-root>\state`; it must not silently reuse unrelated current-project state. |
| Candidate runtime logs | `<extraction-root>\logs`; startup and runtime logs remain local. |
| Manifest and decision records | Versioned repository documents under `docs/release-manifests/`, `docs/review-records/` and `docs/ai-control-center-gates/`. |
| Default mode | `mock`. `real` mode requires separate explicit authority. |

The fixed source supports this proposed boundary: both launch scripts bind Uvicorn to
`127.0.0.1`; the normal launcher defaults to port `8000`; state and startup-log paths
are relative to the repository/extraction root; and fixed `config/runtime.yaml` uses
`codex.mode: mock`. These are static source facts, not deployment evidence.

## 3. RG-05 — cost and credential conditions

- The spend ceiling is **0 JPY**.
- Unknown or unavailable cost remains `UNKNOWN`; it is never reported as zero.
- Paid APIs, paid models and paid external services are prohibited.
- Credentials are not copied into the archive or candidate root.
- Existing credentials must not be changed, reconfigured or newly authorized under
  this envelope.
- Any operation requiring authentication or a credential change stops before that
  action and requires a separate human decision.
- The candidate remains in `mock` mode. Real-mode or model execution is outside this
  envelope even if credentials already exist.

These conditions are fail-closed operating rules. They do not claim a measured JPY
cost or a live credential-path verification.

## 4. RG-07 — ownership, retention and escalation

| Responsibility | Assigned owner / rule |
|---|---|
| User, operating owner and stop authority | 広瀬剛 |
| Planning and documentation | Codex |
| Review and verification | ChatGPT; its combined role is not represented as two independent reviewers. |
| Decision after unresolved thresholds or authority boundary | 広瀬剛 |
| Evidence and state retention | Preserve archive, manifest, records, candidate state and logs until the candidate is explicitly retired or superseded. No automatic deletion. |
| Failure handling | Preserve state/evidence, stop the bounded action and escalate only the concrete unresolved decision or authority need. |
| Destructive recovery | Not authorized. Deletion, reset, credential change or replacement requires a separate explicit decision. |

## 5. Gate mapping and remaining work

| Gate | Evidence fixed here | Proposed status after review |
|---|---|---|
| RG-02 | Host, user, loopback/port, candidate/data/log paths and mock-mode boundary. | `COMPLETE_POLICY_BOUNDARY` |
| RG-05 | Zero-spend, unknown-cost, paid-service and credential-change rules. | `COMPLETE_POLICY_BOUNDARY` |
| RG-07 | Named owner, role allocation, stop authority, retention and escalation rules. | `COMPLETE_POLICY_BOUNDARY` |

RG-03 stop/rollback operation, RG-04 current review transport and RG-06 human scope
disposition remain unfulfilled. The prospective extraction root does not exist as a
result of this work. `NO_RELEASE` remains in force.

## 6. Artifact-quality result

`ARTIFACT_QUALITY_CHECK: PASS` for the documentary operating-envelope boundary:

- artifact identity matches accepted RG-01;
- every human-specified condition is represented;
- fixed-source compatibility is distinguished from runtime proof;
- no unknown cost is converted to zero;
- owners, data locations, exclusions and stop conditions are explicit; and
- downstream RG-03/RG-04/RG-06 work cannot interpret this as execution authority.
