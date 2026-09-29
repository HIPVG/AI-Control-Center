# G6 RI-02 completion rejection

- Pack: `G6-RI02-COMPLETION-20260929-001`
- Reviewed commit: `8aa9b7d97243b7486d259abab0822dc1bba7b7fe`
- Result: `REJECT`

The Reviewer accepted the request-time production-store composition, current/history
separation, same-run criteria and telemetry, unknown-value retention, and restart
readback assertions. The remaining defect is limited to semantic validation of
version history: a valid RunRecord for another run could be placed in the target
run's history directory and used as the initial admission version.

The bounded repair validates every stored version against both the requested run ID
and the complete immutable intent of the current RunRecord before returning any
version. A focused assertion injects valid other-run JSON into the current run's
history and requires the composed read model to return no selected/current run and
no admission.

## Repair validation

Declared repair command:

`python -m pytest tests/test_run_projection_composition.py tests/test_run_contract.py -q`

Attempt 1 passed `15 passed, 6 warnings in 1.88s`. The assertions separately cover
a valid version with another run ID and a valid same-run version whose immutable
intent differs. Both produce no selected/current run and no admission. No second
attempt was used; warnings are the existing FastAPI/Starlette deprecations.
