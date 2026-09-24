# Day 5 Teacher evidence eligibility record

- `evidence_type`: `teacher_evidence`
- `source`: frozen v0.5 `teacher-packets/DR-*` and prior `results/decision-generalization/*/teacher-packets` manifests/instructions
- `verified`: `true`
- `validation.passed`: `true`
- `eligible_for_local_teacher_precision_comparison`: `false`

No actual compatible frozen Teacher result exists. The v0.5 packets have prompts, frozen inputs, registries, and gate records but no Teacher response/result; each `teacher-instructions.json` records `teacher_api_called: false`. Earlier `T-STRUCTURED`/`T-RAW` rows are also ineligible: their corresponding manifests/instructions record `teacher_api_called: false`, and their cases differ from v0.5 DR-001..DR-005.

`TEACHER_COMPARABLE: no`; `TEACHER_PRECISION: not-evaluable`; `PRECISION_GAP: not-evaluable`. This is a provenance/eligibility result, not an authorization for a new Teacher run.
