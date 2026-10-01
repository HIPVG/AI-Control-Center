# G8 RG-03 Stop/Rollback Validation Result

- **Authority:** `AUTH-G8-RG03-STOP-ROLLBACK-20261001-001`
- **Procedure:** `G8-RG03-STOP-ROLLBACK-20261001-001`
- **Candidate:** `AI-Control-Center-Day6-Bounded-RC1`
- **Result:** `EVIDENCE_REPAIR_FIXED_FOR_REVIEW`
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

Reviewer revision 001 did not reject those recorded runtime facts; it rejected their
external traceability. The saved console observations are now fixed in the
create-only machine-readable trace
`docs/review-evidence/G8-RG03-STOP-ROLLBACK-20261001-001/stop-rollback-trace.json`
(8,093 bytes; SHA-256
`f981a085617cb47e0e597094d890afe9c19cc488df772f40d5ac50f879470bf0`).
The trace discloses the access-denied query, the excluded self-matching query,
unknown timestamps/image fields and its post-execution transcription provenance.
No candidate or OS state query was rerun to produce it, and it is not claimed to be
a native Windows audit log.

`ARTIFACT_QUALITY_CHECK: PASS` for this evidence-limited revision of the RG-03
boundary. RG-04, RG-06 and release remain separate; `NO_RELEASE` remains in force.
