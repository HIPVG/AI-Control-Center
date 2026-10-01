# G7 product revalidation handoff after G6 PR-00 through PR-03

## Fixed repair scope

The accepted repair sequence addresses the three discrepancies from
`G7-PRODUCT-E2E-20261001-007` without rewriting that historical run:

- PR-00 binds completion Evidence to the exact product run and criterion;
- PR-01 creates same-run terminal attempt/token/budget/cost-availability telemetry;
- PR-02 orders Evidence, telemetry and terminal state projection and makes exact
  replay non-writing; and
- PR-03 proves the complete production-composition/FastAPI boundary with disposable
  stores and a deterministic injected executor.

## Evidence available to the next G7 decision

- Every Evidence item used for completion has exact run, criterion, Day, contract and
  configuration identity.
- Terminal Day state reaches the durable RunRecord only after Evidence and telemetry
  reconciliation.
- Attempt count and limit, token split, budget decision, and measured or explicitly
  unknown cost are preserved with sources and observation times.
- Exact replay is non-duplicating; incomplete, conflicting and cross-run facts fail
  closed.
- Reconstruction preserves the durable product state. The read-time projection
  timestamp is a fresh observation and is not persisted state.

## G7 boundary

After separate G6 stage-completion acceptance and separate human authority, G7 may
revalidate the repaired product path. This handoff does not authorize an actual Go,
Day/model execution, service/browser use, G8 or product acceptance. If the next G7
product run exposes another cross-component composition gap of the same class, stop
small-patch cycling and reassess the G4/G5 integration design and gate verification
method before another G6 repair.
