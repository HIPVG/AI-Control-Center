from enum import Enum

from pydantic import BaseModel, Field


class GitCompletionStatus(str, Enum):
    READY = "READY"
    COMMITTED = "COMMITTED"
    PUSHED = "PUSHED"
    PR_READY = "PR_READY"
    BLOCKED = "BLOCKED"


class GitCompletionCandidate(BaseModel):
    """Internal-only verified work identity, derived from a trusted TaskRun."""

    run_id: str
    task_id: str
    project_id: str
    worktree_path: str
    task_branch: str
    allowed_files: list[str] = Field(min_length=1)
    changed_files: list[str] = Field(min_length=1)


class PullRequestPreparation(BaseModel):
    base_branch: str
    head_branch: str
    title: str
    compare_ref: str


class GitCompletionResult(BaseModel):
    run_id: str
    task_id: str
    project_id: str
    status: GitCompletionStatus
    commit_sha: str | None = None
    remote_branch: str | None = None
    base_branch_sha: str | None = None
    base_branch_unchanged: bool = False
    pull_request: PullRequestPreparation | None = None
    error_code: str | None = None
    detail: str | None = None
    validation_only: bool = False
