# First controlled Codex repair validation

- Fault ID: `PC-001-A-CONTROLLED-FAULT`
- Target case: `PC-001-A`
- Target source: `scripts/process_consistency.py`
- Fault category: QA shipment anomaly comparison operator, injected only in the disposable worktree.
- Baseline command: `python scripts/validate_process_consistency_cases.py`
- Precheck command: `python scripts/validate_process_consistency_cases.py`
- Postcheck command: `python scripts/validate_process_consistency_cases.py`
- Allowed repair file: `scripts/process_consistency.py`

Expected sequence: clean source baseline PASS, worktree-only fault injection, deterministic precheck FAIL, Codex repair, Scope Guard PASS, deterministic postcheck PASS, then a Git-clean target file relative to `HEAD`. A passing but different implementation requires human review for this first experiment.

Historical run `3e50caa708284b8da2d3b3067b194d9b` had POSTCHECK PASS, Scope Guard PASS, and an empty target-file Git diff. Its old byte-sensitive comparison result is preserved as historical evidence only.
