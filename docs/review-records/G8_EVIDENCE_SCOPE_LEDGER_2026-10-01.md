# G8 evidence and scope ledger

- G8 plan: `G8-ACC-ACCEPTANCE-PLAN-20261001-001`
- Plan acceptance: `G8-ACCEPTANCE-PLAN-20261001-001` (`ACCEPT`)
- Fixed Day 6 product build: `656711367ed837ddbb75e6df65234a955e44900d`
- Accepted product evidence: `G7-PRODUCT-E2E-20261001-009`
- Accepted G7 result: `G7-STAGE-RESULT-20261001-002`
- Policy: `docs/WORKING_RULES.md` at
  `60c0fe7dcf8935fad4c6d3818256a94e95965501`

| G2 condition | Admitted evidence | Scope status | Claim excluded |
|---|---|---|---|
| A01 selected Day / Go | One authorized Day 6 browser Go, a single run ID, durable `COMPLETE`, API and dashboard readback. | `SUPPORTED_FOR_DAY6` | All-Day behavior, another Go or release. |
| A02 typed Evidence / completion | Six bound completion Evidence records and 4/4 criteria on the same Day 6 run; deterministic invalid-evidence guards. | `SUPPORTED_FOR_DAY6` | Other Day contracts and untested Evidence types. |
| A03 repair / revalidation | Accepted deterministic scope/Git/budget/attempt/return guards. No repair was required by the successful product run. | `CONTROL_SUPPORTED; PRODUCT_OCCURRENCE_NOT_EVALUABLE` | A claim that an actual repair succeeded. |
| A04 review / stop / recovery | Accepted correlation/continuation fixtures and one historical actual-actor path. Day 6 did not require a review round trip; current Watcher was not operated. | `CONTROL_AND_HISTORY_SUPPORTED; CURRENT_OCCURRENCE_NOT_EVALUABLE` | Live unattended review continuity, current liveness or real disconnect recovery. |
| A05 dashboard | Same-run Day state, durable RunRecord, API and visible dashboard readback converged on `COMPLETE`. | `SUPPORTED_FOR_DAY6` | General UI acceptance across all conditions/Days. |
| A06 result / relay / cost | Same-run attempt 1/2, token split, budget warning and reasoned unavailable JPY cost were retained. The run did not need a review relay. | `RESULT_AND_TELEMETRY_SUPPORTED_FOR_DAY6; RELAY_AND_MEASURED_COST_NOT_EVALUABLE` | A measured 0 JPY cost or a proven zero-relay review path. |

## Scope conclusion

The evidence supports a bounded Day 6 demonstration result. It does not support a
claim that all Day 1–14 are product-accepted, that release/continuous operation is
ready, or that actual repair/current review/cost measurement have been demonstrated.
No evidence is discarded or reclassified to make the scope appear broader.

`ARTIFACT_QUALITY_CHECK: PASS` — each conclusion has a fixed source and states its
proof boundary.
