---
name: get-handoff
description: Use when you need to resume from one or more named agent handoff snapshots such as `/get-handoff A,B`.
---

# Get Handoff

## Overview

Use `/get-handoff` to read one or more `.handoff/agents/<agent>/snapshot.json` files, merge them, and generate a resumable context for the current agent.

## When to Use

- When the user asks to resume from named prior agents
- When the workflow is `A -> C` or `A + B -> C`
- When `.handoff/agents/<agent>/` snapshots already exist

## Invocation

```text
/get-handoff A,B
```

Source agent names must be explicit.

## Workflow

1. Parse the requested source agent names.
2. Read `.handoff/agents/<agent>/snapshot.json` for each source.
3. Sort snapshots by timestamp descending.
4. Merge using newest-wins primary state.
5. Write `.handoff/imports/current-get-handoff.json`.
6. Write `.handoff/imports/current-get-handoff.md`.
7. Return the merged resume context.

## Merge Rule

- Newest timestamp wins for primary summary and next action.
- Older snapshots remain as supporting context and should not be discarded.

## Notes

- Keep the merged output compact and execution-oriented.
- If a named agent snapshot is missing, report that clearly instead of guessing.
