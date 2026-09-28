# G6 WC-02 bounded repair authority

- Decision ID: `AUTH-G6-WC02-REPAIR-20260928-001`
- Decision maker: 広瀬剛
- Source: `RECORDED_DIRECT_CONVERSATION`, this Codex chat
- Exact human instruction: 「１．で進めてください。」
- Context: the immediately preceding two choices were (1) a named limited
  ratification of the actual edit route, bounds repair, and one new focused
  fixture attempt, or (2) leaving WC-02 unaccepted and stopped.

## Bounded authorization

The authorized editor is the existing foreground Codex actor operating in
`C:\AI-Control-Center`, using `apply_patch` for reviewed source/test changes and
explicit-path Git commit/push through the existing host-approved repository
workflow. This does not authorize the Watcher child, `codex exec` child, a new
writer, a service reload, or a new authentication mechanism.

Authorize only the following WC-02 repair:

1. reject a `RunIntent` whose `requested_limits.active_work_seconds` exceeds
   1800, or whose `requested_limits.max_attempts` exceeds 2, with a concrete
   fail-closed admission blocker;
2. add only the focused boundary assertions needed for those two rejects; and
3. run one fresh-process focused fixture command once after the patch.

The work window is the normal 30 minutes of ACTIVE_WORK, with exactly one new
fixture attempt for this repair and zero cost. The prior WC-02 fixture tally
remains historical evidence and is not relabelled or reused as the new attempt.

No Day selection/Go, model invocation, service operation, credential change,
external product operation, paid work, destructive Git action, WC-03, or wider
policy/config/UI change is authorized. Stop after the one focused fixture result
and deliver the fixed commit for review.
