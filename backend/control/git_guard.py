from dataclasses import dataclass


@dataclass(frozen=True)
class GitCheck:
    allowed: bool
    reason: str | None = None


class GitGuard:
    """Policy-only guard; executing git commands remains a separate concern."""

    _FORBIDDEN = ("git reset --hard", "git clean -fd", "git branch -d")

    def check(self, command: str) -> GitCheck:
        normalized = " ".join(command.lower().split())
        if any(normalized.startswith(item) for item in self._FORBIDDEN):
            return GitCheck(False, "destructive git command is blocked")
        if normalized.startswith("git push") and (" main" in f" {normalized}" or " origin/main" in normalized):
            return GitCheck(False, "direct automated push to main is blocked")
        return GitCheck(True)
