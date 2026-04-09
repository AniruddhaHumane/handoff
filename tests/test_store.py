import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from handoff.store import HandoffStore


class StoreInitTest(unittest.TestCase):
    def test_init_creates_canonical_layout_and_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = HandoffStore(root)
            store.ensure_layout()

            base = root / ".handoff"
            expected_directories = (
                "session",
                "tasks",
                "plans",
                "memory",
                "context",
                "verification",
                "artifacts",
                "artifacts/exports",
                "artifacts/imports",
            )
            expected_files = (
                "manifest.json",
                "restore.md",
                "session/current.json",
                "session/recent-summary.md",
                "session/conversation-tail.md",
                "session/next-action.md",
                "session/status.md",
                "tasks/tasks.json",
                "plans/active-plan.md",
                "plans/plan-index.json",
                "memory/project-memory.json",
                "memory/memory-merge-log.jsonl",
                "context/files-read.json",
                "context/files-touched.json",
                "context/constraints.json",
                "context/instruction-aliases.json",
                "verification/verification.md",
                "verification/checks.json",
            )

            for relative in expected_directories:
                self.assertTrue((base / relative).is_dir(), relative)

            for relative in expected_files:
                self.assertTrue((base / relative).exists(), relative)

            manifest = json.loads((base / "manifest.json").read_text())
            self.assertEqual(manifest["schema_version"], "1")
            self.assertEqual(manifest["active_adapter"], "raw")
            self.assertIsInstance(manifest["created_at"], str)
            self.assertIsInstance(manifest["updated_at"], str)
            self.assertEqual(manifest["created_at"], manifest["updated_at"])
            self.assertIsNone(manifest["last_checkpoint_at"])
            self.assertIsNone(manifest["last_resume_at"])
            self.assertEqual(manifest["integrity"]["algorithm"], "sha256")
            self.assertEqual(
                len(manifest["integrity"]["canonical_layout_fingerprint"]),
                64,
            )
            expected_entries = sorted(expected_directories + expected_files)
            expected_fingerprint = hashlib.sha256(
                "\n".join(expected_entries).encode("utf-8")
            ).hexdigest()
            self.assertEqual(
                manifest["integrity"]["canonical_layout_fingerprint"],
                expected_fingerprint,
            )

            session = json.loads((base / "session" / "current.json").read_text())
            self.assertEqual(session["goal"], "")
            self.assertEqual(session["status"], "idle")
            self.assertEqual(session["next_action"], "")
            self.assertIsNone(session["active_mode"])
            self.assertIsInstance(session["timestamp"], str)
            self.assertIsNone(session["last_checkpoint_at"])
            self.assertEqual(session["last_adapter_used"], "raw")

            self.assertEqual((base / "memory" / "memory-merge-log.jsonl").read_text(), "")


if __name__ == "__main__":
    unittest.main()
