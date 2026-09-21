from pydantic import BaseModel, Field

from backend.models.task import WorkOrder


class TaskContext(BaseModel):
    task_id: str
    goal: str
    acceptance_tests: list[str]
    allowed_files: list[str]
    error_excerpt: str | None
    relevant_diff: str | None
    configuration: dict[str, str]
    retry_number: int
    context_files: dict[str, str] = Field(default_factory=dict)
    context_character_count: int = 0


class ContextBroker:
    """Creates intentionally bounded, task-specific context packages."""

    def build(
        self,
        work_order: WorkOrder,
        *,
        error_excerpt: str | None = None,
        relevant_diff: str | None = None,
        configuration: dict[str, str] | None = None,
        retry_number: int = 0,
        context_files: dict[str, str] | None = None,
    ) -> TaskContext:
        return TaskContext(
            task_id=work_order.task_id,
            goal=work_order.goal,
            acceptance_tests=work_order.acceptance_tests,
            allowed_files=work_order.allowed_files,
            error_excerpt=(error_excerpt or "")[:2000] or None,
            relevant_diff=(relevant_diff or "")[:4000] or None,
            configuration=configuration or {},
            retry_number=retry_number,
            context_files=context_files or {},
            context_character_count=sum(len(value) for value in (context_files or {}).values()),
        )
