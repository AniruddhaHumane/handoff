from contextlib import redirect_stdout
from io import StringIO
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from handoff.cli import main


class CLISmokeTest(unittest.TestCase):
    def test_help_exits_zero(self) -> None:
        repo = Path(__file__).resolve().parents[1]
        env = dict(os.environ)
        env["PYTHONPATH"] = str(repo / "src")
        result = subprocess.run(
            [sys.executable, "-m", "handoff.cli", "--help"],
            cwd=repo,
            capture_output=True,
            env=env,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("checkpoint", result.stdout)
        self.assertIn("resume", result.stdout)

    def test_main_accepts_explicit_argv(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            stdout = StringIO()
            with redirect_stdout(stdout):
                self.assertEqual(main(["checkpoint", "--root", tmp]), 0)


class CLIE2ETest(unittest.TestCase):
    def test_checkpoint_creates_restore_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = Path(__file__).resolve().parents[1]
            env = dict(os.environ)
            env["PYTHONPATH"] = str(repo / "src")

            result = subprocess.run(
                [sys.executable, "-m", "handoff.cli", "checkpoint", "--root", str(root)],
                cwd=repo,
                capture_output=True,
                env=env,
                text=True,
            )

            self.assertEqual(result.returncode, 0)
            self.assertTrue((root / ".handoff" / "restore.md").exists())

    def test_resume_prints_restore_contents(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            restore_path = root / ".handoff" / "restore.md"
            restore_path.parent.mkdir(parents=True)
            restore_path.write_text("# Restore Brief\n")
            repo = Path(__file__).resolve().parents[1]
            env = dict(os.environ)
            env["PYTHONPATH"] = str(repo / "src")

            result = subprocess.run(
                [sys.executable, "-m", "handoff.cli", "resume", "--root", str(root)],
                cwd=repo,
                capture_output=True,
                env=env,
                text=True,
            )

            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "# Restore Brief\n\n")


if __name__ == "__main__":
    unittest.main()
