# G6 same-run state-projection plan rejection — 2026-09-30

## Review identity

- `PACK_ID`: `G6-SAME-RUN-STATE-PROJECTION-PLAN-20260930-001`
- `REVIEWED_COMMIT`: `575108e0a73d1d8ffdffb95724c0341e0e2ef108`
- Reviewer result: `REJECT`
- Applied policy commit: `60c0fe7dcf8935fad4c6d3818256a94e95965501`

## Applied finding

Revision 001 placed projection after the executor returned. That is too early:
`LocalLLMDayProgram.start()` starts `_execute` on a daemon thread and immediately
returns its current view. The default Engine executor returns that value unchanged.
Consequently, a return-time projection can persist `PREFLIGHT` before the worker later
saves `EXTERNAL_ACTION_REQUIRED / REAL_MODE_REQUIRED`, preserving the observed G7
defect.

The correction is limited to the invocation point. The revised plan must notify the
existing guarded projection only after the Day worker has reached a non-active state
and successfully persisted it, exactly once for that execution episode and same run.
No implementation, test, additional Go, real-mode change, model, G8 or state-model
redesign is authorized by this rejection.
