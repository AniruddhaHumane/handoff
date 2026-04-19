# portable-handoff

Portable agent-centric handoff state for cross-agent resume.

## Main Commands

- `/handoff [agent?]`
- `/get-handoff A,B`

The handoff product surface is skill-first. The only CLI is `handoff-install`, which installs the skills.

## Install Skills

From a local checkout, install into Codex with symlinks:

```bash
PYTHONPATH=src python -m handoff.install codex
```

Install into Claude with symlinks:

```bash
PYTHONPATH=src python -m handoff.install claude
```

After package or marketplace installation, the equivalent command is:

```bash
handoff-install codex
handoff-install claude
```

Use copies instead of symlinks when you do not want the installed skills to track this checkout:

```bash
handoff-install codex --mode copy
handoff-install claude --mode copy
```

Restart Codex or Claude after installing so the runtime reloads available skills.

## Purpose

Use `/handoff` to save the current live agent state under a named agent snapshot, then use `/get-handoff A,B` in a new agent session to merge one or more prior agent snapshots into a resumable context.

## Storage

```text
.handoff/
  agents/
    A/
      snapshot.json
      summary.md
  imports/
    current-get-handoff.json
    current-get-handoff.md
  shared/
    constraints.json
    project-memory.json
```

## Recommended Flow

Source agent:

```text
/handoff
```

or:

```text
/handoff A
```

Receiving agent:

```text
/get-handoff A,B
```

## Behavior

- `.handoff/agents/<agent>/` is the source of truth for per-agent snapshots
- `/get-handoff` merges named agent snapshots using newest-wins primary state
- older snapshots remain as supporting context
- hidden model state is not portable; only externalized state transfers
