import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from eval.temporal_state import is_valid_temporal_state, validate_temporal_state


def state():
    return {
        "snapshot_time": "2026-10-01T09:00:00+09:00",
        "planned": [{"fact_id": "production_completion", "value": "complete",
                     "effective_time": "2026-10-02T17:00:00+09:00", "source_record_ids": ["plan-1"]}],
        "actual": [{"fact_id": "material_on_hand", "value": 20,
                    "effective_time": "2026-10-01T08:00:00+09:00", "source_record_ids": ["inventory-1"]}],
        "forecast": [{"fact_id": "material_receipt", "value": 100,
                      "effective_time": "2026-10-03T12:00:00+09:00", "source_record_ids": ["po-1"]}],
    }


class TemporalStateTests(unittest.TestCase):
    def test_01_complete_separated_state_is_valid(self):
        self.assertTrue(is_valid_temporal_state(state()))

    def test_02_missing_time_bucket_fails_closed(self):
        value = state(); del value["forecast"]
        self.assertIn("INVALID_TOP_LEVEL_FIELDS", {row["code"] for row in validate_temporal_state(value)})

    def test_03_actual_cannot_be_after_snapshot(self):
        value = state(); value["actual"][0]["effective_time"] = "2026-10-01T10:00:00+09:00"
        self.assertIn("ACTUAL_AFTER_SNAPSHOT", {row["code"] for row in validate_temporal_state(value)})

    def test_04_fact_requires_provenance(self):
        value = state(); value["forecast"][0]["source_record_ids"] = []
        self.assertIn("INVALID_SOURCE_RECORD_IDS", {row["code"] for row in validate_temporal_state(value)})


if __name__ == "__main__":
    unittest.main()
