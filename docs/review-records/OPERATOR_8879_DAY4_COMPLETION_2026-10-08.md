# 8879 Day 4 completion record — 2026-10-08

## Scope and identity

- Instance: `state/product-operator-normal-v1`
- Target: isolated `state/product-operator-normal-v1/local-llm-lab`
- Target Git HEAD: `e33b0a410fb8647711f02ae4e6e0b66472e6eff0`
- Day: `4`
- Product run: `run-6231d401c6eb415bbf48e3a4d5e45796`
- Preserved producer run: `EXP-20260923T151059-424c537a66`
- Contract: `2026-09-22-v2-evidence-contract`
- Contract fingerprint: `69df6d6afff2ac86506acd22d35e78a093fc76aedfbcdb3d02e0c3f79ddd3140`
- Registration fingerprint: `6ba8cbebe4f80ce1c2bcb28ccaa4f66584ab1216a7a6d1cc7c241e71a38d9987`
- Authority profile: v7, fingerprint `3c342296feb943f0219fc1331ce996c51b6f96b9e41a4be54be242e2436de764`
- Separate Go allocation: `goa-1daa6ce7488b48c89ffd6ef95cb9522e`, 1,800 seconds / 3 attempts / 20,000 tokens / 500 JPY

## Fixed comparison evidence

- Models: `phi4:14b` and `qwen3-14b-q4:latest`.
- Cases: `PC-001-A`, `PC-001-C`, `PC-003-A`, `PC-003-C`.
- Conditions: temperature 0, seed 42, context 8192, output cap 1024, reasoning disabled, repeat 1.
- Stored responses: 8/8 status `success`, four per model. No response was rerun.
- Condition fingerprint: `aacd379b28e1971654f91bcc395d03621d21b60c89059f03b7cf6364d6ed75a9`.
- Manifest SHA-256: `6E4937F95329821B42BEBD99E8B9C3B2BC906CD4CA0D4A823615986BB634C29F`.
- Comparison SHA-256: `54FD774B87AD81DE2DA38C28724E638EF20CB2736C73E07168EA493E3045D3C4`.
- Responses SHA-256: `09984B4D6577F921E75A853FD0D40042AAD679FE293F9530372BDBBB9ACAABF4`.
- Original and isolated copies each contain 20 files / 155,891 bytes; relative-path and SHA-256 comparison found 0 differences.

## Result and quality limits

- phi4: average 46.3122 seconds, 601 prompt tokens, 709 output tokens, 4/4 successful responses, peak GPU memory 11,371 MB.
- Qwen3: average 27.1519 seconds, 572.5 prompt tokens, 686.25 output tokens, 4/4 successful responses, peak GPU memory 11,564 MB.
- One Qwen3 response ended with `done_reason=length` at the output cap.
- Human quality score fields remain unmeasured/null for both models. The retained conclusion is `PARTIAL_IMPROVEMENT_REQUIRES_INDEPENDENT_REVIEW`.
- Retained limitations remain: unsupported control concerns and one output-cap response. No model-quality winner is asserted.

## Product execution and preserved failure

The first and only Day 4 Go created the product run above, but initially stopped as `EXTERNAL_ACTION_REQUIRED / CODEX_RESEARCH_EXECUTION_PLANNER_CODEX_NOT_FOUND` before research execution. The failed planner attempt remains in `action_attempts`; no inference or artifact generation occurred in that attempt.

The already existing producer run was copied read-only into the isolated Lab. The Day 4 retained resolver was repaired only to attach the same current contract/configuration/source-hash attestation already required by the fail-closed validator. A second local fix allows a fully satisfied retained-evidence Resume to bypass model-action budget admission, and terminal telemetry preserves the failed planner attempt instead of treating it as zero usage.

After the same-run Resume and canonical settlement:

- Day snapshot and RunRecord are both `COMPLETE` for the same run.
- Four contract criteria are satisfied with `STRICT` binding; remaining gaps are empty.
- Six retained evidence types validate: baseline artifact, comparison artifact, condition, validation, metrics, and quality assessment.
- Telemetry records 1 attempt. Input/output/cached/uncached tokens are `UNKNOWN` with `RESEARCH_PLANNER_USAGE_MISSING_OR_INVALID`; cost is `UNKNOWN`; budget decision and manual relay count are `UNKNOWN`.
- The earlier `RESUME_RECHECK_BLOCKED` problem and `EXTERNAL_AUTHORITY_REQUIRED` classification remain visible as historical failure evidence even though the terminal RunRecord is complete and has no blocker.

## Validation and boundaries

- Focused tests: 18 passed; Python compilation and `git diff --check` passed.
- 8879 UI readback shows the same run `COMPLETE`, 4/4 strict criteria, attempt count 1, token UNKNOWN, and cost UNKNOWN.
- Isolated Lab HEAD is unchanged and its Git index/worktree remains clean because generated results are ignored. It remains 11 commits ahead of `origin/main`.
- Original `C:\LocalLLM-Lab` was read only. Its existing dirty paths remain present; no reset, cleanup, commit, or push occurred.
- AI-Control-Center code changes are local and uncommitted. No unrelated tests, redesign, model execution, or contract weakening was performed.

## Artifact quality check

`ARTIFACT_QUALITY_CHECK: PASS`

The stored artifacts, fixed conditions, producer identity, hashes, eight responses, metrics, truncation, quality unknowns, failed planner attempt, and missing usage are traceable. PASS is limited to the Day 4 registered evidence contract and does not assert that either model has acceptable production quality.

## Product reviewer re-evaluation

- Report `PRODUCT-RUN-DAY4-COMPLETE-20261008-001` was delivered as PR #1 comment `6050819523`.
- Matching response `PR1-COMMENT-6050832875` returned `CONTINUE` and authorized only same-run re-evaluation.
- The existing product re-evaluation path read the same run and confirmed the exact contract fingerprint `69df6d6afff2ac86506acd22d35e78a093fc76aedfbcdb3d02e0c3f79ddd3140`.
- All four criterion records remained satisfied. Their bound evidence record IDs were re-evaluated by the contract evaluator, and `verify_bound_day_evidence` returned `ACCEPTED` without starting Day execution.
- The persisted expected and observed effect IDs both equal `76810b4c59f1bab7da02019b81b65a96b3f6bd2486aaff80feb1499b8222c77f`.
- No new run, model execution, Lab change, contract change, authority expansion, or code change occurred during this re-evaluation.
