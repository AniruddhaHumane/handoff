from contextlib import redirect_stdout
from io import StringIO
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from handoff.capture import capture_session_state
from handoff.cli import main
from handoff.checkpoint import run_checkpoint, run_to_claude


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
    def _run_cli(self, *args: str, root: Path) -> subprocess.CompletedProcess[str]:
        repo = Path(__file__).resolve().parents[1]
        env = dict(os.environ)
        env["PYTHONPATH"] = str(repo / "src")
        return subprocess.run(
            [sys.executable, "-m", "handoff.cli", *args, "--root", str(root)],
            cwd=repo,
            capture_output=True,
            env=env,
            text=True,
        )

    def _write_json(self, path: Path, payload: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    def _seed_canonical_state(self, root: Path) -> None:
        handoff = root / ".handoff"
        self._write_json(
            handoff / "manifest.json",
            {
                "schema_version": "1",
                "active_adapter": "raw",
                "created_at": "2026-04-09T00:00:00Z",
                "updated_at": "2026-04-09T00:00:00Z",
                "last_checkpoint_at": None,
                "last_resume_at": None,
                "integrity": {
                    "algorithm": "sha256",
                    "canonical_layout_fingerprint": "fingerprint",
                },
            },
        )
        self._write_json(
            handoff / "session" / "current.json",
            {
                "goal": "Preserve seeded goal",
                "status": "working",
                "next_action": "Resume from merged restore",
                "active_mode": None,
                "timestamp": "2026-04-09T00:00:00Z",
                "last_checkpoint_at": None,
                "last_adapter_used": "raw",
            },
        )
        self._write_json(
            handoff / "tasks" / "tasks.json",
            {"tasks": ["Keep canonical task"]},
        )
        self._write_json(
            handoff / "plans" / "plan-index.json",
            {"active": None, "plans": []},
        )
        self._write_json(
            handoff / "memory" / "project-memory.json",
            {
                "entries": [
                    {
                        "key": "local:decision",
                        "value": "Keep canonical local decision",
                        "sources": ["local"],
                        "updated_at": "2026-04-09T00:00:00Z",
                    }
                ]
            },
        )
        self._write_json(handoff / "context" / "files-read.json", {"files": []})
        self._write_json(handoff / "context" / "files-touched.json", {"files": []})
        self._write_json(
            handoff / "context" / "constraints.json",
            {"sources": [], "rules": []},
        )
        self._write_json(
            handoff / "context" / "instruction-aliases.json",
            {"aliases": []},
        )
        self._write_json(handoff / "verification" / "checks.json", {"checks": []})

        for relative in (
            "restore.md",
            "session/recent-summary.md",
            "session/conversation-tail.md",
            "session/next-action.md",
            "session/status.md",
            "plans/active-plan.md",
            "verification/verification.md",
            "memory/memory-merge-log.jsonl",
        ):
            path = handoff / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            if relative == "restore.md":
                path.write_text("# Restore Brief\n\nstale restore\n")
            else:
                path.write_text("")

    def _seed_omx_state(self, root: Path, *, imported_task: str, imported_value: str) -> None:
        omx = root / ".omx"
        self._write_json(
            omx / "project-memory.json",
            {
                "entries": [
                    {
                        "key": "omx:decision",
                        "value": imported_value,
                        "sources": ["omx"],
                        "updated_at": "2026-04-09T01:00:00Z",
                    }
                ]
            },
        )
        self._write_json(
            omx / "state" / "session.json",
            {"cwd": str(root), "session_id": "omx-session"},
        )
        (omx / "plans").mkdir(parents=True, exist_ok=True)
        (omx / "plans" / "2026-04-09-portable-plan.md").write_text(
            "# Portable Handoff Plan\n\n"
            f"- {imported_task}\n"
        )
        (omx / "notepad.md").write_text(
            "## WORKING MEMORY\n"
            "[2026-04-09T01:00:00Z] Imported OMX notes are available.\n"
        )

    def test_checkpoint_creates_restore_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = self._run_cli("checkpoint", root=root)

            self.assertEqual(result.returncode, 0)
            self.assertTrue((root / ".handoff" / "restore.md").exists())

    def test_checkpoint_preserves_canonical_state_and_merges_omx_imports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._seed_canonical_state(root)
            self._seed_omx_state(
                root,
                imported_task="Import OMX plan task",
                imported_value="Merged OMX decision",
            )

            result = self._run_cli("checkpoint", root=root)

            self.assertEqual(result.returncode, 0)

            current = json.loads(
                (root / ".handoff" / "session" / "current.json").read_text()
            )
            self.assertEqual(current["goal"], "Preserve seeded goal")

            manifest = json.loads((root / ".handoff" / "manifest.json").read_text())
            self.assertEqual(manifest["active_adapter"], "omx")

            memory = json.loads(
                (root / ".handoff" / "memory" / "project-memory.json").read_text()
            )
            values = {entry["value"] for entry in memory["entries"]}
            self.assertEqual(
                values,
                {"Keep canonical local decision", "Merged OMX decision"},
            )

            restore = (root / ".handoff" / "restore.md").read_text()
            self.assertNotIn("stale restore", restore)
            self.assertIn("Preserve seeded goal", restore)
            self.assertIn("Keep canonical task", restore)
            self.assertIn("Import OMX plan task", restore)
            self.assertIn("Merged OMX decision", restore)

    def test_checkpoint_repairs_manifest_integrity_from_minimal_seed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._seed_canonical_state(root)
            self._write_json(
                root / ".handoff" / "manifest.json",
                {
                    "schema_version": "1",
                    "active_adapter": "raw",
                    "created_at": "2026-04-09T00:00:00Z",
                    "updated_at": "2026-04-09T00:00:00Z",
                    "last_checkpoint_at": None,
                    "last_resume_at": None,
                    "integrity": {},
                },
            )

            result = self._run_cli("checkpoint", root=root)

            self.assertEqual(result.returncode, 0)

            manifest = json.loads((root / ".handoff" / "manifest.json").read_text())
            self.assertEqual(manifest["integrity"]["algorithm"], "sha256")
            self.assertEqual(len(manifest["integrity"]["canonical_layout_fingerprint"]), 64)

    def test_resume_prints_restore_contents(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            restore_path = root / ".handoff" / "restore.md"
            restore_path.parent.mkdir(parents=True)
            restore_path.write_text("# Restore Brief\n")
            result = self._run_cli("resume", root=root)

            self.assertEqual(result.returncode, 0)
            self.assertIn("# Restore Brief", result.stdout)
            self.assertIn("## Exact Next Action", result.stdout)

    def test_resume_refreshes_restore_from_omx_imports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._seed_canonical_state(root)
            self._seed_omx_state(
                root,
                imported_task="Resume imported OMX task",
                imported_value="Resume imported OMX decision",
            )

            result = self._run_cli("resume", root=root)

            self.assertEqual(result.returncode, 0)
            self.assertIn("Resume imported OMX task", result.stdout)
            self.assertIn("Resume imported OMX decision", result.stdout)
            self.assertNotIn("stale restore", result.stdout)

            restore = (root / ".handoff" / "restore.md").read_text()
            self.assertEqual(result.stdout, restore + "\n")


class RestorePriorityTest(unittest.TestCase):
    def test_checkpoint_prefers_captured_state_in_restore(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            capture_session_state(
                root=root,
                source="codex-skill",
                summary="Captured summary",
                next_action="Captured next action",
                open_tasks=["Captured task"],
                key_decisions=["Captured decision"],
            )

            run_checkpoint(root)
            restore = (root / ".handoff" / "restore.md").read_text()

            self.assertTrue(restore.startswith("# Restore Brief\n"))
            self.assertIn("Captured summary", restore)
            self.assertIn("Captured next action", restore)
            self.assertIn("Captured task", restore)
            self.assertIn("Captured decision", restore)


class ToClaudeCommandTest(unittest.TestCase):
    def test_to_claude_prints_paste_ready_prompt_when_state_is_rich_enough(self) -> None:
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

            prompt = run_to_claude(root, input_fn=lambda _: self.fail("unexpected prompt"))

            self.assertIn("Read .handoff/restore.md first.", prompt)

    def test_to_claude_prompts_when_state_is_too_sparse(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            prompts = iter(
                ["Captured summary", "Captured next action", "Task A, Task B", "Decision A"]
            )

            prompt = run_to_claude(root, input_fn=lambda _: next(prompts))

            self.assertIn("Read .handoff/restore.md first.", prompt)
            current = json.loads(
                (root / ".handoff" / "session" / "current.json").read_text()
            )
            self.assertEqual(current["captured_summary"], "Captured summary")


if __name__ == "__main__":
    unittest.main()
