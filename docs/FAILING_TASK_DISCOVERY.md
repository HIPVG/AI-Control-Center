# Deterministic failing-task discovery

On 2026-09-21, all 24 configured Process Consistency case IDs (`PC-001-A/C` through `PC-012-A/C`) completed the targeted dry-run with exit code 0. `PC-001-A` had already been confirmed through the configured task endpoint; discovery checked the remaining 23 cases and found no deterministic failure.

The initial LocalLLM-Lab `.venv` could not start because its interpreter path was unavailable. This was classified as an environment issue, not a case or code failure. The dry-runs were then executed with the verified Control Center Python and wrote only temporary discovery output; no LocalLLM-Lab source or case data changed.

`config/discovery.yaml` is the trusted source for future discovery. It enumerates only real case IDs and runs the existing dry-run command. A candidate is selected only when a configured machine-readable `code_fix_error_codes` entry is observed; the current configuration intentionally has none because no genuine code failure was found.
