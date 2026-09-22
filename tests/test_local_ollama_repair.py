import json

from backend.control.local_ollama_repair import LocalOllamaRepairBuilder, RepairEdit, RepairProposal


class _Response:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


def test_local_ollama_builder_accepts_only_bounded_structured_edits():
    response = {"message": {"content": json.dumps({
        "diagnosis": "fix temporary output location",
        "edits": [{"path": "tests/test_sample.py", "find": "old", "replace": "new"}],
    })}}
    builder = LocalOllamaRepairBuilder(opener=lambda *_args, **_kwargs: _Response(response))
    proposal = builder.propose(failure_excerpt="PermissionError", files={"tests/test_sample.py": "old"}, timeout_seconds=10)
    assert proposal == RepairProposal("fix temporary output location", (RepairEdit("tests/test_sample.py", "old", "new"),))


def test_local_ollama_builder_warms_the_local_model_without_source_context():
    response = {"model": LocalOllamaRepairBuilder.MODEL, "response": "", "done": True}
    builder = LocalOllamaRepairBuilder(opener=lambda *_args, **_kwargs: _Response(response))
    assert builder.warm(timeout_seconds=1) is True
