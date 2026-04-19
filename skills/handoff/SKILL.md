---
name: handoff
description: Use when you need to externalize the current agent session into a named portable handoff snapshot for another agent to resume from.
---

# Handoff

## Overview

Use `/handoff` to capture the current live session into `.handoff/agents/<agent>/`.

Keep the payload model-neutral. Runtime-specific names are provenance only.

## When to Use

- Before switching from one coding agent/runtime to another
- When the user asks to "handoff", "export context", or "make this resumable elsewhere"
- When another agent will later call `/get-handoff A,B`

## Required Output

Capture these fields from the live session:

- summary
- next action
- open tasks
- key decisions
- blockers
- files touched
- files to read first
- verification state
- confidence / uncertainty

If any of those are unclear from the session, ask the user only for the missing pieces.

## Workflow

1. Resolve the agent name from `/handoff <agent>` if provided, otherwise use the current session identity.
2. Summarize the live session into the required snapshot fields.
3. Write `.handoff/agents/<agent>/snapshot.json`.
4. Write `.handoff/agents/<agent>/summary.md`.
5. End by telling the user the resolved agent name.

## Notes

- Keep the summary concise and execution-oriented.
- Use the exact completion message shape: `handoff saved for agent: <agent>`.
- The receiving side should later use `/get-handoff A,B` with explicit source agent names.
