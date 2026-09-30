# G7 Day 6 real-mode validation preflight block — 2026-10-01

## Fixed scope and result

- Authority: `AUTH-G7-DAY6-REAL-MODE-20261001-001`
- Product build: `3e82626faebab8e9722939b92267deb51075d93b`
- LocalLLM-Lab baseline: `e33b0a410fb8647711f02ae4e6e0b66472e6eff0`
- Run ID: `run-a64337972833404e9f5dcd4265f6765f`
- Result: `INPUT_BLOCKED`
- Run state: `HUMAN_ACTION_REQUIRED`
- Blocker: `EFFECTIVE_PERMISSION_UNKNOWN`
- Cost: 0 JPY
- Real-model executions: 0
- Effective Go POSTs: 1

## Observed facts

The isolated product worktree loaded `codex.mode: real` with the current installed
Codex executable. The clean LocalLLM-Lab checkout remained at the authorized commit
and fingerprint. Reviewer Bus was disabled.

Browser selection of Day 6 created no run. Mouse activation attempts did not produce
a POST and therefore did not consume the Go limit. Keyboard activation of the same
enabled Go control produced exactly one successful
`POST /api/local-llm/day/go` and created the run above.

The prerequisite observation matched exactly. The authority Grant did not match:

- generated immutable RunIntent: `max_attempts: 2`;
- recorded Grant: `max_attempts: 1`;
- preflight permission result: `AUTHORITY_GRANT_NOT_MATCHED`;
- effective permission: unknown;
- execution did not start;
- no Codex/model activity, token usage, Day output worktree or LocalLLM-Lab change
  was observed.

The blocked RunRecord and preflight fact were retained. The loopback service was
stopped and port 8023 no longer listened.

## Classification and correction

This is an experiment-condition/authority-record mismatch introduced when the
one-real-model-execution restriction was encoded as the RunIntent attempt limit.
The product creates a fixed two-attempt RunIntent, while the Day 6 engineering
adapter separately enforces `max_codex_attempts=1`. Therefore a matching Grant must
retain `max_attempts: 2`; the one-model limit remains enforced at the actual Codex
execution boundary.

The existing blocked run cannot be reused after correcting the Grant because
`RunCoordinator` fail-closes a new Go while a nonterminal current RunRecord exists.
Do not erase or overwrite that state. A new isolated validation worktree and one
additional Go require a separate human authorization.

## Stop boundary

No retry, service restart, model invocation, source repair, Watcher operation, G8 or
product acceptance was performed. G7 remains stopped for the additional-Go decision.
