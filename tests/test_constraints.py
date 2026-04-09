import tempfile
import unittest
from pathlib import Path

from handoff.constraints import extract_constraints


class ConstraintsTest(unittest.TestCase):
    def test_extracts_rules_and_aliases_instruction_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            agents = root / "AGENTS.md"
            agents.write_text(
                "- Do not add dependencies\n- Prefer tests first\n"
            )

            result = extract_constraints(root)

            self.assertEqual(result["sources"], [str(agents)])
            self.assertIn("Do not add dependencies", result["rules"])
            self.assertEqual(result["aliases"][0]["canonical"], "AGENTS.md")
            self.assertIn("CLAUDE.md", result["aliases"][0]["equivalents"])

    def test_other_context_files_are_recorded_as_path_plus_excerpt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            notes = root / "docs" / "notes.md"
            notes.parent.mkdir()
            notes.write_text("# Notes\n- Preserve recent summary\n")

            result = extract_constraints(root)

            self.assertEqual(result["sources"], [])
            self.assertEqual(len(result["context_files"]), 1)
            self.assertEqual(result["context_files"][0]["path"], str(notes))
            self.assertIn(
                "Preserve recent summary", result["context_files"][0]["excerpt"]
            )
            self.assertIn(
                "Preserve recent summary", result["context_files"][0]["facts"]
            )


if __name__ == "__main__":
    unittest.main()
