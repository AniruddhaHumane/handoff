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
    store.write_restore(restore)


def run_resume(root: Path) -> str:
    store = HandoffStore(root)
    return store.read_restore()
