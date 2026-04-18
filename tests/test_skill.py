import unittest
from pathlib import Path


class SkillSurfaceTest(unittest.TestCase):
    def test_repo_ships_handoff_and_get_handoff_skills(self) -> None:
        repo = Path(__file__).resolve().parents[1]
        handoff = repo / "skills" / "handoff" / "SKILL.md"
        get_handoff = repo / "skills" / "get-handoff" / "SKILL.md"

        self.assertTrue(handoff.exists())
        self.assertTrue(get_handoff.exists())

        handoff_text = handoff.read_text()
        get_handoff_text = get_handoff.read_text()
        self.assertIn("name: handoff", handoff_text)
        self.assertIn("/handoff", handoff_text)
        self.assertIn("name: get-handoff", get_handoff_text)
        self.assertIn("/get-handoff", get_handoff_text)


if __name__ == "__main__":
    unittest.main()
