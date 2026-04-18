# Agent-Centric Skills Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the CLI-first handoff product with two skill-first agent-centric workflows, `/handoff` and `/get-handoff`, backed by a canonical per-agent `.handoff/` state model.

**Architecture:** Refactor the current session-centric store into an internal agent-centric library that reads and writes `.handoff/agents/<agent>/` snapshots and compiles `.handoff/imports/current-get-handoff.*` artifacts. Remove public CLI commands, wrappers, and CLI-focused tests/docs. Ship two skill assets that become the only intended end-user surface.

**Tech Stack:** Python 3.11 stdlib, existing `handoff` package modules, markdown skill assets, `unittest`

---

### Task 1: Lock The New Public Surface And Cleanup Direction

**Files:**
- Modify: `tests/test_skill.py`
- Create: `tests/test_agent_handoff_store.py`
- Create: `tests/test_get_handoff_merge.py`
- Delete: `tests/test_cli.py`
- Delete: `tests/test_packaging.py`
- Delete: `tests/test_feature_verifier.py`

- [ ] **Step 1: Write the failing skill-surface test**

Add a test that asserts the repo ships both skill assets and that they reference the new commands:

```python
class SkillSurfaceTest(unittest.TestCase):
    def test_repo_ships_handoff_and_get_handoff_skills(self) -> None:
        repo = Path(__file__).resolve().parents[1]
        handoff = repo / "skills" / "handoff" / "SKILL.md"
        get_handoff = repo / "skills" / "get-handoff" / "SKILL.md"

        self.assertTrue(handoff.exists())
        self.assertTrue(get_handoff.exists())
        self.assertIn("/handoff", handoff.read_text())
        self.assertIn("/get-handoff", get_handoff.read_text())
```

- [ ] **Step 2: Write the failing store-layout test**

Add a test that expects agent-centric layout initialization:

```python
class AgentStoreLayoutTest(unittest.TestCase):
    def test_ensure_layout_creates_agent_and_import_roots(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = HandoffStore(Path(tmp))
            store.ensure_layout()

            self.assertTrue((Path(tmp) / ".handoff" / "agents").exists())
            self.assertTrue((Path(tmp) / ".handoff" / "imports").exists())
            self.assertTrue((Path(tmp) / ".handoff" / "shared").exists())
```

- [ ] **Step 3: Write the failing merge test**

Add a test that seeds two snapshots and expects newest-wins primary state:

```python
class GetHandoffMergeTest(unittest.TestCase):
    def test_newest_snapshot_wins_primary_fields(self) -> None:
        merged = merge_snapshots([older_snapshot, newer_snapshot])

        self.assertEqual(merged["primary_agent"], "B")
        self.assertEqual(merged["summary"], "new summary")
        self.assertIn("A", merged["sources"])
        self.assertIn("B", merged["sources"])
```

- [ ] **Step 4: Run the focused tests to verify RED**

Run:

```bash
python -m unittest \
  tests.test_skill \
  tests.test_agent_handoff_store \
  tests.test_get_handoff_merge -v
```

Expected: FAIL because the repo still ships the CLI-first surface and the agent-centric store/merge APIs do not exist yet.

### Task 2: Refactor The Canonical Store To Agent-Centric State

**Files:**
- Modify: `src/handoff/store.py`
- Modify: `src/handoff/models.py`
- Modify: `src/handoff/capture.py`
- Create: `src/handoff/merge.py`
- Test: `tests/test_agent_handoff_store.py`
- Test: `tests/test_get_handoff_merge.py`

- [ ] **Step 1: Replace the session-centric canonical layout**

Update the store constants so the canonical layout is:

```python
CANONICAL_DIRECTORIES = (
    "agents",
    "imports",
    "shared",
)

CANONICAL_JSON_FILES = (
    "shared/constraints.json",
    "shared/project-memory.json",
)

CANONICAL_TEXT_FILES = ()
```

- [ ] **Step 2: Add explicit agent snapshot helpers**

Implement store methods with this shape:

```python
def write_agent_snapshot(self, agent: str, payload: dict) -> Path: ...
def read_agent_snapshot(self, agent: str) -> dict: ...
def write_agent_summary(self, agent: str, content: str) -> Path: ...
def write_import_artifacts(self, payload: dict, content: str) -> None: ...
```

- [ ] **Step 3: Define the new snapshot model**

Add or update model helpers for:

```python
{
    "agent": "A",
    "timestamp": "...",
    "runtime": "codex",
    "summary": "...",
    "next_action": "...",
    "open_tasks": [],
    "key_decisions": [],
    "blockers": [],
    "files_touched": [],
    "files_read_first": [],
    "verification": [],
    "confidence": "medium",
    "uncertainties": [],
    "provenance": {"source": "handoff-skill"}
}
```

- [ ] **Step 4: Implement newest-wins merge**

Create `src/handoff/merge.py` with a minimal merge function:

```python
def merge_snapshots(snapshots: list[dict]) -> dict:
    ordered = sorted(snapshots, key=lambda item: item["timestamp"], reverse=True)
    primary = ordered[0]
    return {
        "primary_agent": primary["agent"],
        "summary": primary["summary"],
        "next_action": primary["next_action"],
        "sources": [item["agent"] for item in ordered],
        "snapshots": ordered,
    }
```

- [ ] **Step 5: Run focused tests to verify GREEN**

Run:

```bash
python -m unittest \
  tests.test_agent_handoff_store \
  tests.test_get_handoff_merge -v
```

Expected: PASS

### Task 3: Implement The Internal Handoff And Get-Handoff Compilers

**Files:**
- Modify: `src/handoff/compiler.py`
- Modify: `src/handoff/capture.py`
- Create: `tests/test_handoff_rendering.py`

- [ ] **Step 1: Write the failing rendering test**

Add a test that expects one per-agent summary and one merged import brief:

```python
class HandoffRenderingTest(unittest.TestCase):
    def test_compile_get_handoff_render_contains_primary_and_appendix(self) -> None:
        text = compile_get_handoff_markdown(merged_payload)

        self.assertIn("# Get Handoff", text)
        self.assertIn("## Primary Context", text)
        self.assertIn("## Additional Agent Snapshots", text)
```

- [ ] **Step 2: Implement per-agent summary rendering**

Add a function similar to:

```python
def compile_agent_summary(snapshot: dict) -> str:
    return (
        f"# Agent Handoff: {snapshot['agent']}\n\n"
        f"## Summary\n{snapshot['summary']}\n\n"
        f"## Next Action\n{snapshot['next_action']}\n"
    )
```

- [ ] **Step 3: Implement merged import rendering**

Add a function similar to:

```python
def compile_get_handoff_markdown(payload: dict) -> str:
    primary = payload["snapshots"][0]
    return (
        "# Get Handoff\n\n"
        f"## Primary Context\nAgent: {primary['agent']}\n\n"
        f"## Summary\n{primary['summary']}\n\n"
        "## Additional Agent Snapshots\n"
    )
```

- [ ] **Step 4: Run rendering tests**

Run:

```bash
python -m unittest tests.test_handoff_rendering -v
```

Expected: PASS

### Task 4: Replace The Product Surface With Two Skills

**Files:**
- Modify: `skills/handoff/SKILL.md`
- Create: `skills/get-handoff/SKILL.md`
- Modify: `src/handoff/assets/handoff/SKILL.md`
- Create: `src/handoff/assets/get-handoff/SKILL.md`
- Test: `tests/test_skill.py`

- [ ] **Step 1: Rewrite the `/handoff` skill around direct snapshot capture**

Replace CLI instructions with a skill contract that:

- resolves the agent name from explicit arg or current session identity
- summarizes the live session into snapshot fields
- writes `.handoff/agents/<agent>/snapshot.json`
- writes `.handoff/agents/<agent>/summary.md`
- prints `handoff saved for agent: <agent>`

- [ ] **Step 2: Create the `/get-handoff` skill**

Create a skill that:

- accepts explicit source agent names
- reads `.handoff/agents/<agent>/snapshot.json` for each source
- merges by newest timestamp
- writes `.handoff/imports/current-get-handoff.json`
- writes `.handoff/imports/current-get-handoff.md`
- returns the merged context

- [ ] **Step 3: Mirror the skill assets under `src/handoff/assets/`**

Ensure packaged assets match repo-local skill docs exactly.

- [ ] **Step 4: Run skill tests**

Run:

```bash
python -m unittest tests.test_skill -v
```

Expected: PASS

### Task 5: Remove The Public CLI Surface And Obsolete Tooling

**Files:**
- Delete: `src/handoff/cli.py`
- Delete: `src/handoff/install.py`
- Delete: `scripts/handoff-to-claude.sh`
- Delete: `scripts/self-test.sh`
- Delete: `scripts/verify-features.sh`
- Modify: `pyproject.toml`
- Modify: `README.md`

- [ ] **Step 1: Remove the console script entrypoint**

Delete the script entrypoint from `pyproject.toml`:

```toml
[project.scripts]
handoff = "handoff.cli:main"
```

- [ ] **Step 2: Remove CLI-only modules and wrappers**

Delete:

```text
src/handoff/cli.py
src/handoff/install.py
scripts/handoff-to-claude.sh
scripts/self-test.sh
scripts/verify-features.sh
```

- [ ] **Step 3: Rewrite README around the two skills only**

The new top-level README should present only this UX:

```md
## Main Commands

- `/handoff [agent?]`
- `/get-handoff A,B`
```

- [ ] **Step 4: Verify the cleanup with a grep-based regression**

Run:

```bash
rg -n "handoff export|handoff capture|install-skill|to-claude|python -m handoff.cli" README.md skills src tests
```

Expected: no product-surface references remain outside historical docs.

### Task 6: Add End-To-End Agent Handoff Integration Tests

**Files:**
- Create: `tests/test_agent_handoff_integration.py`
- Modify: `tests/test_capture.py`
- Modify: `tests/test_store.py`

- [ ] **Step 1: Write the `A -> C` integration test**

Add a test that writes a snapshot for `A`, then reads it through the import path:

```python
class AgentHandoffIntegrationTest(unittest.TestCase):
    def test_single_agent_get_handoff_uses_that_agent_as_primary(self) -> None:
        store.write_agent_snapshot("A", snapshot_a)
        merged = merge_snapshots([store.read_agent_snapshot("A")])

        self.assertEqual(merged["primary_agent"], "A")
```

- [ ] **Step 2: Write the `A + B -> C` integration test**

Add a test that writes `A` and `B` snapshots and expects `B` to win when newer:

```python
def test_multi_agent_get_handoff_uses_newest_snapshot_as_primary(self) -> None:
    store.write_agent_snapshot("A", older)
    store.write_agent_snapshot("B", newer)
    merged = merge_snapshots([store.read_agent_snapshot("A"), store.read_agent_snapshot("B")])

    self.assertEqual(merged["primary_agent"], "B")
```

- [ ] **Step 3: Run the integration tests**

Run:

```bash
python -m unittest tests.test_agent_handoff_integration -v
```

Expected: PASS

### Task 7: Run The Full Verification Pass

**Files:**
- Modify: `README.md`
- Modify: `tests/*` as needed

- [ ] **Step 1: Run the full test suite**

Run:

```bash
python -m unittest discover -s tests -v
```

Expected: PASS

- [ ] **Step 2: Run the cleanup grep**

Run:

```bash
rg -n "handoff export|handoff capture|install-skill|to-claude|python -m handoff.cli" README.md skills src tests
```

Expected: no matches outside archived planning/spec documents.

- [ ] **Step 3: Record the final product boundary**

Before finishing, confirm the shipped UX is only:

- `/handoff [agent?]`
- `/get-handoff A,B`

Anything else should be either deleted or clearly marked as internal/non-product code.

## Spec Coverage Check

- Agent-centric storage: Task 2
- `/handoff` skill with resolved agent name: Task 4
- `/get-handoff A,B` merge/import path: Tasks 2, 3, 4, 6
- Newest-wins semantics: Tasks 2 and 6
- CLI removal and cleanup: Task 5
- Skill-first docs/tests: Tasks 1, 4, 5, 7

## Placeholder Scan

No placeholder behavior is left unspecified:

- store layout is explicit
- snapshot fields are explicit
- merge rule is explicit
- cleanup targets are explicit
- verification commands are explicit
