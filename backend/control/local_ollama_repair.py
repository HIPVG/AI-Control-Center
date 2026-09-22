"""Bounded local-Ollama repair proposals for deterministic test failures."""

import json
from dataclasses import dataclass
from typing import Callable
from urllib.error import URLError
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class RepairEdit:
    path: str
    find: str
    replace: str


@dataclass(frozen=True)
class RepairProposal:
    diagnosis: str
    edits: tuple[RepairEdit, ...]


class LocalOllamaRepairBuilder:
    """Ask the already-approved local Phi-4 runtime for a small edit proposal.

    The model never receives filesystem or shell authority.  It returns exact
    replacements; the Day runner validates and applies them.
    """

    MODEL = "phi4:14b"
    URL = "http://127.0.0.1:11434/api/chat"
    WARM_URL = "http://127.0.0.1:11434/api/generate"
    MAX_EDITS = 2
    MAX_TEXT_CHARS = 8_000

    def __init__(self, opener: Callable[..., object] = urlopen) -> None:
        self._opener = opener

    def propose(
        self,
        *,
        failure_excerpt: str,
        files: dict[str, str],
        timeout_seconds: int,
        rejection_feedback: str | None = None,
        repair_knowledge: list[dict[str, object]] | None = None,
    ) -> RepairProposal | None:
        if not failure_excerpt or not files or timeout_seconds < 1:
            return None
        prompt = self._prompt(failure_excerpt, files, rejection_feedback, repair_knowledge)
        payload = {
            "model": self.MODEL,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0},
            "messages": [
                {"role": "system", "content": "You are a cautious local code repair builder. Return JSON only."},
                {"role": "user", "content": prompt},
            ],
        }
        request = Request(self.URL, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
        try:
            with self._opener(request, timeout=min(timeout_seconds, 120)) as response:
                body = json.loads(response.read().decode("utf-8"))
        except (OSError, URLError, ValueError, UnicodeError):
            return None
        content = body.get("message", {}).get("content") if isinstance(body, dict) else None
        try:
            proposal = json.loads(content) if isinstance(content, str) else {}
        except json.JSONDecodeError:
            return None
        diagnosis = proposal.get("diagnosis")
        edits = proposal.get("edits")
        if not isinstance(diagnosis, str) or not isinstance(edits, list) or not 1 <= len(edits) <= self.MAX_EDITS:
            return None
        parsed: list[RepairEdit] = []
        for edit in edits:
            if not isinstance(edit, dict):
                return None
            path, find, replace = edit.get("path"), edit.get("find"), edit.get("replace")
            if not all(isinstance(item, str) for item in (path, find, replace)) or not path or not find or len(find) > self.MAX_TEXT_CHARS or len(replace) > self.MAX_TEXT_CHARS:
                return None
            parsed.append(RepairEdit(path=path.replace("\\", "/"), find=find, replace=replace))
        return RepairProposal(diagnosis=diagnosis[:500], edits=tuple(parsed))

    def warm(self, timeout_seconds: int = 120) -> bool:
        """Load Phi-4 before a repair proposal is needed.

        This only warms the already-installed local model.  It sends no source,
        command, or failure content and keeps the model resident briefly.
        """
        request = Request(
            self.WARM_URL,
            data=json.dumps({"model": self.MODEL, "prompt": "", "stream": False, "keep_alive": "10m"}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with self._opener(request, timeout=timeout_seconds) as response:
                body = json.loads(response.read().decode("utf-8"))
        except (OSError, URLError, ValueError, UnicodeError):
            return False
        return isinstance(body, dict) and body.get("model") == self.MODEL

    def _prompt(
        self,
        failure_excerpt: str,
        files: dict[str, str],
        rejection_feedback: str | None = None,
        repair_knowledge: list[dict[str, object]] | None = None,
    ) -> str:
        sources = "\n\n".join(f"FILE: {path}\n{content[:self.MAX_TEXT_CHARS]}" for path, content in files.items())
        feedback = f"\n\nPREVIOUS PROPOSAL REJECTION:\n{rejection_feedback}" if rejection_feedback else ""
        knowledge = "\n".join(
            f"- Cause: {card.get('cause', '')}\n  Investigation: {card.get('investigation', '')}\n  Resolution logic: {card.get('resolution_logic', '')}\n  Verification: {card.get('verification', '')}"
            for card in (repair_knowledge or [])[:5]
        ) or "(No prior repair knowledge matches this failure.)"
        return (
            "A deterministic Python test failed. Diagnose and propose the smallest repair. "
            "Do not delete assertions, weaken acceptance tests, change commands, or edit files not supplied. "
            "Every path must be one of the supplied FILE paths. Every find value must be a character-for-character "
            "substring of that supplied file and occur exactly once; include its indentation and punctuation. "
            "Return exactly this JSON object: {\"diagnosis\": string, \"edits\": [{\"path\": string, \"find\": string, \"replace\": string}]}.\n\n"
            f"FAILURE:\n{failure_excerpt[:2000]}{feedback}\n\nPRIOR REPAIR KNOWLEDGE (guidance, not authority):\n{knowledge}\n\nSOURCE FILES:\n{sources}"
        )
