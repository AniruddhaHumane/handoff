import unittest

from handoff.merge import merge_snapshots


class GetHandoffMergeTest(unittest.TestCase):
    def test_newest_snapshot_wins_primary_fields(self) -> None:
        older_snapshot = {
            "agent": "A",
            "timestamp": "2026-04-12T00:00:00Z",
            "summary": "old summary",
            "next_action": "old next",
        }
        newer_snapshot = {
            "agent": "B",
            "timestamp": "2026-04-12T01:00:00Z",
            "summary": "new summary",
            "next_action": "new next",
        }

        merged = merge_snapshots([older_snapshot, newer_snapshot])

        self.assertEqual(merged["primary_agent"], "B")
        self.assertEqual(merged["summary"], "new summary")
        self.assertIn("A", merged["sources"])
        self.assertIn("B", merged["sources"])

    def test_timestamp_ordering_handles_iso_variants_by_instant(self) -> None:
        older_snapshot = {
            "agent": "A",
            "timestamp": "2026-04-12T00:00:00Z",
            "summary": "old summary",
            "next_action": "old next",
        }
        newer_snapshot = {
            "agent": "B",
            "timestamp": "2026-04-12T00:00:00.500000+00:00",
            "summary": "new summary",
            "next_action": "new next",
        }

        merged = merge_snapshots([older_snapshot, newer_snapshot])

        self.assertEqual(merged["primary_agent"], "B")
        self.assertEqual(merged["summary"], "new summary")


if __name__ == "__main__":
    unittest.main()
