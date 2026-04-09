from pathlib import Path

from handoff.adapters.omx import OMXAdapter
from handoff.adapters.raw import RawAdapter
from handoff.capture import capture_session_state
from handoff.compiler import compile_restore
from handoff.constraints import extract_constraints
from handoff.memory import merge_project_memory
from handoff.store import HandoffStore


def run_checkpoint(root: Path) -> None:
    store = HandoffStore(root)
    _refresh_portable_state(store, root, action="checkpoint")


def run_resume(root: Path) -> str:
    store = HandoffStore(root)
    _refresh_portable_state(store, root, action="resume")
    return store.read_restore()


def run_to_claude(root: Path, *, input_fn=input) -> str:
    store = HandoffStore(root)
    _refresh_portable_state(store, root, action="resume")
    current = store.read_json("session/current.json", {})
    memory = store.read_json("memory/project-memory.json", {"entries": []})
    tasks = store.read_json("tasks/tasks.json", {"tasks": []})

    rich_enough = bool(
        (current.get("goal") or current.get("captured_summary"))
        and current.get("next_action")
        and (
            current.get("captured_open_tasks")
            or current.get("captured_key_decisions")
            or tasks.get("tasks")
            or memory.get("entries")
        )
    )

    if not rich_enough:
        summary = _require_non_empty(input_fn, "Summary: ")
        next_action = _require_non_empty(input_fn, "Next action: ")
        open_tasks = input_fn("Open tasks (comma-separated, optional): ").strip()
        key_decisions = input_fn("Key decisions (comma-separated, optional): ").strip()
        capture_session_state(
            root=root,
            source="interactive-cli",
            summary=summary,
            next_action=next_action,
            open_tasks=[item.strip() for item in open_tasks.split(",") if item.strip()],
            key_decisions=[
                item.strip() for item in key_decisions.split(",") if item.strip()
            ],
        )
        _refresh_portable_state(store, root, action="resume")

    return (
        "Read .handoff/restore.md first.\n"
        "Then use .handoff/ as the source of truth for the current goal, status, tasks, memory, and next action.\n"
        "Refresh only the files you actually need after reading the restore brief.\n"
        "Continue from the recorded next action instead of rediscovering context.\n"
    )


def _require_non_empty(input_fn, prompt: str) -> str:
    while True:
        value = input_fn(prompt).strip()
        if value:
            return value


def _refresh_portable_state(store: HandoffStore, root: Path, *, action: str) -> None:
    store.ensure_layout()
    timestamp = store.timestamp()
    constraints = extract_constraints(root)
    store.write_json(
        "context/constraints.json",
        {"sources": constraints["sources"], "rules": constraints["rules"]},
    )
    store.write_json(
        "context/instruction-aliases.json",
        {"aliases": constraints["aliases"]},
    )

    current_session = store.read_json("session/current.json", {})
    manifest = store.read_json("manifest.json", {})
    current_memory = store.read_json("memory/project-memory.json", {"entries": []})

    adapter_payloads = _capture_available_sources(root)
    active_adapter = next(
        (payload["adapter"] for payload in adapter_payloads if payload["adapter"] != "raw"),
        "raw",
    )
    omx_payload = next(
        (payload for payload in adapter_payloads if payload["adapter"] == "omx"),
        None,
    )

    merged_memory = current_memory
    merge_log: list[dict[str, str]] = []
    imported_tasks: list[str] = []
    verification = [f"Detected adapters: {', '.join(payload['adapter'] for payload in adapter_payloads)}"]

    if omx_payload is not None:
        merged_memory, merge_log = merge_project_memory(
            current_memory,
            omx_payload["project_memory"],
        )
        imported_tasks = _extract_plan_tasks(omx_payload["plans"])
        verification.append(
            f"Imported OMX project memory ({len(merge_log)} merge events)"
        )
        if omx_payload["notes"]:
            verification.append("Imported OMX notes")

    store.write_json("memory/project-memory.json", merged_memory)
    store.append_jsonl("memory/memory-merge-log.jsonl", merge_log)

    current_session["timestamp"] = timestamp
    current_session["last_adapter_used"] = active_adapter
    if action == "checkpoint":
        current_session["last_checkpoint_at"] = timestamp
    current_session.setdefault("goal", "")
    current_session.setdefault("status", "idle")
    current_session.setdefault("next_action", "")
    current_session.setdefault("active_mode", None)

    manifest["schema_version"] = manifest.get("schema_version", "1")
    manifest["active_adapter"] = active_adapter
    manifest["created_at"] = manifest.get("created_at", timestamp)
    manifest["updated_at"] = timestamp
    manifest["integrity"] = _normalize_integrity(manifest.get("integrity"), store)
    if action == "checkpoint":
        manifest["last_checkpoint_at"] = timestamp
    if action == "resume":
        manifest["last_resume_at"] = timestamp

    store.write_json("session/current.json", current_session)
    store.write_json("manifest.json", manifest)

    task_payload = store.read_json("tasks/tasks.json", {"tasks": []})
    restore = compile_restore(
        goal=current_session.get("goal", "")
        or current_session.get("captured_summary", ""),
        status=current_session.get("status") or f"{action} created",
        next_action=current_session.get("next_action") or "Resume from restore.md",
        constraints=constraints["rules"],
        tasks=_dedupe(
            current_session.get("captured_open_tasks", [])
            + task_payload.get("tasks", [])
            + imported_tasks
        ),
        decisions=_dedupe(
            current_session.get("captured_key_decisions", [])
            + _memory_values(merged_memory)
        ),
        verification=verification,
        captured_summary=current_session.get("captured_summary", ""),
    )
    store.write_restore(restore)


def _capture_available_sources(root: Path) -> list[dict[str, object]]:
    payloads = [RawAdapter(root).capture()]
    omx_adapter = OMXAdapter(root / ".omx")
    if omx_adapter.available():
        payloads.append(omx_adapter.capture())
    return payloads


def _extract_plan_tasks(plans: list[str]) -> list[str]:
    tasks: list[str] = []
    for plan in plans:
        for line in plan.splitlines():
            stripped = line.strip()
            if stripped.startswith("- "):
                tasks.append(stripped[2:])
    return _dedupe(tasks)


def _memory_values(project_memory: dict[str, object]) -> list[str]:
    values: list[str] = []
    for entry in project_memory.get("entries", []):
        value = entry.get("value")
        if isinstance(value, str) and value:
            values.append(value)
    return _dedupe(values)


def _normalize_integrity(
    integrity: object, store: HandoffStore
) -> dict[str, str]:
    normalized = integrity if isinstance(integrity, dict) else {}
    normalized["algorithm"] = "sha256"
    normalized["canonical_layout_fingerprint"] = store.canonical_layout_fingerprint()
    return normalized


def _dedupe(items: list[str]) -> list[str]:
    return list(dict.fromkeys(item for item in items if item))
