# Day 5 validator result

- `evidence_type`: `validator_result`
- `source`: `C:\LocalLLM-Lab\results\decision-reasoning-v0.5\DRAP-20260922T095508-e2196fec\validation.jsonl`
- `verified`: `true`
- `validation.passed`: `true`

## Identity and rule

The recorded artifact has the output shape of `eval.plan_skeleton_validator_v32.validate_plan_skeleton`. A date-aligned reconstruction identifies LocalLLM commit `681b4763722cf9cfcbaa27dac4058aa2e5565b31`, validator blob `582be38ff5f78b2221152618ae7f7c29827de2c0`, and runner path `decision_reasoning_v4 -> decision_reasoning_v32.run`.

Each emitted plan must have valid schema/status/action list, known feasible actions, no incompatible pair, an active-issue effect mapping, no duplicate action-set, and no contradictory decision status. The artifact also records upstream `FEASIBLE_RELEVANT_ACTION_GATE-v1`.

## Calculation

The denominator is the sum of emitted plans, not the five cases: `3 + 3 + 2 + 0 + 3 = 11`.

| Measure | Value |
| --- | ---: |
| emitted-plan sample count | 11 |
| valid plans | 11 |
| invalid plans | 0 |
| emitted-plan validity precision | 1.0000 (11 / 11) |
| emitted invalid plans / false positives | 0 |
| false negatives | not-evaluable |

False negatives are not measurable: this validator supplies no gold set of unselected valid/best plans. DR-004 produced zero plans after `SEMANTIC_ABSTRACTION` failure, retained as an upstream failure rather than relabelled as a plan-selection false negative.

## Provenance limit

The v0.5 manifest stores gate version and validation outputs but no artifact-embedded validator source hash. The identity above is a date-aligned reconstruction; counts derive solely from frozen `validation.jsonl` fields.
