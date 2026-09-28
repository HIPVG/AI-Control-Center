"""Fail closed before publishing a GitHub-file reviewer trigger."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.control.reviewer_files import FileReplyError, validate_trigger_binding


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("request", type=Path)
    parser.add_argument("trigger", type=Path)
    args = parser.parse_args()
    try:
        binding = validate_trigger_binding(
            args.request.read_text(encoding="utf-8"),
            args.trigger.read_text(encoding="utf-8"),
        )
    except (FileReplyError, OSError) as exc:
        print(f"INVALID: {exc}")
        return 1
    print(f"VALID: {binding['REPORT_ID']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
