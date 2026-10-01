# Temporal State Boundary

Temporal state is a Python-owned, fail-closed input boundary.  It carries four
separate partitions: `planned_time`, `actual_time`, `forecast_time`, and
`snapshot_time`.  Each partition has its own `as_of` timestamp and provenance
backed facts.  Equal fact IDs may appear in more than one partition because a
plan, an observation, and a forecast are different claims.

Consumers must request required facts by ID and, where relevant, their required
partition.  A planned or forecast fact never satisfies a requirement for an
actual fact.  Missing partitions, malformed timestamps, unknown fields,
duplicate IDs within a partition, or missing provenance are validation failures;
the caller must stop rather than fill the gap from another temporal partition.

The schema is `schemas/temporal-state.json`; deterministic validation is in
`scripts/eval/temporal_state.py`.  This boundary records time semantics only.
Temporal contradiction and issue rules remain a later deterministic validation
step and are not inferred by an LLM.
