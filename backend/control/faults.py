import ast
from pathlib import Path

from pydantic import BaseModel, Field, field_validator

from backend.control.tasks import TaskCommand, _safe_relative_paths


class FaultProfile(BaseModel):
    """Trusted, worktree-only mutation used to validate one repair workflow."""

    fault_id: str = Field(min_length=1, max_length=120)
    project_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1, max_length=120)
    base_case: str = Field(min_length=1)
    title: str = Field(min_length=1, max_length=300)
    working_directory: str = "."
    target_file: str
    fault_type: str = Field(min_length=1, max_length=300)
    fault_description: str = Field(min_length=1, max_length=1000)
    baseline: TaskCommand
    postcheck: TaskCommand
    allowed_files: list[str] = Field(min_length=1)
    context_files: list[str] = Field(min_length=1)
    max_retry: int = Field(default=1, ge=0, le=20)
    context_max_characters: int = Field(default=30000, ge=1, le=100000)
    expected_precheck_exit_code: int = 1
    expected_precheck_text: str = Field(min_length=1, max_length=200)

    @field_validator("working_directory", "target_file")
    @classmethod
    def safe_path(cls, value: str) -> str:
        return _safe_relative_paths([value])[0]

    @field_validator("allowed_files", "context_files")
    @classmethod
    def safe_paths(cls, value: list[str]) -> list[str]:
        return _safe_relative_paths(value)

    def validate_scope(self) -> None:
        if self.target_file != "scripts/process_consistency.py":
            raise ValueError("controlled fault target must be scripts/process_consistency.py")
        if self.allowed_files != [self.target_file]:
            raise ValueError("controlled fault repair must allow exactly its target file")
        if self.context_files != [self.target_file]:
            raise ValueError("controlled fault repair must include only its target file")


class FaultRegistry(BaseModel):
    faults: dict[str, FaultProfile] = Field(default_factory=dict)

    def get(self, fault_id: str) -> FaultProfile | None:
        return self.faults.get(fault_id)


def load_fault_registry(path: Path) -> FaultRegistry:
    if not path.exists():
        return FaultRegistry()
    import yaml

    registry = FaultRegistry.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")) or {})
    for profile in registry.faults.values():
        profile.validate_scope()
    return registry


def locate_qa_shipment_gt_operator(source: bytes) -> int | None:
    """Return the unique byte offset of `difference > 0`, or reject ambiguity."""
    try:
        text = source.decode("utf-8")
        tree = ast.parse(text)
    except (SyntaxError, UnicodeError):
        return None
    evaluate_functions = [node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "evaluate"]
    if len(evaluate_functions) != 1:
        return None
    qa_branches = [node for node in ast.walk(evaluate_functions[0]) if isinstance(node, ast.If) and _is_qa_shipment_branch(node.test)]
    if len(qa_branches) != 1:
        return None
    assignments = [
        node for statement in qa_branches[0].body for node in ast.walk(statement)
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) and node.targets[0].id == "anomalous"
    ]
    if len(assignments) != 1 or not _is_difference_gt_zero(assignments[0].value):
        return None
    comparison = assignments[0].value
    start = _byte_offset(source, comparison.lineno, comparison.col_offset)
    end = _byte_offset(source, comparison.end_lineno, comparison.end_col_offset)
    segment = source[start:end]
    if segment.count(b">") != 1 or b">=" in segment:
        return None
    return start + segment.index(b">")


def _is_qa_shipment_branch(node: ast.expr) -> bool:
    return (
        isinstance(node, ast.Compare)
        and isinstance(node.left, ast.Name) and node.left.id == "kind"
        and len(node.ops) == len(node.comparators) == 1
        and isinstance(node.ops[0], ast.Eq)
        and isinstance(node.comparators[0], ast.Constant)
        and node.comparators[0].value == "qa_shipment_quantity"
    )


def _is_difference_gt_zero(node: ast.expr) -> bool:
    return (
        isinstance(node, ast.Compare)
        and isinstance(node.left, ast.Name) and node.left.id == "difference"
        and len(node.ops) == len(node.comparators) == 1
        and isinstance(node.ops[0], ast.Gt)
        and isinstance(node.comparators[0], ast.Constant)
        and isinstance(node.comparators[0].value, (int, float, complex))
        and not isinstance(node.comparators[0].value, bool)
        and node.comparators[0].value == 0
    )


def _byte_offset(source: bytes, line: int, column: int) -> int:
    lines = source.splitlines(keepends=True)
    if line < 1 or line > len(lines):
        raise ValueError("AST source location is outside the source file")
    return sum(len(item) for item in lines[: line - 1]) + column
