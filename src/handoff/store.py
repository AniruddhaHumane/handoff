import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from handoff.models import Manifest, SessionState


class HandoffStore:
    CANONICAL_DIRECTORIES = (
        "session",
        "tasks",
        "plans",
        "memory",
        "context",
        "verification",
        "artifacts",
        "artifacts/exports",
        "artifacts/imports",
    )

    CANONICAL_JSON_FILES = (
        "manifest.json",
        "session/current.json",
        "tasks/tasks.json",
        "plans/plan-index.json",
        "memory/project-memory.json",
        "context/files-read.json",
        "context/files-touched.json",
        "context/constraints.json",
        "context/instruction-aliases.json",
        "verification/checks.json",
    )

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

    def __init__(self, root: Path) -> None:
        self.root = root
        self.base = root / ".handoff"

    def ensure_layout(self) -> None:
        timestamp = self._timestamp()

        for relative in self.CANONICAL_DIRECTORIES:
            (self.base / relative).mkdir(parents=True, exist_ok=True)

        defaults = {
            "manifest.json": Manifest(
                created_at=timestamp,
                updated_at=timestamp,
                integrity={
                    "algorithm": "sha256",
                    "canonical_layout_fingerprint": self._layout_fingerprint(),
                },
            ).to_dict(),
            "session/current.json": SessionState(timestamp=timestamp).to_dict(),
            "tasks/tasks.json": {"tasks": []},
            "plans/plan-index.json": {"active": None, "plans": []},
            "memory/project-memory.json": {"entries": []},
            "context/files-read.json": {"files": []},
            "context/files-touched.json": {"files": []},
            "context/constraints.json": {"sources": [], "rules": []},
            "context/instruction-aliases.json": {"aliases": []},
            "verification/checks.json": {"checks": []},
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
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    def write_restore(self, restore: str) -> Path:
        path = self.base / "restore.md"
        path.write_text(restore)
        return path

    def write_llm_handoff(self, content: str) -> Path:
        path = self.base / "llm-handoff.md"
        path.write_text(content)
        return path

    def read_restore(self) -> str:
        path = self.base / "restore.md"
        if not path.exists():
            raise FileNotFoundError("restore.md not found")
        return path.read_text()

    def read_llm_handoff(self) -> str:
        path = self.base / "llm-handoff.md"
        if not path.exists():
            raise FileNotFoundError("llm-handoff.md not found")
        return path.read_text()

    def _layout_fingerprint(self) -> str:
        entries = sorted(self.CANONICAL_DIRECTORIES + self.CANONICAL_JSON_FILES + self.CANONICAL_TEXT_FILES)
        digest = hashlib.sha256()
        digest.update("\n".join(entries).encode("utf-8"))
        return digest.hexdigest()

    def _timestamp(self) -> str:
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
