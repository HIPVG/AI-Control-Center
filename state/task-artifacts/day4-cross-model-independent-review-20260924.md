# Day 4 fixed-condition cross-model independent review

## Scope and provenance

- Experiment: `C:\LocalLLM-Lab\results\day4-cross-model\EXP-20260923T151059-424c537a66`
- Profile: `week1-day4-cross-family`; local source commit recorded by both child manifests: `e33b0a410fb8647711f02ae4e6e0b66472e6eff0` (dirty working tree recorded by the runner).
- Baseline child run: `PCSMOKE-20260923T151059696929Z-b3e4860f`, `phi4:14b` (`phi4-14b-q4`).
- Comparison child run: `PCSMOKE-20260923T151405234723Z-8ec5370f`, `qwen3-14b-q4:latest` (`qwen3-14b-q4`).
- Top-level artifact SHA-256: manifest `6E4937F95329821B42BEBD99E8B9C3B2BC906CD4CA0D4A823615986BB634C29F`; comparison `54FD774B87AD81DE2DA38C28724E638EF20CB2736C73E07168EA493E3045D3C4`; responses `09984B4D6577F921E75A853FD0D40042AAD679FE293F9530372BDBBB9ACAABF4`.

## Fixed-condition validation

Both child manifests record the same four input SHA-256 values, case-manifest SHA-256 `2dc0661e6b2b4afad83273a76eea03b2f75485f4cf81d4ef10f6906f7ba6aed7`, system-prompt SHA-256 `04c27fdc8b9ab9f77fb0b3e57a88921b0ebce2ba0d7b41e050a8c21fcdba6668`, and settings: Ollama 0.34.2, temperature 0, seed 42 (requested/sent; model determinism not independently verified), context 8192, max output 1024, thinking disabled, timeout 120 seconds, no RAG, and one sequential repeat. Every response has `status=success`; all 8 artifacts exist. `validate_experiment_config.py --experiment` returned `valid=true`, `validated_rows=8`.

## Independent business-quality review

The review oracle was read only after the model run and was not supplied to either model. It defines PC-001-A as a 60-piece supply-evidence gap, PC-001-C as quantity-consistent, PC-003-A as the `compatible=False` / `recommended=True` contradiction, and PC-003-C as the consistent `False` / `False` control.

| Case | phi4:14b | qwen3-14b-q4 | Independent finding |
| --- | --- | --- | --- |
| PC-001-A | Finds 800 vs 860 and cites Records 4/5/7, but treats zero released inventory as an additional inconsistency and suggests process noncompliance without establishing it. | Finds the 860 vs 800 issue with record references, but implies possible defective-product shipment and continues into unsupported inventory/traceability concerns; output is truncated at the cap. | Both detect the material quantity gap but neither states the required 60-piece calculation or keeps the distinction between missing supply evidence and confirmed defective shipment reliably enough. |
| PC-001-C | Correctly explains 860 QA + 0 other-lot stock = 860 shipment, then wrongly elevates `lot_id=none` in the zero-quantity stock record into a traceability issue. | Incorrectly calls the expected 860/0/860 control an inventory inconsistency and adds unsupported shipment-impossibility risk. | Both produce a false-positive operational concern on a no-action control; Qwen's is materially stronger. |
| PC-003-A | Invents a CN/AMER regional inconsistency and says non-recommendation despite the record's `recommended=True`; it misses the actual compatibility/recommendation contradiction. | Identifies the exact `compatible=False` / `recommended=True` conflict in the named compatibility record and keeps unknown facts explicitly unknown. | Qwen catches the critical intended signal; phi4 does not. |
| PC-003-C | Invents CN/AMER regional inconsistency and proposes an ungrounded usage scenario despite the consistent `False` / `False` control. | Correctly states no inconsistency, while adding a conditional, non-factual request to check actual use. | Qwen is materially better at recognizing this control, though its follow-up is broader than the evidence requires. |

## Comparison result

- **Critical business-signal coverage:** Qwen captures the compatibility contradiction in PC-003-A; phi4 does not.
- **Control behavior:** neither model is safe enough to treat all extra concerns as findings. Phi4 yields false-positive escalation in both controls; Qwen yields a clear false positive in PC-001-C and an unnecessary conditional follow-up in PC-003-C.
- **Groundedness:** Qwen is better for PC-003-A/PC-003-C; both need an independent verifier for PC-001 quantity semantics. Phi4's PC-003-A statement that the item is not recommended contradicts the stored record.
- **Completion/truncation:** phi4 had four `done_reason=stop`. Qwen had three `stop` results and PC-001-A `done_reason=length` at 1024 output tokens. This is evidence, not a retry trigger.
- **Performance:** phi4 total 185.25 s, 2,836 output tokens, mean 46.31 s/case, 16.19 output tokens/s. Qwen total 108.61 s, 2,745 output tokens, mean 27.15 s/case, 31.40 output tokens/s. Qwen used a 1.71x lower total wall time (76.64 s less) while its peak GPU measurement was 11,564 MB vs phi4's 11,371 MB. GPU telemetry is runner-reported peak, not an independent hardware certification.

## Business conclusion and limitation

Under this one fixed four-case run, Qwen is materially better at the compatibility decision gate and faster, but it is not established as a stand-alone manufacturing reviewer: it produces a serious false positive on PC-001-C and one response was truncated. Phi4 is not preferable for this task because it misses the PC-003-A core contradiction and invents unsupported regional/flag interpretations. Continue to require deterministic case/oracle validation before a business action; no model-quality result authorizes tuning or rerun.

## Artifact quality check

`ARTIFACT_QUALITY_CHECK: PASS` for the completed cross-model experiment itself: expected files exist; hashes, versions, source commit, model identities, runtime conditions, response status, and derived metrics are traceable; child input and prompt hashes match; metric totals match the stored response records; and this review cites the exact artifact paths.

This does not make the old persisted Day 4 controller contract complete. That contract still describes a different fresh-holdout/metamorphic task, so registering this experiment as formal Day 4 typed evidence would require an explicit contract/authority decision rather than a state edit.
