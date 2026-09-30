# G7 product E2E revision 004 acceptance — 2026-09-30

## Review identity

- `PACK_ID`: `G7-PRODUCT-E2E-20260930-004`
- `REVIEWED_COMMIT`: `18be053bde907f646737bfd2f36753585d8e051d`
- Reviewer result: `ACCEPT`
- Applied policy commit: `60c0fe7dcf8935fad4c6d3818256a94e95965501`

## Accepted result

G7 returns to G6 only for the missing same-run state projection after the Day
executor settles. The accepted facts are:

- a current-build Grant and Day 6 prerequisite observation admitted one browser Go
  for `run-b229e3cee8a347b5bd621b799b146cda`;
- the Day controller stopped fail-closed at
  `EXTERNAL_ACTION_REQUIRED / REAL_MODE_REQUIRED`;
- the durable RunRecord for that same run incorrectly remained `PREFLIGHT` because
  production `RunCoordinator.go()` does not invoke the existing
  `RunExecutionComposition.project_day_state()` after the executor returns;
- A05 therefore fails and the bounded G7 result is `RETURN`;
- `REAL_MODE_REQUIRED` is a separate human/runtime-authority boundary and is not a
  reason to broaden this return.

This acceptance authorizes only preparation of the minimum G6 correction plan. It
does not authorize implementation, another Go, real-mode enablement, model execution,
service/browser work, Watcher operation, G8 or product acceptance. Implementation
remains a separate decision by 広瀬剛.
