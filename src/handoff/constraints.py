from pathlib import Path
from typing import Any


def extract_constraints(root: Path) -> dict[str, Any]:
    sources: list[str] = []
    rules: list[str] = []
    context_files: list[dict[str, Any]] = []
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
        sources.append(str(path))
        for line in path.read_text().splitlines():
            stripped = line.strip().lstrip("-").strip()
            if stripped:
                rules.append(stripped)

    for path in sorted(root.rglob("*.md")):
        if path.name in {"AGENTS.md", "CLAUDE.md"}:
            continue

        lines = path.read_text().splitlines()
        facts = []
        for line in lines:
            stripped = line.strip().lstrip("#-").strip()
            if stripped:
                facts.append(stripped)

        if not facts:
            continue

        excerpt = " ".join(line.strip() for line in lines if line.strip())[:200]
        context_files.append(
            {
                "path": str(path),
                "excerpt": excerpt,
                "facts": facts,
            }
        )

    deduped_rules = list(dict.fromkeys(rules))
    return {
        "sources": sources,
        "rules": deduped_rules,
        "aliases": aliases,
        "context_files": context_files,
    }
