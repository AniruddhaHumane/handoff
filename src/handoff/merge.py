from datetime import datetime, timezone


def merge_snapshots(snapshots: list[dict]) -> dict:
    if not snapshots:
        raise ValueError("At least one snapshot is required")

    ordered = sorted(snapshots, key=_timestamp_key, reverse=True)
    primary = ordered[0]
    return {
        "primary_agent": primary["agent"],
        "summary": primary["summary"],
        "next_action": primary["next_action"],
        "confidence": primary.get("confidence", "medium"),
        "sources": [item["agent"] for item in ordered],
        "open_tasks": _dedupe_from_snapshots(ordered, "open_tasks"),
        "key_decisions": _dedupe_from_snapshots(ordered, "key_decisions"),
        "blockers": _dedupe_from_snapshots(ordered, "blockers"),
        "files_touched": _dedupe_from_snapshots(ordered, "files_touched"),
        "files_read_first": _dedupe_from_snapshots(ordered, "files_read_first"),
        "verification": _dedupe_from_snapshots(ordered, "verification"),
        "uncertainties": _dedupe_from_snapshots(ordered, "uncertainties"),
        "snapshots": ordered,
    }


def _dedupe_from_snapshots(snapshots: list[dict], field: str) -> list[str]:
    values: list[str] = []
    for snapshot in snapshots:
        values.extend(snapshot.get(field, []))
    return list(dict.fromkeys(value for value in values if value))


def _timestamp_key(snapshot: dict) -> datetime:
    timestamp = snapshot["timestamp"]
    normalized = timestamp[:-1] + "+00:00" if timestamp.endswith("Z") else timestamp
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)
