import inspect
import re

from backend.models.audit import AuditEvent, AuditEventType
from backend.orchestrator.day_runner import DayRunner


def test_model_router_and_deterministic_day_events_are_first_class_enum_members():
    assert AuditEventType("DAY_MODEL_ROUTING") is AuditEventType.DAY_MODEL_ROUTING
    assert AuditEventType("DAY_DETERMINISTIC_NO_AI") is AuditEventType.DAY_DETERMINISTIC_NO_AI


def test_every_static_day_runner_audit_event_is_registered():
    source = inspect.getsource(DayRunner)
    produced = set(re.findall(r'self\._audit\([^,]+,\s*"(DAY_[A-Z_]+)"', source))
    registered = {event.value for event in AuditEventType}
    assert produced == {
        "DAY_PLAN_STARTED",
        "DAY_ARCHITECT_DECISION",
        "DAY_MODEL_ROUTING",
        "DAY_DETERMINISTIC_NO_AI",
        "DAY_TASK_RESULT",
        "DAY_EVALUATION_RESULT",
        "DAY_HUMAN_REVIEW",
        "DAY_STOPPED",
        "DAY_COMPLETE",
    }
    assert produced <= registered


def test_new_day_audit_events_remain_serializable():
    event = AuditEvent(task_id="PC-001-A", event_type=AuditEventType.DAY_MODEL_ROUTING, message="routing selected")
    assert event.model_dump(mode="json")["event_type"] == "DAY_MODEL_ROUTING"
