import json
import tempfile
import unittest
from pathlib import Path

from handoff.capture import run_get_handoff, run_handoff


class SkillWorkflowTest(unittest.TestCase):
    def test_run_handoff_uses_resolved_agent_name_and_updates_shared_constraints(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "AGENTS.md").write_text("- Prefer tests first\n")

            message = run_handoff(
                root=root,
                explicit_agent=None,
                default_agent="agent-A",
                runtime="codex",
                source="handoff-skill",
                summary="Finished parser cleanup",
                next_action="Implement merge rendering",
                open_tasks=["Task A"],
                key_decisions=["Decision A"],
            )

            self.assertEqual(message, "handoff saved for agent: agent-A")
            snapshot = json.loads(
                (root / ".handoff" / "agents" / "agent-A" / "snapshot.json").read_text()
            )
            self.assertEqual(snapshot["agent"], "agent-A")
            constraints = json.loads(
                (root / ".handoff" / "shared" / "constraints.json").read_text()
            )
            self.assertIn("Prefer tests first", constraints["rules"])

    def test_run_get_handoff_merges_newest_primary_and_combines_supporting_lists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "AGENTS.md").write_text("- Prefer tests first\n")

            run_handoff(
                root=root,
                explicit_agent="A",
                default_agent=None,
                runtime="codex",
                source="handoff-skill",
                summary="Older summary",
                next_action="Older next",
                open_tasks=["Task A"],
                key_decisions=["Decision A"],
                blockers=["Blocker A"],
                files_touched=["src/a.py"],
                files_read_first=["README.md"],
                verification=["unit A"],
                incoming_project_memory={
                    "entries": [
                        {
                            "key": "architecture:a",
                            "value": "A note",
                            "sources": ["agent-A"],
                            "updated_at": "2026-04-12T00:00:00Z",
                        }
                    ]
                },
            )
            run_handoff(
                root=root,
                explicit_agent="B",
                default_agent=None,
                runtime="claude",
                source="handoff-skill",
                summary="Newer summary",
                next_action="Newer next",
                open_tasks=["Task B"],
                key_decisions=["Decision B"],
                blockers=["Blocker B"],
                files_touched=["src/b.py"],
                files_read_first=["src/b.py"],
                verification=["unit B"],
                incoming_project_memory={
                    "entries": [
                        {
                            "key": "architecture:b",
                            "value": "B note",
                            "sources": ["agent-B"],
                            "updated_at": "2026-04-12T01:00:00Z",
                        }
                    ]
                },
            )

            markdown = run_get_handoff(root=root, source_agents=["A", "B"])

            self.assertIn("# Get Handoff", markdown)
            self.assertIn("Agent: B", markdown)
            self.assertIn("Task A", markdown)
            self.assertIn("Task B", markdown)
            self.assertIn("Decision A", markdown)
            self.assertIn("Decision B", markdown)
            payload = json.loads(
                (root / ".handoff" / "imports" / "current-get-handoff.json").read_text()
            )
            self.assertEqual(payload["primary_agent"], "B")
            self.assertEqual(payload["summary"], "Newer summary")
            self.assertEqual(payload["next_action"], "Newer next")
            self.assertEqual(payload["open_tasks"], ["Task B", "Task A"])
            self.assertEqual(payload["key_decisions"], ["Decision B", "Decision A"])
            self.assertEqual(payload["blockers"], ["Blocker B", "Blocker A"])
            self.assertEqual(payload["files_touched"], ["src/b.py", "src/a.py"])
            self.assertEqual(payload["files_read_first"], ["src/b.py", "README.md"])
            self.assertEqual(payload["verification"], ["unit B", "unit A"])
            self.assertEqual(payload["project_memory"], ["B note", "A note"])


if __name__ == "__main__":
    unittest.main()
