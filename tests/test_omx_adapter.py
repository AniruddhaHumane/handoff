import unittest
from pathlib import Path

from handoff.adapters.omx import OMXAdapter


class OMXAdapterTest(unittest.TestCase):
    def test_reads_notepad_plan_and_session(self) -> None:
        fixture_root = Path(__file__).resolve().parent / "fixtures" / "omx"
        adapter = OMXAdapter(fixture_root)
        payload = adapter.capture()

        self.assertEqual(payload["adapter"], "omx")
        self.assertIn("Working memory", payload["notes"])
        self.assertEqual(payload["session"]["cwd"], "/workspace/project")
        self.assertEqual(len(payload["plans"]), 1)


if __name__ == "__main__":
    unittest.main()
