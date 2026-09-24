# Day 5 Artifact Quality Check

`ARTIFACT_QUALITY_CHECK: PASS`

- `evidence_type`: `artifact_quality_check`
- `source`: independent read-only inspection on 2026-09-24
- `verified`: `true`
- `validation.passed`: `true`

## Checks

| Required check | Result |
| --- | --- |
| expected Day 5 records exist | PASS — validator, local artifact, Teacher eligibility, limitation, and decision records exist |
| provenance traceable | PASS — Local run, config hash, candidate Teacher packet, validator reconstruction limit, and sources are named |
| denominator and precision artifact-derived | PASS — `11 = 3+3+2+0+3`; `11 valid`, `0 invalid`, `1.0000` |
| Local/Teacher comparison conditions traceable | PASS — Teacher packets prove `teacher_api_called:false`; incompatible historical cases are separated |
| incompatible evidence excluded | PASS — no Teacher precision or Local-vs-Teacher gap is calculated |
| false positive/negative traceability | PASS — 0 emitted invalid plans; false negatives explicitly not-evaluable because no selection gold set |
| decision linked to evidence | PASS — Critic low only for emitted-plan structural validity; Selector not-evaluable; DR-004 retained as upstream semantic finding |
| downstream usability | PASS — limitations and non-comparability are explicit, preventing reinterpretation as Teacher performance |
| protected scope | PASS — no model run/rerun/tuning/Critic or Selector implementation, prior Day mutation, persisted-state edit, or main change |

The quality check does not remove the stated limitations. It confirms that those
limitations are explicit and that no unsupported comparison or product decision
was introduced.
