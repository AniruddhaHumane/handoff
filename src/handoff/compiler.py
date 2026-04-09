from textwrap import dedent


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
