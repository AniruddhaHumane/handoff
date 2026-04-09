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
