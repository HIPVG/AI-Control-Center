"""Audited recovery of an explicitly selected report; run with the service stopped."""
import argparse
import json
import socket
from pathlib import Path

from backend.control.reviewer_bus import ReviewerBusWatcher


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-current", required=True)
    parser.add_argument("--target-report-id", required=True)
    parser.add_argument("--target-comment-id", required=True, type=int)
    parser.add_argument("--authority", required=True)
    parser.add_argument("--continuation-scope", required=True)
    args = parser.parse_args()
    with socket.socket() as probe:
        probe.settimeout(2)
        if probe.connect_ex(("127.0.0.1", 8000)) == 0:
            parser.error("Stop the Control Center service before recovery.")
    watcher = ReviewerBusWatcher(Path(__file__).resolve().parents[1])
    comments, error = watcher._fetch_comments()
    if error:
        parser.error(error)
    watcher.recover_outstanding_report(comments, expected_current=args.expected_current,
        target_report_id=args.target_report_id, target_comment_id=args.target_comment_id,
        authority=args.authority, continuation_scope=args.continuation_scope)
    print(json.dumps(watcher.status()["last_binding_recovery"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
