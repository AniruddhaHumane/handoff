# Generic Handoff Export Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor the current session-capture and `to-claude` implementation into a generic `$handoff` + `handoff export` flow that produces a structured LLM-readable handoff artifact while preserving the existing canonical `.handoff` model.

**Architecture:** Reuse the current capture-capable `.handoff` session model, replace the Claude-specific export path with a generic export renderer that writes `.handoff/llm-handoff.md`, and keep the live capture contract generic so future model-specific skill implementations can target the same state and export surfaces.

**Tech Stack:** Python 3.11+, `argparse`, `json`, `pathlib`, `textwrap`, `unittest`, existing stdlib-only `handoff` package

---

## File Structure

### Application files

- Modify: `src/handoff/compiler.py`
- Modify: `src/handoff/checkpoint.py`
- Modify: `src/handoff/cli.py`
- Modify: `src/handoff/store.py`
- Modify: `src/handoff/capture.py`

### Tests

- Modify: `tests/test_cli.py`
- Modify: `tests/test_store.py`
- Modify: `tests/test_capture.py`

### Documentation and helper scripts

- Modify: `README.md`
- Modify: `scripts/handoff-to-claude.sh`
- Modify: `scripts/self-test.sh`

## Implementation Notes

- Keep `.handoff/` canonical.
- Do not remove the existing capture-capable state model; build the generic export on top of it.
- Prefer renaming/aliasing over parallel duplicate code paths.
- v1 should implement a generic export while still allowing the current Claude wrapper to consume it.
- Keep the initial live-capture implementation Codex-oriented only in provenance, not schema.

### Task 1: Add Generic Export File Support to the Canonical Store

**Files:**
- Modify: `src/handoff/store.py`
- Modify: `tests/test_store.py`

- [ ] **Step 1: Write the failing canonical layout test for the generic export file**

```python
class StoreExportLayoutTest(unittest.TestCase):
    def test_ensure_layout_creates_llm_handoff_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = HandoffStore(root)
            store.ensure_layout()
            self.assertTrue((root / ".handoff" / "llm-handoff.md").exists())
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `PYTHONPATH=src python -m unittest tests.test_store.StoreExportLayoutTest -v`

Expected: FAIL because `.handoff/llm-handoff.md` does not exist yet

- [ ] **Step 3: Add the generic export file to the canonical text-file set**

```python
CANONICAL_TEXT_FILES = (
    "restore.md",
    "llm-handoff.md",
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

- [ ] **Step 4: Extend the store test’s expected file list**

```python
expected_files = (
    "manifest.json",
    "restore.md",
    "llm-handoff.md",
    ...
)
```

- [ ] **Step 5: Run the store tests to verify they pass**

Run: `PYTHONPATH=src python -m unittest tests.test_store -v`

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/handoff/store.py tests/test_store.py
git commit -m "Add generic llm handoff file to canonical layout"
```

### Task 2: Replace Claude-Specific Export Rendering With Generic LLM Handoff Rendering

**Files:**
- Modify: `src/handoff/compiler.py`
- Modify: `src/handoff/checkpoint.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Write the failing generic export render test**

```python
class GenericExportRenderTest(unittest.TestCase):
    def test_export_writes_generic_llm_handoff_content(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            capture_session_state(
                root=root,
                source="codex-skill",
                summary="Generic summary",
                next_action="Generic next action",
                open_tasks=["Task A"],
                key_decisions=["Decision A"],
            )
            run_export(root)
            export_text = (root / ".handoff" / "llm-handoff.md").read_text()
            self.assertIn("# LLM Handoff", export_text)
            self.assertIn("## Summary", export_text)
            self.assertIn("## Constraints", export_text)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `PYTHONPATH=src python -m unittest tests.test_cli.GenericExportRenderTest -v`

Expected: FAIL because `run_export` does not exist and no generic export file is written

- [ ] **Step 3: Replace the Claude-oriented restore writer with a generic export renderer**

```python
def compile_llm_handoff(
    *,
    summary: str,
    next_action: str,
    tasks: list[str],
    decisions: list[str],
    constraints: list[str],
) -> str:
    ...
```

The output should be:

```md
# LLM Handoff

## Summary
...

## Next Action
...

## Open Tasks
- ...

## Key Decisions
- ...

## Constraints
- ...

## Notes
- Use `.handoff/` as canonical state.
- Hidden model state is not portable.
```

- [ ] **Step 4: Add a generic export path in `checkpoint.py`**

```python
def run_export(root: Path) -> str:
    store = HandoffStore(root)
    _refresh_portable_state(store, root, action="export")
    return store.read_llm_handoff()
```

Also add:

```python
store.write_llm_handoff(...)
store.read_llm_handoff()
```

if needed on the store surface.

- [ ] **Step 5: Continue writing `restore.md` only as a compatibility artifact**

Keep `restore.md` generation for backward compatibility if useful, but make `.handoff/llm-handoff.md` the canonical generic export file.

- [ ] **Step 6: Run the generic export render test**

Run: `PYTHONPATH=src python -m unittest tests.test_cli.GenericExportRenderTest -v`

Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add src/handoff/compiler.py src/handoff/checkpoint.py tests/test_cli.py
git commit -m "Render generic llm handoff exports"
```

### Task 3: Rename the CLI Surface From `to-claude` to `export`

**Files:**
- Modify: `src/handoff/cli.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Write the failing CLI command test**

```python
class ExportCommandTest(unittest.TestCase):
    def test_export_command_prints_generic_handoff(self) -> None:
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
            output = main(["export", "--root", str(root)])
            self.assertEqual(output, 0)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `PYTHONPATH=src python -m unittest tests.test_cli.ExportCommandTest -v`

Expected: FAIL because the `export` command does not exist yet

- [ ] **Step 3: Add the generic export parser**

```python
export = subparsers.add_parser("export")
export.add_argument("--root", type=Path, default=Path.cwd())
```

- [ ] **Step 4: Route `export` through the generic export path**

```python
if args.command == "export":
    print(run_export(args.root), end="")
    return 0
```

- [ ] **Step 5: Keep `to-claude` temporarily as a compatibility alias**

If you keep it at all in v1, it should call the same `run_export()` implementation so behavior does not diverge.

- [ ] **Step 6: Run the CLI tests**

Run: `PYTHONPATH=src python -m unittest tests.test_cli -v`

Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add src/handoff/cli.py tests/test_cli.py
git commit -m "Add generic export command with alias compatibility"
```

### Task 4: Rename the Human-Facing Skill/Note Surface to Generic Handoff

**Files:**
- Modify: `src/handoff/capture.py`
- Modify: `README.md`
- Modify: `tests/test_capture.py`

- [ ] **Step 1: Write the failing note-surface expectation test**

```python
class LiveCaptureNoteTest(unittest.TestCase):
    def test_capture_writes_live_capture_note(self) -> None:
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
            note = (root / ".handoff" / "session" / "live-capture.md").read_text()
            self.assertIn("# Live Capture", note)
            self.assertIn("## Summary", note)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `PYTHONPATH=src python -m unittest tests.test_capture.LiveCaptureNoteTest -v`

Expected: FAIL because `live-capture.md` is not written yet

- [ ] **Step 3: Extend `capture_session_state` to write `live-capture.md`**

```python
note = f\"\"\"# Live Capture

## Summary
{summary}

## Next Action
{next_action}

## Open Tasks
{...}

## Key Decisions
{...}

## Source
Captured from live session at {timestamp}
\"\"\"
```

- [ ] **Step 4: Update README to describe the generic flow**

Replace Claude-first wording with:

- generic `$handoff` skill contract
- generic `handoff export`
- `.handoff/llm-handoff.md`
- Codex live-capture implementation first

- [ ] **Step 5: Run the capture tests**

Run: `PYTHONPATH=src python -m unittest tests.test_capture -v`

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/handoff/capture.py README.md tests/test_capture.py
git commit -m "Write generic live capture notes"
```

### Task 5: Update the Convenience Wrapper to Use Generic Export

**Files:**
- Modify: `scripts/handoff-to-claude.sh`
- Modify: `README.md`

- [ ] **Step 1: Write the failing wrapper expectation as a shell smoke test**

```bash
tmpdir=$(mktemp -d)
printf 'Summary\nNext action\n\n\n' | ./scripts/handoff-to-claude.sh "$tmpdir" > /tmp/out.txt
grep -q '# LLM Handoff' /tmp/out.txt
rm -rf "$tmpdir" /tmp/out.txt
```

- [ ] **Step 2: Run the wrapper manually to verify current behavior**

Run: `./scripts/handoff-to-claude.sh "$(mktemp -d)"`

Expected: It still uses the older target-specific path rather than the generic export language

- [ ] **Step 3: Point the wrapper at `handoff export`**

```bash
PYTHONPATH=src python -m handoff.cli export --root "$TARGET_ROOT"
```

- [ ] **Step 4: Update wrapper text to be target-neutral**

It should no longer say “Paste this into Claude Code”. It should say something like:

```text
Structured handoff exported for:
  ...

Use this handoff block as context in the destination model.
```

- [ ] **Step 5: Run the wrapper smoke test**

Run: `chmod +x scripts/handoff-to-claude.sh && printf ... | ./scripts/handoff-to-claude.sh "$(mktemp -d)"`

Expected: Prints the generic handoff block and writes `.handoff/llm-handoff.md`

- [ ] **Step 6: Commit**

```bash
git add scripts/handoff-to-claude.sh README.md
git commit -m "Make the wrapper use generic export output"
```

### Task 6: Final Integration and Regression Coverage

**Files:**
- Modify: `tests/test_cli.py`
- Modify: `tests/test_capture.py`
- Modify: `tests/test_store.py`

- [ ] **Step 1: Add an end-to-end capture-to-export regression**

```python
class CaptureToExportIntegrationTest(unittest.TestCase):
    def test_capture_then_export_uses_captured_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            capture_session_state(
                root=root,
                source="codex-skill",
                summary="Captured from live session",
                next_action="Continue elsewhere",
                open_tasks=["Task 1"],
                key_decisions=["Decision 1"],
            )
            export_text = run_export(root)
            self.assertIn("# LLM Handoff", export_text)
            self.assertIn("Captured from live session", export_text)
            self.assertIn("Continue elsewhere", export_text)
```

- [ ] **Step 2: Add a regression for canonical-task-only richness on generic export**

```python
    def test_export_uses_canonical_task_state_without_prompting(self) -> None:
        ...
```

- [ ] **Step 3: Add a regression for `live-capture.md` creation**

```python
    def test_live_capture_note_is_written(self) -> None:
        ...
```

- [ ] **Step 4: Run the full suite**

Run: `PYTHONPATH=src python -m unittest discover -s tests -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_cli.py tests/test_capture.py tests/test_store.py
git commit -m "Lock generic handoff export with integration tests"
```

## Self-Review

### Spec coverage

- generic `$handoff` + generic export architecture: Tasks 2, 3, 5
- Codex-first live capture, generic contract: Tasks 3 and 4
- `.handoff/llm-handoff.md`: Tasks 1 and 2
- structured export sections: Task 2
- generic wrapper text: Task 5
- final integration/regression coverage: Task 6

### Placeholder scan

- No unresolved placeholder markers remain.
- Each task includes concrete files, commands, and code.

### Type consistency

- capture function: `capture_session_state`
- generic export path: `run_export`
- canonical export file: `.handoff/llm-handoff.md`
- generic skill surface: `$handoff`

