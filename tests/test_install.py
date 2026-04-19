import tempfile
import unittest
from pathlib import Path

from handoff.install import install_skills, main


class InstallSkillsTest(unittest.TestCase):
    def test_installs_codex_skills_from_local_source_as_symlinks(self) -> None:
        repo = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)

            installed = install_skills(
                runtime="codex",
                home=home,
                source_root=repo / "skills",
                mode="symlink",
            )

            handoff = home / ".codex" / "skills" / "handoff" / "SKILL.md"
            get_handoff = home / ".codex" / "skills" / "get-handoff" / "SKILL.md"
            self.assertEqual(installed, [handoff.parent, get_handoff.parent])
            self.assertTrue(handoff.exists())
            self.assertTrue(get_handoff.exists())
            self.assertTrue(handoff.parent.is_symlink())
            self.assertTrue(get_handoff.parent.is_symlink())

    def test_installs_claude_skills_from_local_source_as_copies(self) -> None:
        repo = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)

            install_skills(
                runtime="claude",
                home=home,
                source_root=repo / "skills",
                mode="copy",
            )

            handoff = home / ".claude" / "skills" / "handoff" / "SKILL.md"
            get_handoff = home / ".claude" / "skills" / "get-handoff" / "SKILL.md"
            self.assertTrue(handoff.exists())
            self.assertTrue(get_handoff.exists())
            self.assertFalse(handoff.parent.is_symlink())
            self.assertFalse(get_handoff.parent.is_symlink())

    def test_cli_accepts_home_source_and_mode(self) -> None:
        repo = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)

            result = main(
                [
                    "codex",
                    "--home",
                    str(home),
                    "--source",
                    str(repo / "skills"),
                    "--mode",
                    "copy",
                ]
            )

            self.assertEqual(result, 0)
            self.assertTrue((home / ".codex" / "skills" / "handoff" / "SKILL.md").exists())
            self.assertTrue(
                (home / ".codex" / "skills" / "get-handoff" / "SKILL.md").exists()
            )


if __name__ == "__main__":
    unittest.main()
