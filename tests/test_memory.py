import unittest

from handoff.memory import merge_project_memory


class MemoryMergeTest(unittest.TestCase):
    def test_merge_dedup_preserves_provenance(self) -> None:
        current = {
            "entries": [
                {
                    "key": "convention:stdlib-only",
                    "value": "Prefer stdlib only",
                    "sources": ["local"],
                    "updated_at": "2026-04-09T00:00:00Z",
                }
            ]
        }
        incoming = {
            "entries": [
                {
                    "key": "convention:stdlib-only",
                    "value": "Prefer stdlib only",
                    "sources": ["omx"],
                    "updated_at": "2026-04-09T01:00:00Z",
                },
                {
                    "key": "architecture:canonical-store",
                    "value": ".handoff is canonical",
                    "sources": ["spec"],
                    "updated_at": "2026-04-09T01:00:00Z",
                },
            ]
        }

        merged, log = merge_project_memory(current, incoming)

        self.assertEqual(len(merged["entries"]), 2)
        self.assertIn("omx", merged["entries"][0]["sources"])
        self.assertGreaterEqual(len(log), 1)


if __name__ == "__main__":
    unittest.main()
