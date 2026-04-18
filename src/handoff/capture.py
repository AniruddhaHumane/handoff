from pathlib import Path
from typing import Mapping

from handoff.compiler import compile_agent_summary, compile_get_handoff_markdown
from handoff.constraints import extract_constraints
from handoff.merge import merge_snapshots
from handoff.memory import merge_project_memory
from handoff.store import HandoffStore


def capture_agent_handoff(
    *,
    root: Path,
    agent: str,
    runtime: str,
    source: str,
    summary: str,
    next_action: str,
    open_tasks: list[str],
    key_decisions: list[str],
    blockers: list[str] | None = None,
    files_touched: list[str] | None = None,
    files_read_first: list[str] | None = None,
    verification: list[str] | None = None,
    confidence: str = "medium",
    uncertainties: list[str] | None = None,
) -> dict:
    store = HandoffStore(root)
    store.ensure_layout()
    timestamp = store.timestamp()

    snapshot = {
        "agent": agent,
        "timestamp": timestamp,
        "runtime": runtime,
        "summary": summary,
        "next_action": next_action,
        "open_tasks": open_tasks,
        "key_decisions": key_decisions,
        "blockers": blockers or [],
        "files_touched": files_touched or [],
        "files_read_first": files_read_first or [],
        "verification": verification or [],
        "confidence": confidence,
        "uncertainties": uncertainties or [],
        "provenance": {"source": source},
    }
    store.write_agent_snapshot(agent, snapshot)
    store.write_agent_summary(agent, compile_agent_summary(snapshot))
    return snapshot


def get_handoff(root: Path, source_agents: list[str]) -> dict:
    store = HandoffStore(root)
    store.ensure_layout()
    snapshots = [store.read_agent_snapshot(agent) for agent in source_agents]
    merged = merge_snapshots(snapshots)
    markdown = compile_get_handoff_markdown(merged)
    store.write_import_artifacts(merged, markdown)
    return merged


def resolve_agent_name(
    *,
    explicit_agent: str | None,
    default_agent: str | None = None,
    env: Mapping[str, str] | None = None,
) -> str:
    if explicit_agent:
        return explicit_agent
    if default_agent:
        return default_agent
    if env is not None and env.get("HANDOFF_AGENT"):
        return env["HANDOFF_AGENT"]
    raise ValueError("Agent name could not be resolved")


def run_handoff(
    *,
    root: Path,
    explicit_agent: str | None,
    default_agent: str | None,
    runtime: str,
    source: str,
    summary: str,
    next_action: str,
    open_tasks: list[str],
    key_decisions: list[str],
    blockers: list[str] | None = None,
    files_touched: list[str] | None = None,
    files_read_first: list[str] | None = None,
    verification: list[str] | None = None,
    confidence: str = "medium",
    uncertainties: list[str] | None = None,
    incoming_project_memory: dict | None = None,
    env: Mapping[str, str] | None = None,
) -> str:
    agent = resolve_agent_name(
        explicit_agent=explicit_agent,
        default_agent=default_agent,
        env=env,
    )
    store = HandoffStore(root)
    store.ensure_layout()

    constraints = extract_constraints(root)
    store.write_json(
        "shared/constraints.json",
        {"sources": constraints["sources"], "rules": constraints["rules"]},
    )

    if incoming_project_memory is not None:
        current_memory = store.read_json("shared/project-memory.json", {"entries": []})
        merged_memory, _ = merge_project_memory(current_memory, incoming_project_memory)
        store.write_json("shared/project-memory.json", merged_memory)

    capture_agent_handoff(
        root=root,
        agent=agent,
        runtime=runtime,
        source=source,
        summary=summary,
        next_action=next_action,
        open_tasks=open_tasks,
        key_decisions=key_decisions,
        blockers=blockers,
        files_touched=files_touched,
        files_read_first=files_read_first,
        verification=verification,
        confidence=confidence,
        uncertainties=uncertainties,
    )
    return f"handoff saved for agent: {agent}"


def run_get_handoff(*, root: Path, source_agents: list[str]) -> str:
    store = HandoffStore(root)
    store.ensure_layout()
    merged = get_handoff(root, source_agents)

    constraints = store.read_json("shared/constraints.json", {"rules": []})
    project_memory = store.read_json("shared/project-memory.json", {"entries": []})
    merged["constraints"] = constraints.get("rules", [])
    ordered_memory = sorted(
        project_memory.get("entries", []),
        key=lambda entry: entry.get("updated_at", ""),
        reverse=True,
    )
    merged["project_memory"] = [
        entry["value"]
        for entry in ordered_memory
        if isinstance(entry.get("value"), str) and entry["value"]
    ]

    markdown = compile_get_handoff_markdown(merged)
    store.write_import_artifacts(merged, markdown)
    return markdown
