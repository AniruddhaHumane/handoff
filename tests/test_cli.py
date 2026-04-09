import os
import subprocess
import sys
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
        self.assertEqual(main(["checkpoint"]), 0)


if __name__ == "__main__":
    unittest.main()
