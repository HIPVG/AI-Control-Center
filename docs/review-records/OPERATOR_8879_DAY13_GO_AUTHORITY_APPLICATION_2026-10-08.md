# 8879 Day 13 Go authority application — 2026-10-08

## Registered boundary

- Selected Day: `13`
- Objective: run the complete relevant regression and a genuinely new frozen
  holdout while retaining failures.
- Registration fingerprint:
  `6ea6809ca2d34212401d54ab3b3c2e918dd8bd1005f7bf34a2be391782a5ea2f`
- Completion: four criteria requiring `full_test_result`, a new-holdout evidence
  set, retained failures plus classification, and a status summary.
- Registered actions: read-only `D13_FULL_REGRESSION`, research
  `D13_NEW_HOLDOUT`, and decision output `D13_CLASSIFY_RESULT`.

## Smoke and output-path check

The non-effecting Smoke created no run and executed no project test, holdout, or
model. Completion construction is READY. It reported
`CONSUMPTION_UNKNOWN_ATTEMPTS` and `EFFECTIVE_PERMISSION_UNKNOWN`, plus missing
write scope for `D13_NEW_HOLDOUT` and `D13_CLASSIFY_RESULT`.

The action registry maps the only repository output scopes to:

- `results/day-runner/day-13/` for the holdout research output;
- `docs/day-13-report.md` for the result classification and summary.

`git check-ignore --no-index` confirms the Day 13 results path is excluded by
the repository's `results/` rule. No Day 13 action proposes output under
`datasets/` or `artifacts/`. `docs/day-13-report.md` is the exact registered
source-document output, intentionally not ignored. The read-only full regression
has no repository output scope.

A bounded read found no existing JSON config declaring
`research_kind: fresh_holdout` with its exact registered entrypoint in the
isolated Lab. This is not repaired or invented before Go; if the registered
research planner cannot produce a valid frozen condition, that failure must be
preserved.

## Human authority mapping

Direct authority record:
`AUTH-OPERATOR-8879-DAY3-14-CONTINUE-20261008-001` in
`OPERATOR_8879_DAY3_14_CONTINUATION_AUTHORITY_2026-10-08.md`.

The server-validated profile proposal changes only `write_paths`, adding the two
registered paths above to profile v16. Operations, roles, network/model/credential
declarations and the limits remain unchanged at 1,800 active seconds, 3 attempts,
20,000 tokens, and 500 JPY. Proposal effective fingerprint:
`20234404fcea5992d670d87b172ba3746309f7fde26f264f7c279e4277b94d50`.

This is within the recorded direct authority because it is the ordinary 8879
permission confirmation for one sequential Day, with screen-disclosed scope and
unchanged limits. It does not authorize an output outside these paths, a changed
holdout condition, retry after a model-quality failure, `.gitignore` change,
original-Lab change, destructive Git operation, commit, or push.

## Next action

Approve and read back this exact profile change, repeat Smoke, then display the
single-Go confirmation. If the proposal, paths, limits, target Git version, or
exclusion check changes, stop. Otherwise map the one Go and separate allocation
to the same direct human authority, start only one new Day 13 run, and preserve
the actual full-regression and holdout outcome.
