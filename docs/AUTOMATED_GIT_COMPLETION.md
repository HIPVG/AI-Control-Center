# Automated Git Completion Policy

## Purpose

M26 converts a *trusted, already-verified* code-change worktree into a local
commit, an `agent/` remote branch, and a structured pull-request preparation.
It does not create a pull request and it never merges or pushes `main`.

## Candidate contract

Candidates are derived only from persisted `TaskRunResult` records. A record
must be `COMPLETE` with `final_result=COMPLETE`, deterministic
`postcheck_result=PASS`, `scope_guard_result=PASS`, a managed worktree, an
`agent/` task branch, and a non-empty changed-file set.

The Dashboard receives only the run ID, configured task/project IDs, branch,
and changed-file list. It cannot submit a Git command, filesystem path, remote,
base branch, commit message, or target branch.

## Completion contract

Before mutation, trusted Python rechecks:

1. the worktree is on its persisted `agent/` branch;
2. the configured project default branch exists and is not the target branch;
3. `origin` exists;
4. current changed files exactly equal the verified changed-file set and remain
   inside the allowed-file scope;
5. `git diff --check` passes; and
6. a local Git commit identity is configured.

Only then it stages the verified paths, commits a fixed generated message, and
pushes the same `agent/` branch to `origin`. Push failures are recorded as
`COMMITTED` / `GIT_PUSH_FAILED`; there is no silent retry. A successful push
creates a local `PullRequestPreparation` (`base...head`, title, branches) for
human PR creation and review. The base branch SHA is checked before and after
the operation; any concurrent base change stops PR preparation and is recorded.

When such a candidate exists, M25's normal **Continue autonomously** path
prioritizes this completion over another experiment. It therefore performs the
fixed commit/push/PR-preparation flow without asking the browser for Git data.

## Validation-only flow

The Dashboard **Validate Git completion** action creates an isolated local
repository and local bare remote under Control Center state. It proves commit,
agent-branch push, base-branch preservation, audit events, and PR preparation
without reading, modifying, pushing, or merging any configured project. It is
not a GitHub PR and does not use credentials or network access.
