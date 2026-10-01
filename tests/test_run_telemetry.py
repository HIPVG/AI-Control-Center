from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from backend.control.run_telemetry_store import JsonRunTelemetryStore
from backend.models.local_llm_day import (
    RunIntervention,
    RunInterventionType,
    RunTelemetry,
    TelemetryMetric,
)


NOW = datetime(2026, 9, 29, tzinfo=timezone.utc)


def known(value, unit, source):
    return TelemetryMetric(value=value, unit=unit, source=source, observed_at=NOW)


def unknown(unit, reason):
    return TelemetryMetric(value=None, unit=unit, source=None, observed_at=NOW,
                           unknown_reason=reason)


def telemetry(**changes):
    values = dict(
        run_id="run-001",
        manual_relay_count=known(1, "count", "review registry"),
        interventions=(RunIntervention(
            intervention_id="I-001", run_id="run-001",
            intervention_type=RunInterventionType.MANUAL_RELAY,
            reason="Reviewer transport was unavailable", actor="広瀬剛",
            source="recorded direct conversation", occurred_at=NOW,
        ),),
        attempt_count=known(2, "attempts", "repair episode"),
        attempt_limit=known(3, "attempts", "RunIntent requested limits"),
        input_tokens=unknown("tokens", "provider did not expose usage"),
        output_tokens=unknown("tokens", "provider did not expose usage"),
        cost=known(0.0, "JPY", "human-authorized zero-cost fixture"),
        captured_at=NOW,
    )
    values.update(changes)
    return RunTelemetry(**values)


def test_json_round_trip_and_create_only_store_preserve_one_run(tmp_path):
    original = telemetry()
    restored = RunTelemetry.model_validate_json(original.model_dump_json())
    assert restored == original
    assert restored.schema_version == 1
    assert restored.cached_input_tokens is None
    assert restored.uncached_input_tokens is None
    assert restored.budget_decision is None
    assert restored.attempt_count.value == 2
    assert restored.attempt_limit.value == 3
    assert restored.attempt_count.source != restored.attempt_limit.source

    store = JsonRunTelemetryStore(tmp_path)
    store.create(original)
    assert store.get("run-001") == original
    with pytest.raises(FileExistsError):
        store.create(original)


def test_unknown_tokens_remain_unknown_and_are_not_inferred_as_zero():
    result = telemetry()
    assert result.input_tokens.value is None
    assert result.output_tokens.value is None
    assert result.input_tokens.unknown_reason == "provider did not expose usage"
    payload = result.model_dump(mode="json")
    assert payload["input_tokens"]["value"] is None
    assert payload["output_tokens"]["value"] is None


def test_reasonless_intervention_is_rejected():
    with pytest.raises(ValidationError, match="reason"):
        RunIntervention(intervention_id="I-002", run_id="run-001",
                        intervention_type=RunInterventionType.HUMAN_INTERVENTION,
                        reason="", actor="広瀬剛", source="conversation", occurred_at=NOW)


def test_intervention_from_another_run_is_rejected():
    mixed = RunIntervention(intervention_id="I-002", run_id="run-other",
                            intervention_type=RunInterventionType.HUMAN_INTERVENTION,
                            reason="Authority required", actor="広瀬剛",
                            source="conversation", occurred_at=NOW)
    with pytest.raises(ValidationError, match="run ID mismatch"):
        telemetry(interventions=(mixed,), manual_relay_count=known(0, "count", "review registry"))


def test_manual_relay_count_must_match_reasoned_intervention_records():
    with pytest.raises(ValidationError, match="Manual relay count"):
        telemetry(manual_relay_count=known(0, "count", "review registry"))


def test_duplicate_intervention_id_in_the_same_run_is_rejected():
    intervention = telemetry().interventions[0]
    with pytest.raises(ValidationError, match="Duplicate telemetry intervention ID"):
        telemetry(interventions=(intervention, intervention),
                  manual_relay_count=known(2, "count", "review registry"))


@pytest.mark.parametrize("metric", [
    dict(value=None, unit="tokens", source=None, observed_at=NOW),
    dict(value=7, unit="tokens", source=None, observed_at=NOW),
    dict(value=7, unit="tokens", source="provider", observed_at=NOW,
         unknown_reason="should not coexist"),
])
def test_known_and_unknown_metrics_require_consistent_provenance(metric):
    with pytest.raises(ValidationError):
        TelemetryMetric(**metric)


def test_attempt_limit_and_actual_are_separate_and_over_limit_is_preserved_as_evidence():
    result = telemetry(attempt_count=known(4, "attempts", "repair episode"),
                       attempt_limit=known(2, "attempts", "RunIntent requested limits"))
    assert result.attempt_count.value == 4
    assert result.attempt_limit.value == 2
    assert result.attempt_count.source == "repair episode"
    assert result.attempt_limit.source == "RunIntent requested limits"
