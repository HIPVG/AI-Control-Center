# G7 clean-baseline product validation authority — 2026-09-30

## Direct human decision

- Decision ID: `AUTH-G7-CLEAN-BASELINE-VALIDATION-20260930-001`
- Human authority holder: 広瀬剛
- Exact instruction: `はい、進めてください。`
- Subject presented immediately before the instruction:
  1. preserve the existing dirty `C:/LocalLLM-Lab` working tree;
  2. create a separate clean worktree at
     `e33b0a410fb8647711f02ae4e6e0b66472e6eff0`;
  3. resume the bounded Day 6 product-E2E validation in a new G7 window.
- Source: `RECORDED_DIRECT_CONVERSATION` in the current Codex Work chat
- Message identifier: `UNKNOWN`
- Exact received time: `UNKNOWN`

## Authorized effect and limits

- Action class: `VALIDATION`
- Approved LocalLLM-Lab baseline:
  `e33b0a410fb8647711f02ae4e6e0b66472e6eff0` in a separate clean worktree.
- Existing `C:/LocalLLM-Lab` modifications and untracked files must remain untouched.
- Target: Day 6 product path only.
- ACTIVE_WORK limit: 30 minutes from this new window.
- Go limit: at most two attempts in this new window.
- Cost limit: 0 JPY; paid model or external paid action is prohibited.
- Reviewer Bus remains disabled; no Watcher restart or credential change is authorized.
- The local loopback service and browser may be used only as required by the accepted
  G7 verification plan and the previously accepted product-E2E boundary.
- This decision does not authorize production-code repair, G8, product acceptance,
  destructive Git operations, merging or modifying either repository's `main`.

## Stop and evidence boundary

Fail closed on an admission or prerequisite failure. Preserve the same-run API,
dashboard, Git, Evidence and telemetry observations without inferring unavailable
facts. If a product defect is observed, record it and return it to the applicable
gate; do not repair it inside this validation window. A completion or blocking result
requires its own fixed evidence and review.
