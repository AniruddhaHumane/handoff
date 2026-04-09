import json
from pathlib import Path
from typing import Any

from handoff.adapters.base import read_text


class OMXAdapter:
    name = "omx"

    def __init__(self, root: Path) -> None:
        self.root = root

    def available(self) -> bool:
        return (self.root / "notepad.md").exists()

    def capture(self) -> dict[str, Any]:
        plans_dir = self.root / "plans"
        plan_paths = sorted(plans_dir.glob("*.md")) if plans_dir.exists() else []

        session_path = self.root / "state" / "session.json"
        session = json.loads(read_text(session_path)) if session_path.exists() else {}

        project_memory_path = self.root / "project-memory.json"
        project_memory = (
            json.loads(read_text(project_memory_path))
            if project_memory_path.exists()
            else {"entries": []}
        )

        return {
            "adapter": self.name,
            "notes": read_text(self.root / "notepad.md"),
            "plans": [read_text(path) for path in plan_paths],
            "session": session,
            "project_memory": project_memory,
        }
