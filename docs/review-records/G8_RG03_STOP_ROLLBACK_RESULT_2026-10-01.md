# G8 RG-03 Stop/Rollback Validation Result

- **Authority:** `AUTH-G8-RG03-STOP-ROLLBACK-20261001-001`
- **Procedure:** `G8-RG03-STOP-ROLLBACK-20261001-001`
- **Candidate:** `AI-Control-Center-Day6-Bounded-RC1`
- **Result:** `FIXED_FOR_REVIEW`
- **Extraction / start / stop:** `1 / 1 / 1`
- **HTTP reads:** `2 / 2`
- **Model, Day/Go, Watcher operation:** `0 / 0 / 0`
- **Cost:** 0 JPY

The accepted archive hash matched, the candidate extracted once with its fixed
124-file inventory, and the packaged launcher served two successful read-only
loopback requests in mock mode. The exact captured process tree was stopped once.
Final checks found no captured or candidate-path process, port-8000 listener,
candidate Windows service or candidate scheduled task. State, logs and raw HTTP
responses remain in the inactive candidate root.

The launcher recorded a `HostException` diagnostic when its child was deliberately
terminated. That diagnostic is retained and does not support a graceful-shutdown
claim. The proposed RG-03 claim is limited to usable exact-process stop and rollback
to a non-listening, non-autostart, evidence-preserving state.

`ARTIFACT_QUALITY_CHECK: PASS` for this limited RG-03 boundary. RG-04, RG-06 and
release remain separate; `NO_RELEASE` remains in force.
