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
    summary_block = (
        f"""
## Captured Summary
{captured_summary}
"""
        if captured_summary
        else ""
    )

    return dedent(
        f"""\
        # Restore Brief

        ## Goal
        {goal}

        ## Status
        {status}
{summary_block}

        ## Constraints
        {constraint_lines}

        ## Open Tasks
        {task_lines}

        ## Important Decisions
        {decision_lines}

        ## Verification
        {verification_lines}

        ## Exact Next Action
        {next_action}

        ## Portability Boundary
        - Durable state is portable through `.handoff/`.
        - Hidden model state and opaque runtime state are not portable.
        """
    )
