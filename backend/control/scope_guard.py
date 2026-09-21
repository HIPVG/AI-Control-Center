from pydantic import BaseModel

from backend.models.task import WorkOrder


class ScopeCheck(BaseModel):
    allowed: bool
    out_of_scope: list[str] = []


class ScopeGuard:
    def check(self, work_order: WorkOrder, changed_files: list[str]) -> ScopeCheck:
        allowed = set(work_order.allowed_files)
        normalized = [item.replace("\\", "/").lstrip("./") for item in changed_files]
        out_of_scope = sorted(set(normalized) - allowed)
        return ScopeCheck(allowed=not out_of_scope, out_of_scope=out_of_scope)
