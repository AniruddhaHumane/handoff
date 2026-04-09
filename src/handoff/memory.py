from copy import deepcopy
from typing import Any


def merge_project_memory(
    current: dict[str, Any], incoming: dict[str, Any]
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    merged = deepcopy(current)
    entries = {entry["key"]: deepcopy(entry) for entry in merged.get("entries", [])}
    merge_log: list[dict[str, str]] = []

    for entry in incoming.get("entries", []):
        key = entry["key"]
        if key not in entries:
            entries[key] = deepcopy(entry)
            merge_log.append({"action": "insert", "key": key})
            continue

        existing = entries[key]
        existing_sources = list(
            dict.fromkeys(existing.get("sources", []) + entry.get("sources", []))
        )
        existing["sources"] = existing_sources
        if entry.get("updated_at", "") >= existing.get("updated_at", ""):
            existing["value"] = entry["value"]
            existing["updated_at"] = entry["updated_at"]
        merge_log.append({"action": "merge", "key": key})

    merged["entries"] = list(entries.values())
    return merged, merge_log
