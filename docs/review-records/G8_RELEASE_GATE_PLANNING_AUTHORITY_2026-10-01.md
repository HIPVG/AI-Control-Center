# G8 GA-03 Release-Gate Planning Authority

## Authority identity

- **Authority ID:** `AUTH-G8-GA03-RELEASE-GATE-20261001-001`
- **Decision maker:** 広瀬剛
- **Source class:** `RECORDED_DIRECT_CONVERSATION`
- **Received through:** current Codex Work chat
- **Message ID / exact received time:** `UNKNOWN`
- **Record date:** 2026-10-01

## Exact human approval

> 承認します。進めてください。

This exact approval confirms the immediately preceding, fully specified GA-03
authority proposal in the same direct conversation. It is not independent access to
the original human message outside this chat.

## Approved planning scope

- **Candidate product build:** `656711367ed837ddbb75e6df65234a955e44900d`.
- **Decision/evidence baseline:** current work branch through
  `bb09f76067420b32d0b0de2488793186dfa0dacf` before this authority record.
- **Operating owner:** 広瀬剛.
- **Proposed acceptance environment:** Windows local operation, bound to
  `127.0.0.1` only; no external publication or distribution.
- **Planning-only rollback model:** no process starts during planning. Any later
  authorized operation must stop its loopback service, restore `NO_RELEASE`, and
  preserve JSON state, logs and evidence without destructive Git operations.
- **Review requirement:** Review Bridge PR #1 is the plan-review path. Current
  Watcher liveness is an unsatisfied requirement for continuous operation or release,
  not evidence to be assumed.
- **Cost and credentials:** no spending; no credential addition/change/recording;
  measured JPY cost remains `UNKNOWN` and is not read as 0 JPY.

## Explicit exclusions

This authority permits only release-gate planning, records and review preparation. It
does not permit product release, distribution, service or Watcher operation, Day/Go,
model execution, tests, credential changes, spending, destructive Git actions, or a
claim of all-Day product acceptance.
