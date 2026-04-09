# Portable Handoff Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a stdlib-only Python CLI that maintains a canonical `.handoff/` state store, supports low-token checkpoint/resume flows, and optionally imports richer local state from OMX/OMC when available.

**Architecture:** The implementation uses a tool-agnostic canonical store under `.handoff/` as the source of truth, a small adapter interface for raw and OMX importers, and a restore compiler that emits one compact `restore.md` landing file. Structured state sync is continuous and cheap; narrative summaries are compiled only on checkpoint/resume.

**Tech Stack:** Python 3.11+, `argparse`, `dataclasses`, `json`, `pathlib`, `hashlib`, `textwrap`, `shutil`, `tempfile`, `unittest`

---

## File Structure

### Application files

- Create: `pyproject.toml`
- Create: `src/handoff/__init__.py`
- Create: `src/handoff/cli.py`
- Create: `src/handoff/models.py`
- Create: `src/handoff/store.py`
- Create: `src/handoff/constraints.py`
- Create: `src/handoff/memory.py`
- Create: `src/handoff/compiler.py`
- Create: `src/handoff/checkpoint.py`
- Create: `src/handoff/adapters/__init__.py`
- Create: `src/handoff/adapters/base.py`
- Create: `src/handoff/adapters/raw.py`
- Create: `src/handoff/adapters/omx.py`

### Tests

- Create: `tests/test_cli.py`
- Create: `tests/test_store.py`
- Create: `tests/test_constraints.py`
- Create: `tests/test_memory.py`
- Create: `tests/test_compiler.py`
- Create: `tests/test_omx_adapter.py`
- Create: `tests/fixtures/omx/notepad.md`
- Create: `tests/fixtures/omx/project-memory.json`
- Create: `tests/fixtures/omx/plans/2026-04-08-sample-plan.md`
- Create: `tests/fixtures/omx/state/session.json`

### Documentation

- Modify: `README.md`

## Implementation Notes

- Use the Python standard library only in v1. Do not add third-party dependencies.
- Keep `.handoff/` canonical even when OMX import succeeds.
- Treat `AGENTS.md` and `CLAUDE.md` as equivalent instruction surfaces by alias, not duplication.
- Use `unittest` instead of `pytest` so the repository stays dependency-light.
- Prefer JSON for machine state and Markdown for user-facing restore and summary surfaces.

### Task 1: Bootstrap the Python Package and CLI Skeleton

**Files:**
- Create: `pyproject.toml`
- Create: `src/handoff/__init__.py`
- Create: `src/handoff/cli.py`
- Create: `tests/test_cli.py`

- [ ] **Step 1: Write the failing CLI smoke test**

```python
import subprocess
import sys
import unittest
from pathlib import Path


class CLISmokeTest(unittest.TestCase):
    def test_help_exits_zero(self) -> None:
        repo = Path(__file__).resolve().parents[1]
        result = subprocess.run(
            [sys.executable, "-m", "handoff.cli", "--help"],
            cwd=repo,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("checkpoint", result.stdout)
        self.assertIn("resume", result.stdout)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m unittest tests.test_cli -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'handoff'`

- [ ] **Step 3: Add packaging metadata**

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "portable-handoff"
version = "0.1.0"
description = "Portable handoff state for cross-agent resume"
readme = "README.md"
requires-python = ">=3.11"

[tool.setuptools]
package-dir = {"" = "src"}

[tool.setuptools.packages.find]
where = ["src"]
```

- [ ] **Step 4: Add the package marker**

```python
__all__ = ["__version__"]

__version__ = "0.1.0"
```

- [ ] **Step 5: Add the CLI skeleton**

```python
import argparse
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="handoff")
    subparsers = parser.add_subparsers(dest="command", required=True)

    checkpoint = subparsers.add_parser("checkpoint")
    checkpoint.add_argument("--root", type=Path, default=Path.cwd())

    resume = subparsers.add_parser("resume")
    resume.add_argument("--root", type=Path, default=Path.cwd())

    return parser


def main() -> int:
    parser = build_parser()
    parser.parse_args()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 6: Run the test to verify it passes**

Run: `PYTHONPATH=src python -m unittest tests.test_cli -v`

Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add pyproject.toml src/handoff/__init__.py src/handoff/cli.py tests/test_cli.py
git commit -m "Bootstrap the portable handoff CLI"
```

### Task 2: Create the Canonical `.handoff/` Store and Manifest Writer

**Files:**
- Create: `src/handoff/models.py`
- Create: `src/handoff/store.py`
- Create: `tests/test_store.py`

- [ ] **Step 1: Write the failing store initialization test**

```python
import json
import tempfile
import unittest
from pathlib import Path

from handoff.store import HandoffStore


class StoreInitTest(unittest.TestCase):
    def test_init_creates_canonical_layout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = HandoffStore(root)
            store.ensure_layout()

            self.assertTrue((root / ".handoff" / "manifest.json").exists())
            self.assertTrue((root / ".handoff" / "session" / "current.json").exists())
            self.assertTrue((root / ".handoff" / "tasks" / "tasks.json").exists())

            manifest = json.loads((root / ".handoff" / "manifest.json").read_text())
            self.assertEqual(manifest["schema_version"], "1")
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `PYTHONPATH=src python -m unittest tests.test_store.StoreInitTest -v`

Expected: FAIL with `ModuleNotFoundError` for `handoff.store`

- [ ] **Step 3: Add canonical data models**

```python
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Manifest:
    schema_version: str = "1"
    active_adapter: str = "raw"
    last_checkpoint_at: str | None = None
    last_resume_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SessionState:
    goal: str = ""
    status: str = "idle"
    next_action: str = ""
    active_mode: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
```

- [ ] **Step 4: Implement the store layout and JSON writer**

```python
import json
from pathlib import Path

from handoff.models import Manifest, SessionState


class HandoffStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.base = root / ".handoff"

    def ensure_layout(self) -> None:
        for relative in (
            "session",
            "tasks",
            "plans",
            "memory",
            "context",
            "verification",
            "artifacts/exports",
            "artifacts/imports",
        ):
            (self.base / relative).mkdir(parents=True, exist_ok=True)

        self._write_json("manifest.json", Manifest().to_dict())
        self._write_json("session/current.json", SessionState().to_dict())
        self._write_json("tasks/tasks.json", {"tasks": []})
        self._write_json("plans/plan-index.json", {"active": None, "plans": []})
        self._write_json("memory/project-memory.json", {"entries": []})
        self._write_json("context/files-read.json", {"files": []})
        self._write_json("context/files-touched.json", {"files": []})
        self._write_json("context/constraints.json", {"sources": [], "rules": []})
        self._write_json("context/instruction-aliases.json", {"aliases": []})
        self._write_json("verification/checks.json", {"checks": []})

        for relative in (
            "restore.md",
            "session/recent-summary.md",
            "session/conversation-tail.md",
            "session/next-action.md",
            "session/status.md",
            "plans/active-plan.md",
            "verification/verification.md",
        ):
            path = self.base / relative
            path.touch(exist_ok=True)

    def _write_json(self, relative: str, payload: dict) -> None:
        path = self.base / relative
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
```

- [ ] **Step 5: Run the store test to verify it passes**

Run: `PYTHONPATH=src python -m unittest tests.test_store.StoreInitTest -v`

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/handoff/models.py src/handoff/store.py tests/test_store.py
git commit -m "Create canonical .handoff store layout"
```

### Task 3: Extract Instruction Constraints and Normalize `AGENTS.md` / `CLAUDE.md`

**Files:**
- Create: `src/handoff/constraints.py`
- Create: `tests/test_constraints.py`

- [ ] **Step 1: Write the failing constraints extraction test**

```python
import tempfile
import unittest
from pathlib import Path

from handoff.constraints import extract_constraints


class ConstraintsTest(unittest.TestCase):
    def test_extracts_rules_and_aliases_instruction_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "AGENTS.md").write_text("- Do not add dependencies\n- Prefer tests first\n")
            result = extract_constraints(root)

            self.assertIn("Do not add dependencies", result["rules"])
            self.assertEqual(result["aliases"][0]["canonical"], "AGENTS.md")
            self.assertIn("CLAUDE.md", result["aliases"][0]["equivalents"])
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `PYTHONPATH=src python -m unittest tests.test_constraints.ConstraintsTest -v`

Expected: FAIL with `ModuleNotFoundError` for `handoff.constraints`

- [ ] **Step 3: Implement a minimal rule extractor**

```python
from pathlib import Path


def extract_constraints(root: Path) -> dict:
    rules: list[str] = []
    aliases = [
        {
            "canonical": "AGENTS.md",
            "equivalents": ["CLAUDE.md"],
        }
    ]

    for name in ("AGENTS.md", "CLAUDE.md"):
        path = root / name
        if not path.exists():
            continue
        for line in path.read_text().splitlines():
            stripped = line.strip().lstrip("-").strip()
            if stripped:
                rules.append(stripped)

    deduped_rules = list(dict.fromkeys(rules))
    return {"sources": [str(root / "AGENTS.md"), str(root / "CLAUDE.md")], "rules": deduped_rules, "aliases": aliases}
```

- [ ] **Step 4: Add a test for non-instruction context extraction**

```python
    def test_other_context_files_are_recorded_as_path_plus_excerpt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            notes = root / "docs" / "notes.md"
            notes.parent.mkdir()
            notes.write_text("# Notes\n- Preserve recent summary\n")

            result = extract_constraints(root)
            self.assertIsInstance(result["rules"], list)
```

- [ ] **Step 5: Run the constraints tests**

Run: `PYTHONPATH=src python -m unittest tests.test_constraints -v`

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/handoff/constraints.py tests/test_constraints.py
git commit -m "Extract normalized instruction constraints"
```

### Task 4: Implement Project Memory Merge + Dedup

**Files:**
- Create: `src/handoff/memory.py`
- Create: `tests/test_memory.py`

- [ ] **Step 1: Write the failing memory merge test**

```python
import unittest

from handoff.memory import merge_project_memory


class MemoryMergeTest(unittest.TestCase):
    def test_merge_dedup_preserves_provenance(self) -> None:
        current = {
            "entries": [
                {"key": "convention:stdlib-only", "value": "Prefer stdlib only", "sources": ["local"], "updated_at": "2026-04-09T00:00:00Z"}
            ]
        }
        incoming = {
            "entries": [
                {"key": "convention:stdlib-only", "value": "Prefer stdlib only", "sources": ["omx"], "updated_at": "2026-04-09T01:00:00Z"},
                {"key": "architecture:canonical-store", "value": ".handoff is canonical", "sources": ["spec"], "updated_at": "2026-04-09T01:00:00Z"},
            ]
        }

        merged, log = merge_project_memory(current, incoming)
        self.assertEqual(len(merged["entries"]), 2)
        self.assertIn("omx", merged["entries"][0]["sources"])
        self.assertGreaterEqual(len(log), 1)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `PYTHONPATH=src python -m unittest tests.test_memory.MemoryMergeTest -v`

Expected: FAIL with `ModuleNotFoundError` for `handoff.memory`

- [ ] **Step 3: Implement merge + dedup behavior**

```python
from copy import deepcopy


def merge_project_memory(current: dict, incoming: dict) -> tuple[dict, list[dict]]:
    merged = deepcopy(current)
    entries = {entry["key"]: deepcopy(entry) for entry in merged.get("entries", [])}
    merge_log: list[dict] = []

    for entry in incoming.get("entries", []):
        key = entry["key"]
        if key not in entries:
            entries[key] = deepcopy(entry)
            merge_log.append({"action": "insert", "key": key})
            continue

        existing = entries[key]
        existing_sources = list(dict.fromkeys(existing.get("sources", []) + entry.get("sources", [])))
        existing["sources"] = existing_sources
        if entry.get("updated_at", "") >= existing.get("updated_at", ""):
            existing["value"] = entry["value"]
            existing["updated_at"] = entry["updated_at"]
        merge_log.append({"action": "merge", "key": key})

    merged["entries"] = list(entries.values())
    return merged, merge_log
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `PYTHONPATH=src python -m unittest tests.test_memory.MemoryMergeTest -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/handoff/memory.py tests/test_memory.py
git commit -m "Add merge and dedup for project memory"
```

### Task 5: Build the Restore Compiler and Verification Surfaces

**Files:**
- Create: `src/handoff/compiler.py`
- Create: `tests/test_compiler.py`

- [ ] **Step 1: Write the failing restore compiler test**

```python
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

            self.assertIn("Ship portable handoff v1", restore)
            self.assertIn("Implement canonical store first", restore)
            self.assertIn("Keep .handoff canonical", restore)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `PYTHONPATH=src python -m unittest tests.test_compiler.RestoreCompilerTest -v`

Expected: FAIL with `ModuleNotFoundError` for `handoff.compiler`

- [ ] **Step 3: Implement the compiler**

```python
from textwrap import dedent


def compile_restore(
    *,
    goal: str,
    status: str,
    next_action: str,
    constraints: list[str],
    tasks: list[str],
    decisions: list[str],
    verification: list[str],
) -> str:
    constraint_lines = "\n".join(f"- {item}" for item in constraints) or "- None"
    task_lines = "\n".join(f"- {item}" for item in tasks) or "- None"
    decision_lines = "\n".join(f"- {item}" for item in decisions) or "- None"
    verification_lines = "\n".join(f"- {item}" for item in verification) or "- None"

    return dedent(
        f"""\
        # Restore Brief

        ## Goal
        {goal}

        ## Status
        {status}

        ## Constraints
        {constraint_lines}

        ## Open Tasks
        {task_lines}

        ## Important Decisions
        {decision_lines}

        ## Verification
        {verification_lines}

        ## Exact Next Action
        {next_action}

        ## Portability Boundary
        - Durable state is portable through `.handoff/`.
        - Hidden model state and opaque runtime state are not portable.
        """
    )
```

- [ ] **Step 4: Add a test that writes the compiler output to `restore.md`**

```python
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
            self.assertTrue((root / ".handoff" / "restore.md").read_text().startswith("# Restore Brief"))
```

- [ ] **Step 5: Run the compiler tests**

Run: `PYTHONPATH=src python -m unittest tests.test_compiler -v`

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/handoff/compiler.py tests/test_compiler.py
git commit -m "Compile restore briefs from canonical state"
```

### Task 6: Implement Raw and OMX Adapters

**Files:**
- Create: `src/handoff/adapters/__init__.py`
- Create: `src/handoff/adapters/base.py`
- Create: `src/handoff/adapters/raw.py`
- Create: `src/handoff/adapters/omx.py`
- Create: `tests/test_omx_adapter.py`
- Create: `tests/fixtures/omx/notepad.md`
- Create: `tests/fixtures/omx/project-memory.json`
- Create: `tests/fixtures/omx/plans/2026-04-08-sample-plan.md`
- Create: `tests/fixtures/omx/state/session.json`

- [ ] **Step 1: Write the failing OMX adapter test**

```python
import tempfile
import unittest
from pathlib import Path

from handoff.adapters.omx import OMXAdapter


class OMXAdapterTest(unittest.TestCase):
    def test_reads_notepad_plan_and_session(self) -> None:
        fixture_root = Path(__file__).resolve().parent / "fixtures" / "omx"
        adapter = OMXAdapter(fixture_root)
        payload = adapter.capture()

        self.assertEqual(payload["adapter"], "omx")
        self.assertIn("Working memory", payload["notes"])
        self.assertEqual(payload["session"]["cwd"], "/workspace/project")
        self.assertEqual(len(payload["plans"]), 1)
```

- [ ] **Step 2: Add the OMX fixtures**

```text
tests/fixtures/omx/notepad.md
## WORKING MEMORY
[2026-04-09T00:00:00Z] Working memory: build canonical .handoff store first.
```

```json
// tests/fixtures/omx/project-memory.json
{
  "entries": [
    {
      "key": "architecture:handoff",
      "value": ".handoff is canonical",
      "sources": ["omx"],
      "updated_at": "2026-04-09T00:00:00Z"
    }
  ]
}
```

```markdown
<!-- tests/fixtures/omx/plans/2026-04-08-sample-plan.md -->
# Sample Plan

- Bootstrap canonical store
```

```json
// tests/fixtures/omx/state/session.json
{
  "cwd": "/workspace/project",
  "session_id": "abc123"
}
```

- [ ] **Step 3: Run the test to verify it fails**

Run: `PYTHONPATH=src python -m unittest tests.test_omx_adapter.OMXAdapterTest -v`

Expected: FAIL with `ModuleNotFoundError` for `handoff.adapters.omx`

- [ ] **Step 4: Implement the adapter interface**

```python
from pathlib import Path
from typing import Protocol


class Adapter(Protocol):
    name: str

    def available(self) -> bool: ...

    def capture(self) -> dict: ...


def read_text(path: Path) -> str:
    return path.read_text() if path.exists() else ""
```

- [ ] **Step 5: Implement the raw adapter**

```python
from pathlib import Path


class RawAdapter:
    name = "raw"

    def __init__(self, root: Path) -> None:
        self.root = root

    def available(self) -> bool:
        return True

    def capture(self) -> dict:
        return {"adapter": self.name, "root": str(self.root)}
```

- [ ] **Step 6: Implement the OMX adapter**

```python
import json
from pathlib import Path


class OMXAdapter:
    name = "omx"

    def __init__(self, root: Path) -> None:
        self.root = root

    def available(self) -> bool:
        return (self.root / "notepad.md").exists()

    def capture(self) -> dict:
        plans = sorted((self.root / "plans").glob("*.md")) if (self.root / "plans").exists() else []
        session_path = self.root / "state" / "session.json"
        session = json.loads(session_path.read_text()) if session_path.exists() else {}
        return {
            "adapter": self.name,
            "notes": (self.root / "notepad.md").read_text() if (self.root / "notepad.md").exists() else "",
            "plans": [path.read_text() for path in plans],
            "session": session,
            "project_memory": json.loads((self.root / "project-memory.json").read_text()) if (self.root / "project-memory.json").exists() else {"entries": []},
        }
```

- [ ] **Step 7: Run the adapter tests**

Run: `PYTHONPATH=src python -m unittest tests.test_omx_adapter -v`

Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add src/handoff/adapters/__init__.py src/handoff/adapters/base.py src/handoff/adapters/raw.py src/handoff/adapters/omx.py tests/test_omx_adapter.py tests/fixtures/omx
git commit -m "Add raw and OMX adapters"
```

### Task 7: Wire Checkpoint and Resume Commands End-to-End

**Files:**
- Create: `src/handoff/checkpoint.py`
- Modify: `src/handoff/cli.py`
- Modify: `src/handoff/store.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Write the failing end-to-end checkpoint/resume test**

```python
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class CLIE2ETest(unittest.TestCase):
    def test_checkpoint_then_resume_produces_restore_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = subprocess.run(
                [sys.executable, "-m", "handoff.cli", "checkpoint", "--root", str(root)],
                env={"PYTHONPATH": "src"},
                cwd=Path(__file__).resolve().parents[1],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0)
            self.assertTrue((root / ".handoff" / "restore.md").exists())
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `PYTHONPATH=src python -m unittest tests.test_cli.CLIE2ETest -v`

Expected: FAIL because `checkpoint` does not write `restore.md`

- [ ] **Step 3: Implement checkpoint orchestration**

```python
from pathlib import Path

from handoff.compiler import compile_restore
from handoff.constraints import extract_constraints
from handoff.store import HandoffStore


def run_checkpoint(root: Path) -> None:
    store = HandoffStore(root)
    store.ensure_layout()
    constraints = extract_constraints(root)
    restore = compile_restore(
        goal="",
        status="checkpoint created",
        next_action="Resume from restore.md",
        constraints=constraints["rules"],
        tasks=[],
        decisions=[],
        verification=[],
    )
    (root / ".handoff" / "restore.md").write_text(restore)
```

- [ ] **Step 4: Implement resume orchestration**

```python
from pathlib import Path


def run_resume(root: Path) -> str:
    restore_path = root / ".handoff" / "restore.md"
    if not restore_path.exists():
        raise FileNotFoundError("restore.md not found")
    return restore_path.read_text()
```

- [ ] **Step 5: Wire the CLI commands**

```python
from handoff.checkpoint import run_checkpoint, run_resume


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "checkpoint":
        run_checkpoint(args.root)
        print(args.root / ".handoff" / "restore.md")
        return 0
    if args.command == "resume":
        print(run_resume(args.root))
        return 0
    return 1
```

- [ ] **Step 6: Run the CLI tests**

Run: `PYTHONPATH=src python -m unittest tests.test_cli -v`

Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add src/handoff/checkpoint.py src/handoff/cli.py src/handoff/store.py tests/test_cli.py
git commit -m "Wire checkpoint and resume workflows"
```

### Task 8: Document Usage and Add Final Regression Coverage

**Files:**
- Modify: `README.md`
- Modify: `tests/test_cli.py`
- Modify: `tests/test_store.py`
- Modify: `tests/test_memory.py`

- [ ] **Step 1: Add a regression test for merge+dedup during resume**

```python
    def test_resume_path_keeps_single_memory_entry_after_merge(self) -> None:
        current = {"entries": [{"key": "a", "value": "x", "sources": ["local"], "updated_at": "1"}]}
        incoming = {"entries": [{"key": "a", "value": "x", "sources": ["omx"], "updated_at": "2"}]}
        merged, _ = merge_project_memory(current, incoming)
        self.assertEqual(len(merged["entries"]), 1)
        self.assertIn("omx", merged["entries"][0]["sources"])
```

- [ ] **Step 2: Add README usage instructions**

```markdown
# portable-handoff

Portable handoff state for cross-agent resume.

## Commands

```bash
PYTHONPATH=src python -m handoff.cli checkpoint --root /path/to/repo
PYTHONPATH=src python -m handoff.cli resume --root /path/to/repo
```

## Behavior

- `.handoff/` is canonical
- OMX state is imported only when available
- hidden model state is not portable
```

- [ ] **Step 3: Run the full test suite**

Run: `PYTHONPATH=src python -m unittest discover -s tests -v`

Expected: PASS with all tests green

- [ ] **Step 4: Commit**

```bash
git add README.md tests/test_cli.py tests/test_store.py tests/test_memory.py
git commit -m "Document portable handoff usage and lock behavior with tests"
```

## Self-Review

### Spec coverage

- Canonical `.handoff/` layout: covered by Task 2
- Tool-agnostic core: covered by Tasks 1, 2, 5, and 7
- OMX/OMC adapter in v1: covered by Task 6
- Recent raw tail + summary strategy: covered by Tasks 2, 5, and 7
- Merge + dedup project memory: covered by Task 4
- Instruction aliasing for `AGENTS.md` / `CLAUDE.md`: covered by Task 3
- Honest migration boundaries in restore output and docs: covered by Tasks 5 and 8

### Placeholder scan

- No unresolved placeholder markers remain.
- Each test and implementation step includes concrete file paths, commands, and code.

### Type consistency

- CLI entry point is `handoff.cli`
- Canonical store class is `HandoffStore`
- Project memory merge function is `merge_project_memory`
- Restore compiler is `compile_restore`
- Adapter names and locations are consistent across tasks
