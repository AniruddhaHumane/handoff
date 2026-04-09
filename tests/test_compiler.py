import tempfile
import unittest
from pathlib import Path

from handoff.compiler import compile_restore
from handoff.store import HandoffStore


class RestoreCompilerTest(unittest.TestCase):
    def test_restore_contains_core_resume_sections(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = HandoffStore(root)
            store.ensure_layout()

            restore = compile_restore(
                goal="Ship portable handoff v1",
                status="Spec approved, plan written",
                next_action="Implement canonical store first",
                constraints=["Prefer stdlib only", "Keep .handoff canonical"],
                tasks=["Bootstrap CLI", "Implement store"],
                decisions=["Use optional OMX adapter"],
                verification=["Spec reviewed manually"],
            )

            self.assertIn("# Restore Brief", restore)
            self.assertIn("## Goal", restore)
            self.assertIn("## Status", restore)
            self.assertIn("## Constraints", restore)
            self.assertIn("## Open Tasks", restore)
            self.assertIn("## Important Decisions", restore)
            self.assertIn("## Verification", restore)
            self.assertIn("## Exact Next Action", restore)
            self.assertIn("## Portability Boundary", restore)
            self.assertIn("Ship portable handoff v1", restore)
            self.assertIn("Implement canonical store first", restore)
            self.assertIn("Keep .handoff canonical", restore)

    def test_restore_file_is_written(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = HandoffStore(root)
            store.ensure_layout()

            restore = compile_restore(
                goal="Goal",
                status="Status",
                next_action="Next",
                constraints=[],
                tasks=[],
                decisions=[],
                verification=[],
            )

            (root / ".handoff" / "restore.md").write_text(restore)

            self.assertTrue(
                (root / ".handoff" / "restore.md")
                .read_text()
                .startswith("# Restore Brief")
            )


if __name__ == "__main__":
    unittest.main()
