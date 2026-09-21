"""Deterministic, agent-branch-only Git completion for verified work."""

import subprocess
from pathlib import Path

from backend.control.git_guard import GitGuard
from backend.models.git_completion import (
    GitCompletionCandidate, GitCompletionResult, GitCompletionStatus, PullRequestPreparation,
)


class GitCompletionService:
    """Commit and push only an internally-derived verified worktree candidate."""

    def candidate_from_task_run(self, item: dict) -> GitCompletionCandidate | None:
        if not (
            item.get("state") == "COMPLETE"
            and item.get("final_result") == "COMPLETE"
            and item.get("postcheck_result") == "PASS"
            and item.get("scope_guard_result") == "PASS"
            and item.get("worktree_path")
            and item.get("task_branch")
            and item.get("changed_files")
            and item.get("allowed_files")
        ):
            return None
        branch = str(item["task_branch"])
        if not self._agent_branch(branch):
            return None
        return GitCompletionCandidate(
            run_id=str(item["run_id"]), task_id=str(item["task_id"]), project_id=str(item["project_id"]),
            worktree_path=str(item["worktree_path"]), task_branch=branch,
            allowed_files=list(item["allowed_files"]), changed_files=sorted(set(item["changed_files"])),
        )

    def complete(self, candidate: GitCompletionCandidate, *, base_branch: str, validation_only: bool = False) -> GitCompletionResult:
        root = Path(candidate.worktree_path).resolve()
        blocked = self._validate_candidate(root, candidate, base_branch)
        if blocked:
            return self._blocked(candidate, blocked, validation_only)
        _, base_before, _ = self._run(root, ["rev-parse", base_branch])
        if any(self._run(root, ["config", "--get", key])[0] != 0 for key in ("user.name", "user.email")):
            return self._blocked(candidate, "GIT_COMMIT_IDENTITY_UNAVAILABLE", validation_only)
        if self._run(root, ["diff", "--check"])[0] != 0:
            return self._blocked(candidate, "GIT_DIFF_CHECK_FAILED", validation_only)
        if self._run(root, ["add", "--", *candidate.changed_files])[0] != 0:
            return self._blocked(candidate, "GIT_STAGE_FAILED", validation_only)
        staged, _, _ = self._run(root, ["diff", "--cached", "--quiet"])
        if staged == 0:
            return self._blocked(candidate, "GIT_NO_STAGED_CHANGES", validation_only)
        if staged not in {0, 1}:
            return self._blocked(candidate, "GIT_STAGED_DIFF_UNAVAILABLE", validation_only)
        message = f"fix: verified {candidate.task_id} completion"
        committed, _, _ = self._run(root, ["commit", "-m", message])
        if committed != 0:
            return self._blocked(candidate, "GIT_COMMIT_FAILED", validation_only)
        sha_code, sha, _ = self._run(root, ["rev-parse", "HEAD"])
        if sha_code != 0 or not sha:
            return self._blocked(candidate, "GIT_HEAD_UNAVAILABLE", validation_only)
        if not GitGuard().check(f"git push origin {candidate.task_branch}").allowed:
            return self._blocked(candidate, "GIT_PUSH_POLICY_BLOCKED", validation_only)
        pushed, _, _ = self._run(root, ["push", "-u", "origin", candidate.task_branch])
        if pushed != 0:
            return GitCompletionResult(
                run_id=candidate.run_id, task_id=candidate.task_id, project_id=candidate.project_id,
                status=GitCompletionStatus.COMMITTED, commit_sha=sha, error_code="GIT_PUSH_FAILED",
                base_branch_sha=base_before, validation_only=validation_only,
            )
        _, base_after, _ = self._run(root, ["rev-parse", base_branch])
        if not base_after or base_after != base_before:
            return GitCompletionResult(
                run_id=candidate.run_id, task_id=candidate.task_id, project_id=candidate.project_id,
                status=GitCompletionStatus.PUSHED, commit_sha=sha, remote_branch=candidate.task_branch,
                base_branch_sha=base_before, error_code="GIT_BASE_BRANCH_CHANGED", validation_only=validation_only,
            )
        preparation = PullRequestPreparation(
            base_branch=base_branch, head_branch=candidate.task_branch,
            title=f"Verified completion: {candidate.task_id}",
            compare_ref=f"{base_branch}...{candidate.task_branch}",
        )
        return GitCompletionResult(
            run_id=candidate.run_id, task_id=candidate.task_id, project_id=candidate.project_id,
            status=GitCompletionStatus.PR_READY, commit_sha=sha, remote_branch=candidate.task_branch,
            base_branch_sha=base_before, base_branch_unchanged=True, pull_request=preparation, validation_only=validation_only,
        )

    def _validate_candidate(self, root: Path, candidate: GitCompletionCandidate, base_branch: str) -> str | None:
        if not root.is_dir() or not self._agent_branch(candidate.task_branch) or not base_branch or candidate.task_branch == base_branch:
            return "GIT_CANDIDATE_INVALID"
        branch_code, branch, _ = self._run(root, ["branch", "--show-current"])
        if branch_code != 0 or branch != candidate.task_branch:
            return "GIT_BRANCH_MISMATCH"
        base_code, _, _ = self._run(root, ["rev-parse", "--verify", base_branch])
        if base_code != 0:
            return "GIT_BASE_BRANCH_UNAVAILABLE"
        remote_code, _, _ = self._run(root, ["remote", "get-url", "origin"])
        if remote_code != 0:
            return "GIT_ORIGIN_UNAVAILABLE"
        actual = self._changed_files(root)
        if actual is None:
            return "GIT_STATUS_UNAVAILABLE"
        expected = sorted(set(candidate.changed_files))
        if actual != expected or not set(expected).issubset(candidate.allowed_files):
            return "GIT_VERIFIED_SCOPE_MISMATCH"
        return None

    def _changed_files(self, root: Path) -> list[str] | None:
        tracked_code, tracked, _ = self._run(root, ["diff", "--name-only", "--no-renames", "HEAD"])
        untracked_code, untracked, _ = self._run(root, ["ls-files", "--others", "--exclude-standard"])
        if tracked_code != 0 or untracked_code != 0:
            return None
        return sorted({line.replace("\\", "/") for line in (tracked.splitlines() + untracked.splitlines()) if line})

    @staticmethod
    def _agent_branch(branch: str) -> bool:
        return branch.startswith("agent/") and branch != "agent/main" and ".." not in branch and not branch.endswith("/")

    @staticmethod
    def _blocked(candidate: GitCompletionCandidate, code: str, validation_only: bool) -> GitCompletionResult:
        return GitCompletionResult(run_id=candidate.run_id, task_id=candidate.task_id, project_id=candidate.project_id, status=GitCompletionStatus.BLOCKED, error_code=code, validation_only=validation_only)

    @staticmethod
    def _run(root: Path, arguments: list[str]) -> tuple[int, str, str]:
        try:
            completed = subprocess.run(
                ["git", "-C", str(root), "-c", f"safe.directory={root}", *arguments],
                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30, check=False, shell=False,
            )
        except (FileNotFoundError, OSError, subprocess.TimeoutExpired):
            return 127, "", ""
        return completed.returncode, completed.stdout.strip(), completed.stderr.strip()[:240]
