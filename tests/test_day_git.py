import subprocess
from pathlib import Path

from backend.control import day_git


def git(root: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(root), *arguments],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    return completed.stdout.strip()


def write(root: Path, relative: str, contents: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(contents, encoding="utf-8")


def repository(tmp_path: Path) -> Path:
    root = tmp_path / "repository"
    git(tmp_path, "init", "-b", "main", str(root))
    git(root, "config", "user.name", "Test")
    git(root, "config", "user.email", "test@example.invalid")
    write(root, "backend/source.py", "baseline = True\n")
    write(root, "state/.gitkeep", "")
    write(root, "state/tracked-runtime.log", "old runtime output\n")
    git(root, "add", "backend/source.py", "state/.gitkeep", "state/tracked-runtime.log")
    git(root, "commit", "-m", "baseline")
    return root


def test_generated_runtime_artifacts_are_narrowly_classified():
    for path in (
        "state/runtime.json",
        "state/runtime.xml",
        "state/runtime.log",
        ".pytest-debug/local-llm/output.log",
        ".pytest-debug2/local-llm/output.log",
        "day1-failfast-output.txt",
    ):
        assert day_git.generated(path)
    assert not day_git.generated("state/.gitkeep")
    assert not day_git.generated("unapproved-root.py")
    assert not day_git.generated("day1-other-output.txt")


def test_checkpoint_rejects_an_unapproved_non_generated_root_path(tmp_path):
    root = repository(tmp_path)
    write(root, "unapproved-root.py", "unsafe = True\n")

    assert day_git.checkpoint(root) == {
        "authority_required": "UNAPPROVED_SOURCE_PATHS",
        "paths": ["unapproved-root.py"],
    }


def test_checkpoint_excludes_generated_artifacts_without_changing_user_git_state(tmp_path):
    root = repository(tmp_path)
    write(root, "backend/source.py", "staged = True\n")
    git(root, "add", "backend/source.py")
    write(root, "backend/source.py", "worktree = True\n")
    write(root, "state/runtime.json", '{"runtime": true}\n')
    write(root, "state/runtime.xml", "<runtime/>\n")
    write(root, "state/runtime.log", "runtime output\n")
    write(root, ".pytest-debug/local-llm/debug.log", "debug\n")
    write(root, "day1-failfast-output.txt", "failfast output\n")
    status_before = git(root, "status", "--porcelain=v1", "-z")
    index_path = Path(git(root, "rev-parse", "--git-path", "index"))
    if not index_path.is_absolute():
        index_path = root / index_path
    index_before = index_path.read_bytes()

    result = day_git.checkpoint(root)

    assert result["is_commit"] is True
    assert result["generated_paths_excluded"] is True
    assert git(root, "status", "--porcelain=v1", "-z") == status_before
    assert index_path.read_bytes() == index_before
    assert (root / "backend/source.py").read_text(encoding="utf-8") == "worktree = True\n"
    tree_paths = git(root, "ls-tree", "-r", "--name-only", result["head"]).splitlines()
    assert "backend/source.py" in tree_paths
    assert "state/.gitkeep" in tree_paths
    assert "state/tracked-runtime.log" not in tree_paths
    assert not any(path.startswith("state/runtime") for path in tree_paths)
    assert not any(path.startswith(".pytest-debug/") for path in tree_paths)
    assert "day1-failfast-output.txt" not in tree_paths
