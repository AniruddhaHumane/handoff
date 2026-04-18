import json
import tempfile
import unittest
from pathlib import Path

from handoff.store import HandoffStore


class AgentStoreLayoutTest(unittest.TestCase):
    def test_ensure_layout_creates_agent_and_import_roots(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = HandoffStore(root)
            store.ensure_layout()

            self.assertTrue((root / ".handoff" / "agents").exists())
            self.assertTrue((root / ".handoff" / "imports").exists())
            self.assertTrue((root / ".handoff" / "shared").exists())

    def test_write_and_read_agent_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = HandoffStore(root)
            store.ensure_layout()

            payload = {
                "agent": "A",
                "timestamp": "2026-04-12T00:00:00Z",
                "summary": "Summary",
                "next_action": "Next",
            }

            path = store.write_agent_snapshot("A", payload)

            self.assertTrue(path.exists())
            self.assertEqual(store.read_agent_snapshot("A"), payload)
            self.assertEqual(json.loads(path.read_text()), payload)


if __name__ == "__main__":
    unittest.main()
