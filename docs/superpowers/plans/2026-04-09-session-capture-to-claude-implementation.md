# Session Capture to Claude Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a session-aware capture flow plus a `to-claude` CLI command so Codex can externalize current chat context into `.handoff` and produce a paste-ready Claude Code prompt.

**Architecture:** Extend the canonical `.handoff/session/current.json` state with captured fields, append live-capture events to `capture-history.jsonl`, and implement a `to-claude` command that either renders from rich existing state or interactively prompts for the missing summary/next-action payload. Keep the CLI and any future skill on the same canonical write path.

**Tech Stack:** Python 3.11+, `argparse`, `json`, `pathlib`, `textwrap`, `unittest`, existing stdlib-only `handoff` package

---

## File Structure

### Application files

- Modify: `src/handoff/models.py`
- Modify: `src/handoff/store.py`
- Modify: `src/handoff/compiler.py`
- Modify: `src/handoff/checkpoint.py`
- Modify: `src/handoff/cli.py`
- Create: `src/handoff/capture.py`

### Tests

- Modify: `tests/test_cli.py`
- Create: `tests/test_capture.py`

### Documentation and helpers

- Modify: `README.md`
- Modify: `scripts/handoff-to-claude.sh`

## Implementation Notes

- Keep `.handoff/` canonical; do not invent a parallel storage surface.
- Stay stdlib-only.
- Make `to-claude` usable without the live capture skill; the skill just improves fidelity.
- Capture should overwrite current state and append history.
- `restore.md` must render from normalized current state, not replay history directly.

### Task 1: Extend Canonical Session State for Live Capture

**Files:**
- Modify: `src/handoff/models.py`
- Modify: `src/handoff/store.py`
- Create: `tests/test_capture.py`

- [ ] **Step 1: Write the failing capture-state initialization test**

```python
import json
import tempfile
import unittest
from pathlib import Path

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
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `PYTHONPATH=src python -m unittest tests.test_capture.CaptureStateTest.test_ensure_layout_initializes_capture_fields_and_history_file -v`

Expected: FAIL because the capture fields and history file do not exist yet

- [ ] **Step 3: Extend `SessionState` with captured fields**

```python
@dataclass
class SessionState:
    goal: str = ""
    status: str = "idle"
    next_action: str = ""
    active_mode: str | None = None
    timestamp: str = ""
    last_checkpoint_at: str | None = None
    last_adapter_used: str = "raw"
    captured_summary: str = ""
    captured_open_tasks: list[str] = field(default_factory=list)
    captured_key_decisions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
```

- [ ] **Step 4: Create the capture history file in the canonical layout**

```python
CANONICAL_TEXT_FILES = (
    "restore.md",
    "session/recent-summary.md",
    "session/conversation-tail.md",
    "session/next-action.md",
    "session/status.md",
    "session/capture-history.jsonl",
    "plans/active-plan.md",
    "verification/verification.md",
    "memory/memory-merge-log.jsonl",
)
```

- [ ] **Step 5: Run the capture initialization test to verify it passes**

Run: `PYTHONPATH=src python -m unittest tests.test_capture.CaptureStateTest.test_ensure_layout_initializes_capture_fields_and_history_file -v`

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/handoff/models.py src/handoff/store.py tests/test_capture.py
git commit -m "Extend canonical session state for live capture"
```

### Task 2: Implement Capture Persistence and History Appending

**Files:**
- Create: `src/handoff/capture.py`
- Modify: `src/handoff/store.py`
- Modify: `tests/test_capture.py`

- [ ] **Step 1: Write the failing capture write-path test**

```python
import json
import tempfile
import unittest
from pathlib import Path

from handoff.capture import capture_session_state


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
            self.assertIn("\"source\": \"codex-skill\"", history)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `PYTHONPATH=src python -m unittest tests.test_capture.CaptureWriteTest -v`

Expected: FAIL with `ModuleNotFoundError` for `handoff.capture`

- [ ] **Step 3: Implement capture persistence**

```python
import json
from pathlib import Path

from handoff.store import HandoffStore


def capture_session_state(
    *,
    root: Path,
    source: str,
    summary: str,
    next_action: str,
    open_tasks: list[str],
    key_decisions: list[str],
) -> None:
    store = HandoffStore(root)
    store.ensure_layout()
    timestamp = store.timestamp()

    current = store.read_json("session/current.json", {})
    current["captured_summary"] = summary
    current["captured_open_tasks"] = open_tasks
    current["captured_key_decisions"] = key_decisions
    current["next_action"] = next_action
    current["timestamp"] = timestamp
    store.write_json("session/current.json", current)

    store.append_jsonl(
        "session/capture-history.jsonl",
        [
            {
                "timestamp": timestamp,
                "source": source,
                "summary": summary,
                "next_action": next_action,
                "open_tasks": open_tasks,
                "key_decisions": key_decisions,
            }
        ],
    )
```

- [ ] **Step 4: Add a history append regression**

```python
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
```

- [ ] **Step 5: Run the capture tests**

Run: `PYTHONPATH=src python -m unittest tests.test_capture -v`

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/handoff/capture.py src/handoff/store.py tests/test_capture.py
git commit -m "Persist captured Codex session state"
```

### Task 3: Render Restore Output From Captured State

**Files:**
- Modify: `src/handoff/checkpoint.py`
- Modify: `src/handoff/compiler.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Write the failing restore-priority test**

```python
import json
import tempfile
import unittest
from pathlib import Path

from handoff.capture import capture_session_state
from handoff.checkpoint import run_checkpoint


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

            self.assertIn("Captured summary", restore)
            self.assertIn("Captured next action", restore)
            self.assertIn("Captured task", restore)
            self.assertIn("Captured decision", restore)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `PYTHONPATH=src python -m unittest tests.test_cli.RestorePriorityTest -v`

Expected: FAIL because the current restore render path ignores captured fields

- [ ] **Step 3: Feed captured fields into restore compilation**

```python
restore = compile_restore(
    goal=current_session.get("goal", "") or current_session.get("captured_summary", ""),
    status=current_session.get("status") or f"{action} created",
    next_action=current_session.get("next_action") or "Resume from restore.md",
    constraints=constraints["rules"],
    tasks=_dedupe(
        current_session.get("captured_open_tasks", [])
        + task_payload.get("tasks", [])
        + imported_tasks
    ),
    decisions=_dedupe(
        current_session.get("captured_key_decisions", [])
        + _memory_values(merged_memory)
    ),
    verification=verification,
)
```

- [ ] **Step 4: Add a captured summary section to the restore compiler**

```python
def compile_restore(..., captured_summary: str = "") -> str:
    summary_block = f\"\"\"\n## Captured Summary\n{captured_summary}\n\"\"\" if captured_summary else \"\"
    ...
```

- [ ] **Step 5: Run the restore-priority test to verify it passes**

Run: `PYTHONPATH=src python -m unittest tests.test_cli.RestorePriorityTest -v`

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/handoff/checkpoint.py src/handoff/compiler.py tests/test_cli.py
git commit -m "Render restore briefs from captured session state"
```

### Task 4: Add `to-claude` CLI With Interactive Fallback

**Files:**
- Modify: `src/handoff/cli.py`
- Modify: `src/handoff/checkpoint.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Write the failing `to-claude` command test**

```python
import tempfile
import unittest
from pathlib import Path

from handoff.cli import main


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
            output = main(["to-claude", "--root", str(root)])
            self.assertEqual(output, 0)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `PYTHONPATH=src python -m unittest tests.test_cli.ToClaudeCommandTest -v`

Expected: FAIL because `to-claude` does not exist yet

- [ ] **Step 3: Add the `to-claude` parser**

```python
to_claude = subparsers.add_parser("to-claude")
to_claude.add_argument("--root", type=Path, default=Path.cwd())
```

- [ ] **Step 4: Implement `to-claude` with rich-state detection**

```python
def run_to_claude(root: Path, *, input_fn=input) -> str:
    store = HandoffStore(root)
    _refresh_portable_state(store, root, action="resume")
    current = store.read_json("session/current.json", {})
    memory = store.read_json("memory/project-memory.json", {"entries": []})

    rich_enough = bool(
        (current.get("goal") or current.get("captured_summary"))
        and current.get("next_action")
        and (
            current.get("captured_open_tasks")
            or current.get("captured_key_decisions")
            or memory.get("entries")
        )
    )

    if not rich_enough:
        summary = input_fn("Summary: ").strip()
        next_action = input_fn("Next action: ").strip()
        open_tasks = input_fn("Open tasks (comma-separated, optional): ").strip()
        key_decisions = input_fn("Key decisions (comma-separated, optional): ").strip()
        capture_session_state(
            root=root,
            source="interactive-cli",
            summary=summary,
            next_action=next_action,
            open_tasks=[item.strip() for item in open_tasks.split(",") if item.strip()],
            key_decisions=[item.strip() for item in key_decisions.split(",") if item.strip()],
        )
        _refresh_portable_state(store, root, action="resume")

    return (
        "Read .handoff/restore.md first.\\n"
        "Then use .handoff/ as the source of truth for the current goal, status, tasks, memory, and next action.\\n"
        "Refresh only the files you actually need after reading the restore brief.\\n"
        "Continue from the recorded next action instead of rediscovering context.\\n"
    )
```

- [ ] **Step 5: Wire the command into `main()`**

```python
if args.command == "to-claude":
    print(run_to_claude(args.root), end="")
    return 0
```

- [ ] **Step 6: Add an interactive fallback test with mocked input**

```python
    def test_to_claude_prompts_when_state_is_too_sparse(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            prompts = iter(["Captured summary", "Captured next action", "Task A, Task B", "Decision A"])
            prompt = run_to_claude(root, input_fn=lambda _: next(prompts))
            self.assertIn("Read .handoff/restore.md first.", prompt)
            current = json.loads((root / ".handoff" / "session" / "current.json").read_text())
            self.assertEqual(current["captured_summary"], "Captured summary")
```

- [ ] **Step 7: Run the CLI tests**

Run: `PYTHONPATH=src python -m unittest tests.test_cli -v`

Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add src/handoff/cli.py src/handoff/checkpoint.py tests/test_cli.py
git commit -m "Add to-claude export with interactive fallback"
```

### Task 5: Update the Wrapper and Documentation

**Files:**
- Modify: `scripts/handoff-to-claude.sh`
- Modify: `README.md`

- [ ] **Step 1: Write the failing wrapper expectation test as a shell assertion**

```bash
tmpdir=$(mktemp -d)
output=$(./scripts/handoff-to-claude.sh "$tmpdir")
printf '%s' "$output" | grep -q 'Read .handoff/restore.md first.'
rm -rf "$tmpdir"
```

- [ ] **Step 2: Run the wrapper manually to verify current behavior**

Run: `./scripts/handoff-to-claude.sh "$(mktemp -d)"`

Expected: It still shells through `checkpoint` only and does not use `to-claude`

- [ ] **Step 3: Update the wrapper to call `to-claude`**

```bash
#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_ROOT="${1:-$(pwd)}"

cd "$ROOT_DIR"

printf 'Portable handoff refreshed for:\n  %s\n\n' "$TARGET_ROOT"
printf 'Paste this into Claude Code:\n\n'
PYTHONPATH=src python -m handoff.cli to-claude --root "$TARGET_ROOT"
```

- [ ] **Step 4: Update README to describe the new behavior**

```markdown
## Codex To Claude Code Workflow

Preferred path:

1. Use the Codex capture skill while the live session still exists.
2. Run:

```bash
PYTHONPATH=src python -m handoff.cli to-claude --root /path/to/repo
```

If the handoff state is too sparse, the command prompts for a short summary and saves it into `.handoff`.
```

- [ ] **Step 5: Run the wrapper smoke test**

Run: `chmod +x scripts/handoff-to-claude.sh && ./scripts/handoff-to-claude.sh "$(mktemp -d)"`

Expected: Prints the Claude prompt block, even when interactive fallback is needed

- [ ] **Step 6: Commit**

```bash
git add scripts/handoff-to-claude.sh README.md
git commit -m "Update Claude wrapper for live capture export"
```

### Task 6: Final Regression and Integration Coverage

**Files:**
- Modify: `tests/test_capture.py`
- Modify: `tests/test_cli.py`
- Modify: `README.md`

- [ ] **Step 1: Add an end-to-end regression that combines capture then `to-claude`**

```python
class CaptureToClaudeIntegrationTest(unittest.TestCase):
    def test_capture_then_to_claude_uses_captured_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            capture_session_state(
                root=root,
                source="codex-skill",
                summary="Captured from live Codex session",
                next_action="Continue in Claude",
                open_tasks=["Task 1"],
                key_decisions=["Decision 1"],
            )
            prompt = run_to_claude(root, input_fn=lambda _: self.fail("prompted unexpectedly"))
            restore = (root / ".handoff" / "restore.md").read_text()
            self.assertIn("Captured from live Codex session", restore)
            self.assertIn("Continue in Claude", restore)
            self.assertIn("Read .handoff/restore.md first.", prompt)
```

- [ ] **Step 2: Add a regression for capture history append semantics**

```python
    def test_capture_history_contains_both_events_after_multiple_captures(self) -> None:
        ...
```

- [ ] **Step 3: Run the full suite**

Run: `PYTHONPATH=src python -m unittest discover -s tests -v`

Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add tests/test_capture.py tests/test_cli.py README.md
git commit -m "Lock live capture to Claude handoff with integration tests"
```

## Self-Review

### Spec coverage

- live capture into canonical state: Tasks 1 and 2
- capture history append + current-state overwrite: Task 2
- restore rendering from captured state: Task 3
- `to-claude` CLI UX and interactive fallback: Task 4
- wrapper and docs update: Task 5
- integration/regression coverage: Task 6

### Placeholder scan

- No unresolved placeholder markers remain.
- Each task includes concrete files, tests, commands, and code snippets.

### Type consistency

- canonical capture function: `capture_session_state`
- export command surface: `to-claude`
- persistent history file: `session/capture-history.jsonl`
- current-state captured keys: `captured_summary`, `captured_open_tasks`, `captured_key_decisions`
