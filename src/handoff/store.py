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
        "session/recent-summary.md",
        "session/conversation-tail.md",
        "session/next-action.md",
        "session/status.md",
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

        self._write_json(
            "manifest.json",
            Manifest(
                created_at=timestamp,
                updated_at=timestamp,
                integrity={
                    "algorithm": "sha256",
                    "canonical_layout_fingerprint": self._layout_fingerprint(),
                },
            ).to_dict(),
        )
        self._write_json(
            "session/current.json",
            SessionState(timestamp=timestamp).to_dict(),
        )
        self._write_json("tasks/tasks.json", {"tasks": []})
        self._write_json("plans/plan-index.json", {"active": None, "plans": []})
        self._write_json("memory/project-memory.json", {"entries": []})
        self._write_json("context/files-read.json", {"files": []})
        self._write_json("context/files-touched.json", {"files": []})
        self._write_json("context/constraints.json", {"sources": [], "rules": []})
        self._write_json("context/instruction-aliases.json", {"aliases": []})
        self._write_json("verification/checks.json", {"checks": []})

        for relative in self.CANONICAL_TEXT_FILES:
            path = self.base / relative
            path.touch(exist_ok=True)

    def _write_json(self, relative: str, payload: dict) -> None:
        path = self.base / relative
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    def _layout_fingerprint(self) -> str:
        entries = sorted(self.CANONICAL_DIRECTORIES + self.CANONICAL_JSON_FILES + self.CANONICAL_TEXT_FILES)
        digest = hashlib.sha256()
        digest.update("\n".join(entries).encode("utf-8"))
        return digest.hexdigest()

    def _timestamp(self) -> str:
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
