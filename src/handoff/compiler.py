from textwrap import dedent


def compile_agent_summary(snapshot: dict) -> str:
    sections = [
        f"# Agent Handoff: {snapshot['agent']}",
        "",
        "## Summary",
        snapshot.get("summary", ""),
        "",
        "## Next Action",
        snapshot.get("next_action", ""),
    ]
    return dedent("\n".join(sections) + "\n")


def compile_get_handoff_markdown(payload: dict) -> str:
    primary = payload["snapshots"][0]
    open_tasks = "\n".join(f"- {item}" for item in payload.get("open_tasks", [])) or "- None"
    decisions = "\n".join(f"- {item}" for item in payload.get("key_decisions", [])) or "- None"
    blockers = "\n".join(f"- {item}" for item in payload.get("blockers", [])) or "- None"
    files_read_first = "\n".join(f"- {item}" for item in payload.get("files_read_first", [])) or "- None"
    verification = "\n".join(f"- {item}" for item in payload.get("verification", [])) or "- None"
    project_memory = "\n".join(f"- {item}" for item in payload.get("project_memory", [])) or "- None"
    appendix_lines = []
    for snapshot in payload["snapshots"][1:]:
        appendix_lines.extend(
            [
                f"### Agent: {snapshot['agent']}",
                snapshot.get("summary", ""),
                "",
                f"Next: {snapshot.get('next_action', '')}",
                "",
            ]
        )

    if not appendix_lines:
        appendix_lines = ["- None"]

    sections = [
        "# Get Handoff",
        "",
        "## Primary Context",
        f"Agent: {primary['agent']}",
        "",
        "## Summary",
        primary.get("summary", ""),
        "",
        "## Next Action",
        primary.get("next_action", ""),
        "",
        "## Open Tasks",
        open_tasks,
        "",
        "## Key Decisions",
        decisions,
        "",
        "## Blockers",
        blockers,
        "",
        "## Files To Read First",
        files_read_first,
        "",
        "## Verification",
        verification,
        "",
        "## Shared Project Memory",
        project_memory,
        "",
        "## Additional Agent Snapshots",
        *appendix_lines,
    ]
    return dedent("\n".join(sections) + "\n")


def compile_restore(
    *,
    goal: str,
    status: str,
    next_action: str,
    constraints: list[str],
    tasks: list[str],
    decisions: list[str],
    verification: list[str],
    captured_summary: str = "",
) -> str:
    constraint_lines = "\n".join(f"- {item}" for item in constraints) or "- None"
    task_lines = "\n".join(f"- {item}" for item in tasks) or "- None"
    decision_lines = "\n".join(f"- {item}" for item in decisions) or "- None"
    verification_lines = "\n".join(f"- {item}" for item in verification) or "- None"
    sections = [
        "# Restore Brief",
        "",
        "## Goal",
        goal,
        "",
        "## Status",
        status,
    ]

    if captured_summary:
        sections.extend(
            [
                "",
                "## Captured Summary",
                captured_summary,
            ]
        )

    sections.extend(
        [
            "",
            "## Constraints",
            constraint_lines,
            "",
            "## Open Tasks",
            task_lines,
            "",
            "## Important Decisions",
            decision_lines,
            "",
            "## Verification",
            verification_lines,
            "",
            "## Exact Next Action",
            next_action,
            "",
            "## Portability Boundary",
            "- Durable state is portable through `.handoff/`.",
            "- Hidden model state and opaque runtime state are not portable.",
        ]
    )

    return dedent("\n".join(sections) + "\n")


def compile_llm_handoff(
    *,
    summary: str,
    next_action: str,
    tasks: list[str],
    decisions: list[str],
    constraints: list[str],
) -> str:
    task_lines = "\n".join(f"- {item}" for item in tasks) or "- None"
    decision_lines = "\n".join(f"- {item}" for item in decisions) or "- None"
    constraint_lines = "\n".join(f"- {item}" for item in constraints) or "- None"

    sections = [
        "# LLM Handoff",
        "",
        "## Summary",
        summary,
        "",
        "## Next Action",
        next_action,
        "",
        "## Open Tasks",
        task_lines,
        "",
        "## Key Decisions",
        decision_lines,
        "",
        "## Constraints",
        constraint_lines,
        "",
        "## Notes",
        "- Use `.handoff/` as canonical state.",
        "- Hidden model state is not portable.",
    ]
    return dedent("\n".join(sections) + "\n")
