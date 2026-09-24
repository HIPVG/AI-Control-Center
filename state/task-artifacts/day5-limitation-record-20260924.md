# Day 5 limitation record

- `evidence_type`: `limitation_record`
- `source`: Day 5 frozen Local and Teacher provenance audit
- `verified`: `true`
- `validation.passed`: `true`

1. Local `11/11` measures emitted-plan structural/constraint validity only, not recall, best-plan selection, or business-decision precision.
2. The validator lacks a gold set of unselected valid plans; local false negatives are not-evaluable.
3. DR-004 zero plans follow semantic-abstraction failure, an upstream semantic finding rather than a plan-selection false negative.
4. No actual compatible frozen Teacher result exists; Teacher precision and Local-vs-Teacher gap are not-evaluable.
5. Local artifact validator source identity is reconstructed, not embedded as a source hash.
