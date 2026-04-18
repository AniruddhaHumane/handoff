import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

class HandoffStore:
    CANONICAL_DIRECTORIES = (
        "agents",
        "imports",
        "shared",
    )

    CANONICAL_JSON_FILES = (
        "shared/constraints.json",
        "shared/project-memory.json",
    )
    CANONICAL_TEXT_FILES: tuple[str, ...] = ()

    def __init__(self, root: Path) -> None:
        self.root = root
        self.base = root / ".handoff"

    def ensure_layout(self) -> None:
        timestamp = self._timestamp()

        for relative in self.CANONICAL_DIRECTORIES:
            (self.base / relative).mkdir(parents=True, exist_ok=True)

        defaults = {
            "shared/constraints.json": {"sources": [], "rules": []},
            "shared/project-memory.json": {"entries": []},
        }

        for relative, payload in defaults.items():
            path = self.base / relative
            if not path.exists():
                self._write_json(relative, payload)

        for relative in self.CANONICAL_TEXT_FILES:
            path = self.base / relative
            path.touch(exist_ok=True)

    def read_json(self, relative: str, default: dict | None = None) -> dict:
        path = self.base / relative
        if not path.exists():
            return {} if default is None else default
        return json.loads(path.read_text())

    def write_json(self, relative: str, payload: dict) -> Path:
        self._write_json(relative, payload)
        return self.base / relative

    def append_jsonl(self, relative: str, entries: list[dict]) -> Path:
        path = self.base / relative
        if not entries:
            return path
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            for entry in entries:
                handle.write(json.dumps(entry, sort_keys=True) + "\n")
        return path

    def timestamp(self) -> str:
        return self._timestamp()

    def canonical_layout_fingerprint(self) -> str:
        return self._layout_fingerprint()

    def _write_json(self, relative: str, payload: dict) -> None:
        path = self.base / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    def write_agent_snapshot(self, agent: str, payload: dict) -> Path:
        path = self.base / "agents" / agent / "snapshot.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        return path

    def read_agent_snapshot(self, agent: str) -> dict:
        path = self.base / "agents" / agent / "snapshot.json"
        if not path.exists():
            raise FileNotFoundError(f"snapshot.json not found for agent {agent}")
        return json.loads(path.read_text())

    def write_agent_summary(self, agent: str, content: str) -> Path:
        path = self.base / "agents" / agent / "summary.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        return path

    def write_import_artifacts(self, payload: dict, content: str) -> None:
        self._write_json("imports/current-get-handoff.json", payload)
        path = self.base / "imports" / "current-get-handoff.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)

    def _layout_fingerprint(self) -> str:
        entries = sorted(
            self.CANONICAL_DIRECTORIES
            + self.CANONICAL_JSON_FILES
            + self.CANONICAL_TEXT_FILES
        )
        digest = hashlib.sha256()
        digest.update("\n".join(entries).encode("utf-8"))
        return digest.hexdigest()

    def _timestamp(self) -> str:
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
