# Git branch inventory — 2026-10-08

This is a branch-use marker, based on local refs and a live `git ls-remote
--heads origin` readback on 2026-10-08. It does not delete commits or alter the
Day Runner's persisted state.

| Branch | Disposition | Reason |
| --- | --- | --- |
| `agent/g0-g5-baseline-publication` | Current publication branch | Checked out in `C:/AI-Control-Center`; existing staged work must be reconciled separately. |
| `codex/results-publication-20261008-001` | Retain | Checked out in `state/main-publication-20261008-001`; its head matches the observed `origin/main`. |
| `agent/autonomous-multitask-orchestration` | Retain | `docs/WORKING_RULES.md` names this as the canonical policy branch. The local ref is behind its live remote ref. |
| `ai-control-center/day1-baseline-afe966e422e9fd2a` | Historical; do not use for new work | It has one commit not contained in observed `origin/main`. Preserve the checkpoint until its evidence is reconciled. |
| Local `main` | Do not use for new work | Observed 398 commits behind `origin/main`; policy keeps `main` read-only. |
| `origin/codex/archive-*` (three refs dated 2026-09-24) | Archived; do not use for new work | The archive names already mark their purpose. Each has commits not contained in observed `origin/main`, so retain the refs as history. |

No branch was proven safe and unnecessary to delete. In particular, the historical
Day 1 checkpoint and archive refs contain unique commits, and the other branches
are current, checked out, protected, or named by policy. Re-evaluate this inventory
against fresh remote refs before any future deletion.
