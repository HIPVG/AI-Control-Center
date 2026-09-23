"""Git observations and non-destructive Day 1 checkpoint construction."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
from uuid import uuid4


class GitSafetyError(RuntimeError):
    pass


def git(root: Path, *args: str, env=None, input=None) -> bytes:
    result = subprocess.run(["git", "-C", str(root), "-c", f"safe.directory={root}", *args],
                            input=input, env=env, capture_output=True, timeout=60)
    if result.returncode:
        raise GitSafetyError(f"git {args[0]} failed: {result.stderr.decode('utf-8', 'replace')[:500]}")
    return result.stdout


def generated(path: str) -> bool:
    normalized = path.replace("\\", "/")
    if normalized.startswith("state/"):
        return normalized != "state/.gitkeep"
    if normalized.split("/", 1)[0] in {".pytest-debug", ".pytest-debug2"}:
        return True
    if normalized == "day1-failfast-output.txt":
        return True
    parts = Path(normalized).parts
    blocked = {"results", "artifacts", "models", "datasets", "teacher", "telemetry", "logs", "cache", "__pycache__", ".pytest_cache", ".git"}
    return any(part.lower() in blocked for part in parts) or Path(path).suffix.lower() in {".pyc", ".zip", ".gguf", ".safetensors"}


def approved(path: str) -> bool:
    normalized = path.replace("\\", "/")
    if generated(normalized) or any(s in normalized.lower() for s in (".env", "credential", "secret", "private_key")):
        return False
    return (normalized.startswith(("src/", "backend/", "scripts/", "tests/", "config/", "docs/", "schemas/"))
            and Path(path).suffix.lower() in {".py", ".json", ".yaml", ".yml", ".md", ".toml", ".txt"}
            or normalized in {".gitignore", "README.md", "requirements.txt", "pyproject.toml", "pytest.ini"})


def files(root: Path) -> list[str]:
    return sorted(set(git(root, "ls-files", "-z", "--cached", "--others", "--exclude-standard").decode("utf-8").strip("\0").split("\0")) - {""})


def fingerprint(root: Path) -> str:
    values = []
    for relative in files(root):
        if not approved(relative):
            continue
        path = root / relative
        if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
            raise GitSafetyError("SOURCE_PATH_ESCAPE")
        values.append((relative, hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else "DELETED"))
    head = git(root, "rev-parse", "HEAD").decode().strip()
    return hashlib.sha256(json.dumps([head, values], sort_keys=True).encode()).hexdigest()


def checkpoint(root: Path) -> dict:
    head = git(root, "rev-parse", "HEAD").decode().strip()
    branch = git(root, "symbolic-ref", "HEAD").decode().strip()
    status = git(root, "status", "--porcelain=v1", "-z", "-uall")
    index = Path(git(root, "rev-parse", "--git-path", "index").decode().strip())
    if not index.is_absolute():
        index = root / index
    original_index = index.read_bytes() if index.exists() else None
    all_paths = files(root)
    changes = set(git(root, "diff", "HEAD", "--name-only", "-z").decode().strip("\0").split("\0")) - {""}
    changes.update(git(root, "ls-files", "--others", "--exclude-standard", "-z").decode().strip("\0").split("\0"))
    unsafe = sorted(path for path in changes if path and not approved(path) and not generated(path))
    if unsafe:
        return {"authority_required": "UNAPPROVED_SOURCE_PATHS", "paths": unsafe}
    before = fingerprint(root)
    temporary_index = index.parent / f"acc-day1-{uuid4().hex}.index"
    env = {**os.environ, "GIT_INDEX_FILE": str(temporary_index), "GIT_OPTIONAL_LOCKS": "0"}
    try:
        git(root, "read-tree", "HEAD", env=env)
        # Remove protected generated material from the *temporary* snapshot,
        # including material already tracked in HEAD. Never touch user index.
        protected = [path for path in all_paths if generated(path)]
        for path in protected:
            git(root, "update-index", "--force-remove", "--", path, env=env)
        selected = [path for path in all_paths if approved(path)]
        if selected:
            git(root, "add", "-A", "--", *selected, env=env)
        tree = git(root, "write-tree", env=env).decode().strip()
        # Independent comparison uses Git's filters/line-ending semantics,
        # checks deleted and untracked source, and rejects generated entries.
        staged = git(root, "ls-files", "-z", env=env).decode().strip("\0").split("\0")
        if any(generated(path) for path in staged):
            raise GitSafetyError("GENERATED_CHECKPOINT_ENTRY")
        for path in selected:
            target = root / path
            listing = git(root, "ls-files", "--stage", "--", path, env=env).decode().strip()
            if target.is_file():
                expected = git(root, "hash-object", f"--path={path}", "--", path).decode().strip()
                if not listing or listing.split()[1] != expected:
                    raise GitSafetyError("CHECKPOINT_SOURCE_MISMATCH")
            elif listing:
                raise GitSafetyError("CHECKPOINT_DELETION_MISMATCH")
        if fingerprint(root) != before:
            raise GitSafetyError("SOURCE_CHANGED_DURING_CHECKPOINT")
        commit = git(root, "commit-tree", tree, "-p", head, "-m", "Day 1 baseline checkpoint", env=env).decode().strip()
        ref = f"refs/heads/ai-control-center/day1-baseline-{commit[:16]}"
        git(root, "update-ref", ref, commit, "0" * len(commit))
        if git(root, "rev-parse", f"{ref}^{{tree}}").decode().strip() != tree:
            raise GitSafetyError("CHECKPOINT_REF_MISMATCH")
        return {"branch": ref, "head": commit, "is_commit": True, "checkpoint_ref": ref,
                "parent_head": head, "tree": tree, "source_fingerprint": before,
                "approved_paths": selected, "generated_paths_excluded": True}
    finally:
        temporary_index.unlink(missing_ok=True)
        if (git(root, "rev-parse", "HEAD").decode().strip() != head
                or git(root, "symbolic-ref", "HEAD").decode().strip() != branch
                or (index.read_bytes() if index.exists() else None) != original_index
                or git(root, "status", "--porcelain=v1", "-z", "-uall") != status):
            raise GitSafetyError("USER_GIT_STATE_CHANGED")
