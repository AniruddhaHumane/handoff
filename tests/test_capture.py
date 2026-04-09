import json
import tempfile
import unittest
from pathlib import Path

from handoff.store import HandoffStore


class CaptureStateTest(unittest.TestCase):
    def test_ensure_layout_initializes_capture_fields_and_history_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = HandoffStore(root)
            store.ensure_layout()

            current = json.loads(
                (root / ".handoff" / "session" / "current.json").read_text()
            )
            self.assertIn("captured_summary", current)
            self.assertIn("captured_open_tasks", current)
            self.assertIn("captured_key_decisions", current)
            self.assertTrue(
                (root / ".handoff" / "session" / "capture-history.jsonl").exists()
            )


if __name__ == "__main__":
    unittest.main()
