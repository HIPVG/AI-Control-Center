"""Repository-local, per-session temporary paths for pytest on Windows."""

import os
import tempfile
from pathlib import Path
from uuid import uuid4

import _pytest.tmpdir

_ORIGINAL_MAKE_NUMBERED_DIR = _pytest.tmpdir.make_numbered_dir


def pytest_configure(config):
    parent = Path(config.rootpath) / ".pytest-tmp"
    parent.mkdir(parents=True, exist_ok=True)
    session_root = parent / f"run-{os.getpid()}-{uuid4().hex[:8]}"
    session_root.mkdir()
    # A unique child avoids pytest trying to delete a prior sandbox session's
    # ACL-restricted directory. The repository-owned parent remains stable.
    # pytest normally recreates --basetemp with mode 0700. In this sandbox
    # that child can immediately become unreadable to the test process. Keep
    # the pre-created repository-owned session root as the factory base.
    _pytest.tmpdir.TempPathFactory.getbasetemp = lambda _factory: session_root
    _pytest.tmpdir.make_numbered_dir = lambda root, prefix, mode=0o700: _ORIGINAL_MAKE_NUMBERED_DIR(root, prefix, mode=0o777)
    config.option.basetemp = str(session_root)
    os.environ["TEMP"] = str(session_root)
    os.environ["TMP"] = str(session_root)
    tempfile.tempdir = str(session_root)
    # Each session has a unique ignored child, so do not scan or remove a
    # sandbox-created child after the run.
    _pytest.tmpdir.cleanup_dead_symlinks = lambda _path: None
