from pathlib import Path

from handoff.store import HandoffStore


def capture_session_state(
    *,
    root: Path,
    source: str,
    summary: str,
    next_action: str,
    open_tasks: list[str],
    key_decisions: list[str],
) -> None:
    store = HandoffStore(root)
    store.ensure_layout()
    timestamp = store.timestamp()

    current = store.read_json("session/current.json", {})
    current["captured_summary"] = summary
    current["captured_open_tasks"] = open_tasks
    current["captured_key_decisions"] = key_decisions
    current["next_action"] = next_action
    current["timestamp"] = timestamp
    store.write_json("session/current.json", current)

    task_lines = "\n".join(f"- {item}" for item in open_tasks) or "- None"
    decision_lines = "\n".join(f"- {item}" for item in key_decisions) or "- None"
    note = (
        "# Live Capture\n\n"
        f"## Summary\n{summary}\n\n"
        f"## Next Action\n{next_action}\n\n"
        f"## Open Tasks\n{task_lines}\n\n"
        f"## Key Decisions\n{decision_lines}\n\n"
        f"## Source\nCaptured from {source} at {timestamp}\n"
    )
    (store.base / "session" / "live-capture.md").write_text(note)

    store.append_jsonl(
        "session/capture-history.jsonl",
        [
            {
                "timestamp": timestamp,
                "source": source,
                "summary": summary,
                "next_action": next_action,
                "open_tasks": open_tasks,
                "key_decisions": key_decisions,
            }
        ],
    )
