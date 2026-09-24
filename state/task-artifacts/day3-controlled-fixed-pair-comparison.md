# Day 3 controlled fixed-condition comparison

## Source artifacts

- v0.3.2: `C:\LocalLLM-Lab\results\day3-fixed-pair\v032\DRAP-20260923T143652-4d8123df`
  - manifest SHA-256: `8cf542fd911b413e5b9af994d2b43cc626ef8cb1a8d5fe12246766b347071908`
- v0.4: `C:\LocalLLM-Lab\results\day3-fixed-pair\v04\DRAP-20260923T143924-8e11506d`
  - manifest SHA-256: `9749d5af9107fab08427a01c59683ee71cfdda894c9c1ad46b5ad1e6e6ff3038`

Historical artifacts and the earlier checkpoint table are retained but are not
the numerical source of truth for this comparison.

## Pair comparability

- `CONDITION_MATCH: yes`
- `FACT_COUNT_MATCH: yes` (23 in every case of each run)
- `INPUT_HASH_MATCH: yes` (the five raw-case SHA-256 values match)
- `FACT_LAYER_HASH_MATCH: yes` (the five canonical-business-state SHA-256
  values match)
- `ONLY_INTENDED_VERSION_DIFFERENCE: yes` (v0.3.2 versus v0.4 action gate)
- Same model (`phi4:14b`), temperature (0), seed (42), context (4096), retry
  setting (`false`), output caps (1024), serial mode, and nine-call budget.

## Artifact-derived metrics

| Metric | v0.3.2 | v0.4 |
| --- | ---: | ---: |
| Plans | 12 | 11 |
| Valid plans | 10 | 11 |
| Invalid plans | 2 | 0 |
| Selected actions | 23 | 18 |
| Reasoner prompt tokens | 11,104 | 10,345 |
| Reasoner output tokens | 682 | 620 |
| Sum of case elapsed seconds | 106.533 | 83.829 |
| DR-005 blocking coverage | 0.667 | 0.667 |
| DR-005 mandatory coverage | 0.714 | 0.714 |

The v0.4 gate considered 75 action decisions: 28 permitted, 44 removed as
infeasible, and 3 removed despite feasibility because they were irrelevant to
an active verified issue. The latter were `NO_ACTION`, `RENEGOTIATE_DELIVERY`,
and `RESCHEDULE_PRODUCTION` (one case each).

## Retained model-quality findings

- v0.3.2: `DR-002:PLAN_VALIDATION`, `DR-004:SEMANTIC_ABSTRACTION`.
- v0.4: `DR-001:PLAN_VALIDATION`, `DR-004:SEMANTIC_ABSTRACTION`,
  `DR-005:PLAN_VALIDATION`.

No result was retried, tuned, hidden, or used to change the condition.

## Comparison conclusion

- `PLAN_QUALITY_REGRESSION: no` — valid plans rose from 10 to 11 and invalid
  plans fell from 2 to 0.
- `COST_REGRESSION: no` — reasoner input/output tokens and summed case elapsed
  time were lower for v0.4 in this one fixed-condition pair.
- `COVERAGE_REGRESSION: no` — the recorded DR-005 blocking and mandatory
  coverage values match.

## Artifact Quality Check

`ARTIFACT_QUALITY_CHECK: PASS`

Expected artifacts exist; provenance and immutable manifest identities are
recorded; fixed conditions and Fact Layer match; report values are
artifact-derived; the historical table is explicitly excluded; and a downstream
operator can use this pair without resolving an ambiguity. Day 4 must treat
this document as the source of truth only for the v0.3.2/v0.4 delta. Day 4's
holdout conclusions must use its own fresh-holdout artifacts, not this pair.
