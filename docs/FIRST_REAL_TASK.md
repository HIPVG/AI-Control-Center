# First real task: PC-001-A

- **Task ID:** `PC-001-A`
- **Source:** `C:\LocalLLM-Lab\benchmarks\business\process-consistency\cases.jsonl`; the individual case is selected by `scripts/run_process_consistency_smoke.py`.
- **Selection:** this is an existing official Process Consistency anomaly case, is independently selectable by `--cases PC-001-A`, and its `--dry-run` exits deterministically without a model or AI evaluator.
- **Precheck / postcheck:** `python scripts/run_process_consistency_smoke.py --dry-run --cases PC-001-A --output-root {artifact_root}`. The configured runtime expands `{artifact_root}` to a per-run Control Center state directory.
- **Allowed files:** `scripts/run_process_consistency_smoke.py`, `scripts/process_consistency.py`.
- **Context files:** the same two targeted runner/validator sources, bounded to 30,000 characters.
- **Expected initial result:** PASS based on the documented runner contract; it was not executed against LocalLLM-Lab in this development task.
- **Uncertainty:** no currently reproducible code failure was found during targeted read-only inspection. A PASS therefore returns `COMPLETE_NO_CHANGE`; a deterministic exit-1 failure is the only v1 condition triaged as `CODE_FIX`.
