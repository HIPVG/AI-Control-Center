# G6 same-run state-projection plan revision 002 acceptance — 2026-09-30

## Review identity

- `PACK_ID`: `G6-SAME-RUN-STATE-PROJECTION-PLAN-20260930-002`
- `REVIEWED_COMMIT`: `c6b81eb779350f9f2ed1be47bcc6da1a23c3aa0b`
- Reviewer result: `ACCEPT`
- Applied policy commit: `60c0fe7dcf8935fad4c6d3818256a94e95965501`

## Accepted scope

Revision 002 is accepted as the minimum sufficient G6 plan for the bounded G7 return.
The accepted SP-00 boundary is:

1. the asynchronous Day worker reaches a non-active state;
2. its final snapshot save succeeds;
3. the captured run ID emits one notification for that execution episode;
4. the existing guarded `project_day_state()` performs the same-run durable
   projection;
5. early return, save failure, identity mismatch and projection rejection remain
   non-applying.

There is no unresolved gap in the plan scope. Implementation and deterministic
fixture proof remain unperformed. This acceptance does not authorize source changes,
test execution, service/browser, Go/Day, real-mode/config change, model, Watcher,
credentials, spending, G8 or product acceptance. SP-00 implementation requires a
separate direct decision by 広瀬剛.
