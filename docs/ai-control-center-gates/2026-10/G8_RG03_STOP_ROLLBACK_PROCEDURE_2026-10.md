# G8 RG-03 — Stop and Rollback Procedure and Validation

- **Procedure ID:** `G8-RG03-STOP-ROLLBACK-20261001-001`
- **Status:** `EVIDENCE_REPAIR_FIXED_FOR_REVIEW`
- **Authority:** `AUTH-G8-RG03-STOP-ROLLBACK-20261001-001`
- **Candidate:** `AI-Control-Center-Day6-Bounded-RC1`
- **Source commit:** `656711367ed837ddbb75e6df65234a955e44900d`
- **Archive SHA-256:**
  `6453a213b0a48b827bbbc83ec2bdf1036515e6d857451473402cae3fb79f6714`
- **Runtime root:**
  `C:\AI-Control-Center\state\release-candidates\AI-Control-Center-Day6-Bounded-RC1`
- **Mode / endpoint:** `mock`, `127.0.0.1:8000`

## 1. Validated procedure

1. Confirm the original ZIP exists and its full SHA-256 matches the accepted RG-01
   identity.
2. Confirm the exact runtime root is absent and port 8000 has no listener. If either
   is occupied, stop as `INPUT_BLOCKED`; do not overwrite, delete or stop it.
3. Extract the ZIP once into the fixed parent so the archive prefix creates the exact
   runtime root.
4. Confirm 124 fixed files, `codex.mode: mock`, loopback binding and default port
   8000 before starting.
5. Set `AI_CONTROL_CENTER_DISABLE_REVIEWER_BUS=1` for the candidate process and start
   packaged `scripts/start.ps1 -Port 8000` once in a hidden local PowerShell host.
6. Record launcher/server process identities and verify the only listener is
   `127.0.0.1:8000`.
7. Perform the bounded read-only HTTP checks and retain their response bytes.
8. Stop only the captured candidate descendants followed by the launcher if still
   present. Do not operate an unrelated process.
9. Confirm captured PIDs, candidate-path processes and port 8000 listeners are absent.
10. Confirm no Windows service or scheduled task references the candidate root.
11. Preserve the inactive runtime root, state, logs and response evidence. Do not
    delete or auto-start it.

The rollback baseline is: original archive and repository unchanged; candidate
process/listener absent; no service/task registration; candidate root retained but
inactive; state/log evidence preserved.

## 2. Execution record

| Event | Observed fact |
|---|---|
| Preflight archive | 288,116 bytes; accepted SHA-256 matched. |
| Preflight target | Absent. |
| Preflight port 8000 | No listener. |
| Extraction | One execution, `2026-10-01T08:17:34.4074685Z` to `2026-10-01T08:17:35.5694863Z`. |
| Extracted inventory | 124 files before runtime. |
| Static boundary | `mode: mock`; loopback and default-port checks true. |
| Service start | One execution at `2026-10-01T08:18:06.5169793Z`. |
| Process identity | launcher PID 16088; server PID 1448; console child PID 21468. |
| Listener | Exactly `127.0.0.1:8000`, owned by server PID 1448. |
| HTTP check 1 | `GET /` returned 200; 6,654 bytes. |
| HTTP check 2 | `GET /api/local-llm/runs` returned 200; 300 bytes; no selected/current run. |
| Stop request | One execution at `2026-10-01T08:19:02.3083990Z`. |
| Final processes | Captured PIDs absent; candidate-path process count 0. |
| Final listener | Port 8000 listener count 0. |
| Autostart integration | Candidate Windows service count 0; scheduled-task count 0. |
| Watcher | Persisted candidate state says `running: false`, `available: false`, `last_error: DISABLED_BY_ENV`. |
| Retained runtime files | 210 files total after runtime; 2 state files and 6 log files retained. |

## 3. Retained evidence hashes

| Candidate-relative evidence | Bytes | SHA-256 |
|---|---:|---|
| `config/runtime.yaml` | 138 | `23e7fd06fb56aee08d8ddff71c932cc1deb060c2ad154f189f229baef400a5f6` |
| `scripts/start.ps1` | 3,387 | `40ab111f0d9554fdb5996b039ba60a6129d7dd88ecbe4ff87d91c428b2b852f8` |
| `state/reviewer-bus-watcher.json` | 185 | `b26b78023178d124fd3986dff0f83f3531e0c25678a01c8bea69d8aec9fc129f` |
| `logs/startup.log` | 283 | `0a1cdd361be5168c3a1d5157916cee2b16308aa22d78ebf0f4f64663307efdd8` |
| `logs/rg03-service.stdout.log` | 124 | `e2077d8cb582bd8a2fc6d50d15a932b2ce6e7f7de48698890aecedca2397270d` |
| `logs/rg03-service.stderr.log` | 201 | `5ee4d9069714b5957becabdd5e79204e05089f3d5b0054dcefeacd10bbbe93ef` |
| `logs/rg03-http-root.response` | 6,654 | `baa9dcb998a4277a3002b8157d622a3d02f857f9074c05b30c33da4a4cbd43ad` |
| `logs/rg03-http-runs.response` | 300 | `4e565ed9b60f30d3c41e606b27ef73f829d08fe230f6a1c82a818603ef853dce` |

Raw runtime evidence remains outside Git in the retained inactive candidate root.
The post-execution machine-readable observation trace is versioned at
`docs/review-evidence/G8-RG03-STOP-ROLLBACK-20261001-001/stop-rollback-trace.json`
(8,093 bytes; SHA-256
`f981a085617cb47e0e597094d890afe9c19cc488df772f40d5ac50f879470bf0`;
Git blob `79f87c72fdc23ed09851f9aea46ecc7bc4a8393a`). The trace transcribes the
already returned tool output; it did not rerun the candidate or any process,
listener, service or scheduled-task query.

The trace records the known PID/parent/command identities, listener owner, final
known-PID and candidate-path absence, final listener zero, service/task zero and
their timestamp limits. It also preserves two evidence qualifications: the first
non-elevated final query was access-denied, and a first elevated path query reported
one self-match because the query command contained the candidate path. Neither is
used as successful absence evidence. The later self-excluding query is the source of
the zero candidate-path process result. Because the original final queries did not
emit a timestamp, their exact observation time remains `null` with the evidence
capture time as a lower bound. This versioned trace makes the transcription
tamper-evident; it is not represented as a native Windows audit log.

## 4. Disclosed stop diagnostic

The service reached application startup and served both HTTP requests. Stopping the
captured server process caused the blocking launcher script to record:

`LAUNCH_EXCEPTION | reason=PYTHON_INVOCATION_FAILED type=HostException`

This is not hidden or reclassified as a clean graceful shutdown. It is the launcher's
current diagnostic for externally terminating its child. The independent rollback
facts are that the exact child/root processes ended, the listener disappeared, no
service/task registration exists and state/log evidence remains. No retry or source
repair was performed.

## 5. Result and remaining gates

RG-03 is proposed `COMPLETE_OPERATIONAL_BOUNDARY`: the named candidate can be
isolated, started once, observed on loopback, stopped by exact process identity and
returned to a non-listening, non-autostart, evidence-preserving state.

RG-04 current Reviewer transport and RG-06 human limitation disposition remain
unfulfilled. This result is not distribution or release authority. `NO_RELEASE`
remains in force.

`ARTIFACT_QUALITY_CHECK: PASS` for the revision-002 evidence package because the
exact artifact, start/stop identities, HTTP evidence, final absence observations,
retained evidence, evidence qualifications and the non-clean launcher diagnostic are
fixed without overclaiming graceful shutdown or native OS audit provenance.
