import json
import tempfile
import unittest
from pathlib import Path

from handoff.capture import capture_agent_handoff, get_handoff


class AgentHandoffIntegrationTest(unittest.TestCase):
    def test_single_agent_get_handoff_uses_that_agent_as_primary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            capture_agent_handoff(
                root=root,
                agent="A",
                runtime="codex",
                source="handoff-skill",
                summary="Agent A summary",
                next_action="Agent A next",
                open_tasks=["Task A"],
                key_decisions=["Decision A"],
            )

            merged = get_handoff(root, ["A"])

            self.assertEqual(merged["primary_agent"], "A")
            import_markdown = (root / ".handoff" / "imports" / "current-get-handoff.md").read_text()
            self.assertIn("Agent: A", import_markdown)

    def test_multi_agent_get_handoff_uses_newest_snapshot_as_primary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            capture_agent_handoff(
                root=root,
                agent="A",
                runtime="codex",
                source="handoff-skill",
                summary="Agent A summary",
                next_action="Agent A next",
                open_tasks=["Task A"],
                key_decisions=["Decision A"],
            )
            snapshot_b = capture_agent_handoff(
                root=root,
                agent="B",
                runtime="claude",
                source="handoff-skill",
                summary="Agent B summary",
                next_action="Agent B next",
                open_tasks=["Task B"],
                key_decisions=["Decision B"],
            )
            snapshot_a = json.loads((root / ".handoff" / "agents" / "A" / "snapshot.json").read_text())
            snapshot_b["timestamp"] = "9999-12-31T23:59:59Z"
            (root / ".handoff" / "agents" / "B" / "snapshot.json").write_text(
                json.dumps(snapshot_b, indent=2, sort_keys=True) + "\n"
            )

            merged = get_handoff(root, ["A", "B"])

            self.assertEqual(snapshot_a["agent"], "A")
            self.assertEqual(merged["primary_agent"], "B")
            self.assertEqual(merged["summary"], "Agent B summary")
            import_payload = json.loads(
                (root / ".handoff" / "imports" / "current-get-handoff.json").read_text()
            )
            self.assertEqual(import_payload["sources"], ["B", "A"])


if __name__ == "__main__":
    unittest.main()
