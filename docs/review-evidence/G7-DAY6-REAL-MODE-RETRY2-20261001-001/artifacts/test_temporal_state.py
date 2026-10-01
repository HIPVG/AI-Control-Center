import copy
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from eval.temporal_state import TIME_PARTITIONS, load_schema, validate_temporal_state


def state():
    result = {}
    for partition in TIME_PARTITIONS:
        result[partition] = {"as_of": "2026-10-01T09:00:00+00:00", "facts": []}
    result["planned_time"]["facts"] = [{"fact_id": "FACT-PRODUCTION-COMPLETE", "value": "planned", "unit": "status", "source_record_ids": ["PLAN-1"]}]
    result["actual_time"]["facts"] = [{"fact_id": "FACT-PRODUCTION-COMPLETE", "value": "in_progress", "unit": "status", "source_record_ids": ["MES-1"]}]
    result["forecast_time"]["facts"] = [{"fact_id": "FACT-PRODUCTION-COMPLETE", "value": "at_risk", "unit": "status", "source_record_ids": ["FORECAST-1"]}]
    return result


class TemporalStateTests(unittest.TestCase):
    def test_schema_separates_all_four_time_partitions(self):
        schema = load_schema()
        self.assertEqual(set(schema["required"]), set(TIME_PARTITIONS))
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(json.loads((ROOT / "schemas" / "temporal-state.json").read_text(encoding="utf-8")), schema)

    def test_valid_temporal_state_keeps_same_fact_separate_by_time(self):
        report = validate_temporal_state(state(), {"FACT-PRODUCTION-COMPLETE": "actual_time"})
        self.assertEqual(report["validation_status"], "SUCCESS")
        self.assertEqual(report["errors"], [])

    def test_missing_required_actual_fact_fails_closed(self):
        value = state()
        value["actual_time"]["facts"] = []
        report = validate_temporal_state(value, {"FACT-PRODUCTION-COMPLETE": "actual_time"})
        self.assertEqual(report["validation_status"], "FAILED")
        self.assertIn({"code": "MISSING_REQUIRED_FACT", "partition": "actual_time"}, report["errors"])

    def test_plan_does_not_satisfy_required_actual_fact(self):
        value = state()
        value["actual_time"]["facts"] = []
        self.assertEqual(validate_temporal_state(value, {"FACT-PRODUCTION-COMPLETE": "actual_time"})["validation_status"], "FAILED")

    def test_unknown_partition_and_unprovenanced_fact_fail_closed(self):
        value = copy.deepcopy(state())
        value["unexpected_time"] = value.pop("snapshot_time")
        value["actual_time"]["facts"][0]["source_record_ids"] = []
        report = validate_temporal_state(value)
        self.assertEqual(report["validation_status"], "FAILED")
        self.assertIn({"code": "TEMPORAL_PARTITIONS_INVALID"}, report["errors"])
        self.assertIn({"code": "MISSING_PROVENANCE", "partition": "actual_time"}, report["errors"])

    def test_timezone_less_snapshot_is_rejected(self):
        value = state()
        value["snapshot_time"]["as_of"] = "2026-10-01T09:00:00"
        self.assertIn({"code": "INVALID_AS_OF", "partition": "snapshot_time"},
                      validate_temporal_state(value)["errors"])


if __name__ == "__main__":
    unittest.main()
