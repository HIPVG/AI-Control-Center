# G6 PR-02 rejection repair — immutable replay

Reviewer rejected `G6-PR02-COMPLETION-20261001-001` because an already completed
run reached `bind_day_evidence()` before the replay guard. The evaluator recreated
the same IDs with new `collected_at` values and the Day snapshot was saved, so the
operation was not write-free even though the RunRecord stayed unchanged.

The bounded repair moves completed-run handling before Evidence binding. It now:

1. verifies the current bound Evidence in memory, including exact run, criterion,
   Day, contract, configuration and deterministic record IDs;
2. deterministically rebuilds the candidate terminal telemetry without storing it;
3. accepts only exact equality with the existing telemetry; and
4. returns `ALREADY_PROJECTED` without saving Evidence, Day snapshot, telemetry or a
   new RunRecord version.

Conflicting Evidence or telemetry is rejected before any write. The added assertions
compare the serialized Day snapshot and RunRecord before and after exact replay and
both conflict paths.

Under `AUTH-G6-PR02-REVALIDATION-RETRY-20261001-001`, the one additional execution of
the existing focused command passed `118 passed, 6 warnings in 189.55s`, exit `0`.
The warnings are the same existing FastAPI/Starlette deprecations. No further test
execution is authorized or performed.

`ARTIFACT_QUALITY_CHECK: PASS`
