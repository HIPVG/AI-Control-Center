# G7 SP-00 product revalidation authority — 2026-09-30

## Direct human decision

- Decision ID: `AUTH-G7-SP00-PRODUCT-REVALIDATION-20260930-001`
- Human authority holder: 広瀬剛
- Exact instruction: `許可します`
- Subject: the immediately preceding proposal to publish the SP-00 acceptance and
  perform one bounded G7 product revalidation of fixed implementation commit
  `3e82626faebab8e9722939b92267deb51075d93b`
- Source class: `RECORDED_DIRECT_CONVERSATION`
- Channel: current Codex Work chat
- Message identifier: `UNKNOWN`
- Exact received time: `UNKNOWN`

## Authorized effect and limits

- Action class: `VALIDATION`
- Target: Day 6 product path and SP-00 same-run asynchronous settlement projection.
- Product build: `3e82626faebab8e9722939b92267deb51075d93b`.
- Environment: isolated clean AI-Control-Center checkout and the previously approved
  clean LocalLLM-Lab baseline at
  `e33b0a410fb8647711f02ae4e6e0b66472e6eff0`.
- Window: 30 minutes of ACTIVE_WORK.
- Go limit: one attempt.
- Cost limit: 0 JPY.
- Reviewer Bus remains disabled; no Watcher restart or credential change.
- Create a current-build exact Grant and fresh Day 6 prerequisite observation only
  as required for this validation.
- Start the loopback service and use the browser only for Day 6 selection, one Go,
  and readback after the asynchronous worker settles.

## Required observation and stop boundary

Confirm whether the dashboard, API and durable RunRecord converge on the same run at
`EXTERNAL_ACTION_REQUIRED / REAL_MODE_REQUIRED` after asynchronous settlement. Preserve
the early `PREFLIGHT` response separately from the later settled readback. Do not
enable real mode, invoke a model, retry Go, repair source, operate Watcher, start G8,
claim product acceptance, spend money, alter credentials, merge, modify `main`, or
perform destructive Git operations. Stop after fixed evidence and review preparation.
