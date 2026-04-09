import json
import tempfile
import unittest
from pathlib import Path

from handoff.capture import capture_session_state
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


class CaptureWriteTest(unittest.TestCase):
    def test_capture_updates_current_state_and_appends_history(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            capture_session_state(
                root=root,
                source="codex-skill",
                summary="We finished the checkpoint/resume implementation and want Claude to continue the UX layer.",
                next_action="Implement the to-claude command",
                open_tasks=["Add interactive fallback", "Improve wrapper UX"],
                key_decisions=["Use skill plus CLI", "Persist captured state"],
            )

            current = json.loads(
                (root / ".handoff" / "session" / "current.json").read_text()
            )
            self.assertEqual(
                current["captured_summary"],
                "We finished the checkpoint/resume implementation and want Claude to continue the UX layer.",
            )
            self.assertEqual(
                current["captured_open_tasks"],
                ["Add interactive fallback", "Improve wrapper UX"],
            )
            history = (
                root / ".handoff" / "session" / "capture-history.jsonl"
            ).read_text()
            self.assertIn('"source": "codex-skill"', history)

    def test_capture_appends_history_without_replacing_prior_events(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            capture_session_state(
                root=root,
                source="codex-skill",
                summary="first",
                next_action="first-action",
                open_tasks=[],
                key_decisions=[],
            )
            capture_session_state(
                root=root,
                source="codex-skill",
                summary="second",
                next_action="second-action",
                open_tasks=[],
                key_decisions=[],
            )
            lines = (
                root / ".handoff" / "session" / "capture-history.jsonl"
            ).read_text().strip().splitlines()
            self.assertEqual(len(lines), 2)

    def test_capture_writes_live_capture_note(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            capture_session_state(
                root=root,
                source="codex-skill",
                summary="Summary",
                next_action="Next action",
                open_tasks=["Task A"],
                key_decisions=["Decision A"],
            )
            note = (root / ".handoff" / "session" / "live-capture.md").read_text()
            self.assertIn("# Live Capture", note)
            self.assertIn("## Summary", note)
            self.assertIn("Captured from codex-skill", note)
