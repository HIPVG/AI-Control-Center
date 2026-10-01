# Temporal State Boundary

Temporal facts are admitted only through the `temporal-state.json` contract.
`planned`, `actual`, and `forecast` are separate collections; a fact never
changes collection implicitly. `snapshot_time` records when the complete state
was assembled, rather than the time the fact is planned, occurred, or forecast.

Every fact requires an identifier, value, effective time, and at least one
source record identifier. Actual facts may not have an effective time after the
snapshot. Missing buckets, unknown fields, malformed timestamps, missing
provenance, duplicate identifiers within a bucket, and actual-after-snapshot
claims fail closed. The validator does not infer actual facts from plans or
forecasts, and it does not mutate state.
