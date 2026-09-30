# G6 AF-00 expiry-boundary rejection repair

## Review result applied

- Rejected pack: `G6-AF00-COMPLETION-20260930-001`
- Rejected commit: `2a42323b6999b6e79fc34c6c9ec08edaabe9fcd6`
- Result: `REJECT`
- Concrete defect: `now > expires_at` admitted a grant at its exact expiration
  instant; no assertion covered that equality boundary.

The rejection was applied without broadening into AF-01 or product operation.

## Minimum repair

- Changed the valid-time condition to reject when `now >= expires_at`.
- Added one assertion where the resolver clock and `expires_at` are exactly equal.
- The assertion requires permission to remain unknown and every grant-provenance
  field to remain absent, while independently valid prerequisite evidence may still
  resolve `True`.

## Validation boundary

The earlier broad focused command has exhausted its recorded executions. The repair
therefore declares one new, narrower command for the exact changed boundary:

```text
python -m pytest -q tests/test_preflight_authority.py -k exact_expiration
```

Execution 1 exited `0`: `1 passed, 18 deselected in 0.87s`. The assertion directly
confirmed the equality boundary and absence of Grant provenance after rejection.

`ARTIFACT_QUALITY_CHECK: PASS`

No service, browser, Go/Day, model, Watcher, credentials, spending, AF-01, G8 or
product acceptance is part of this repair.
