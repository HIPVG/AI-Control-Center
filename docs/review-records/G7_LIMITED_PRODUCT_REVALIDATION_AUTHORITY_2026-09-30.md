# G7 limited product revalidation authority — 2026-09-30

## Direct human decision

- Decision ID: `AUTH-G7-LIMITED-PRODUCT-REVALIDATION-20260930-001`
- Human authority holder: 広瀬剛
- Exact instruction: `限定G7製品再検証  を承認します。進めてください`
- Subject: the bounded G7 product revalidation required after acceptance of
  `G6-AUTHORITY-FACT-STAGE-COMPLETION-20260930-001`
- Source class: `RECORDED_DIRECT_CONVERSATION`
- Channel: current Codex Work chat
- Message identifier: `UNKNOWN`
- Exact received time: `UNKNOWN`

## Authorized effect and limits

- Action class: `VALIDATION`
- Target: Day 6 product path only, using AI-Control-Center build
  `7b849803de140454b9f67beca98c52132a7bdb6f`.
- LocalLLM-Lab baseline:
  `e33b0a410fb8647711f02ae4e6e0b66472e6eff0` in the preserved clean validation
  worktree at `C:/AI-Control-Center/state/g7-local-llm-clean-20260930`.
- Allowed effect: `RUN_DAY_PRODUCT_VALIDATION`.
- Window: 30 minutes of ACTIVE_WORK.
- Go limit: at most two attempts.
- Cost limit: 0 JPY; no paid model or paid external action.
- Reviewer Bus remains disabled. No Watcher restart or credential change is
  authorized.
- The loopback service and browser may be used only to execute and observe this
  bounded product revalidation.
- Existing user work in both repositories must remain untouched.

## Stop boundary

Fail closed at the first admission, authority, prerequisite, implementation, or
evidence blocker. Preserve same-run API, dashboard, Git, Evidence and telemetry
observations. Do not repair product code in this validation window. Do not start G8,
declare product acceptance, change credentials, spend money, merge, modify `main`, or
perform destructive Git operations. A blocking or completion result requires fixed
evidence and separate review.
