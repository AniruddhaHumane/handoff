# portable-handoff

![handoff](assets/handoff.png)

Keep coding-agent work portable, resumable, and tool-neutral.

`portable-handoff` gives Codex and Claude two small skills:

- `/handoff [agent?]` captures the current agent session into a durable snapshot.
- `/get-handoff A,B` merges one or more snapshots into a compact resume brief.

Use it when work should survive model switches, context limits, interrupted
sessions, parallel agents, or handoffs between people and tools.

## Why It Exists

Coding agents are powerful while they remember the work. They are fragile when
that memory lives only inside one chat window.

`portable-handoff` moves the important state into files:

- what the agent was trying to do
- what changed
- what still needs to happen
- what was already verified
- what constraints and decisions matter
- which files the next agent should read first

The result is a practical handoff protocol for agentic development. It does not
try to preserve hidden model state. It preserves the parts a future agent can
actually inspect, trust, and continue from.

## When To Use It

Use `portable-handoff` whenever losing context would slow the next session down.


| Situation                                          | How it helps                                                                          |
| -------------------------------------------------- | ------------------------------------------------------------------------------------- |
| Switching from Codex to Claude, or Claude to Codex | Carries the project state through `.handoff/` instead of relying on copied chat text. |
| Hitting a context limit                            | Saves a compact continuation point before the current session gets too large.         |
| Running multiple agents                            | Lets agent `C` resume from agent `A`, agent `B`, or both.                             |
| Pausing work overnight                             | Records what changed, what passed, what failed, and the next action.                  |
| Handing work to a teammate                         | Gives them a file-backed summary with decisions, blockers, and relevant files.        |
| Reviewing long-running refactors                   | Keeps cleanup intent, touched files, and verification state visible.                  |
| Debugging across tools                             | Preserves hypotheses and failed paths so the next agent does not repeat them.         |
| Working in constrained environments                | Uses plain files and agent instructions; no service or package runtime is required.   |


## Quick Start

Clone the repo, then install the skills into Codex:

```bash
./install.sh codex
```

Install into Claude:

```bash
./install.sh claude
```

Install into both:

```bash
./install.sh both
```

Restart Codex or Claude after installing so the runtime reloads available
skills.

## How The Workflow Feels

At the end of a session, ask the source agent to save a handoff:

```text
/handoff A
```

That writes:

```text
.handoff/agents/A/snapshot.json
.handoff/agents/A/summary.md
```

In a new session, ask the receiving agent to resume:

```text
/get-handoff A
```

For parallel or sequential work, merge multiple sources:

```text
/get-handoff A,B
```

The receiving agent reads the named snapshots, chooses the newest snapshot as
the primary state, keeps older snapshots as supporting context, writes import
artifacts, and returns a compact resume brief.

## What Gets Captured

The `/handoff` skill tells the agent to capture:

- current summary
- next action
- open tasks
- key decisions
- blockers
- files touched
- files to read first
- verification state
- confidence and uncertainty

That is the information future agents usually need to continue the work without
guessing.

## Storage Layout

```text
.handoff/
  agents/
    A/
      snapshot.json
      summary.md
    B/
      snapshot.json
      summary.md
  imports/
    current-get-handoff.json
    current-get-handoff.md
  shared/
    constraints.json
    project-memory.json
```

The `.handoff/` directory belongs to the project being handed off. Commit it
only when you intentionally want handoff state in version control; otherwise
keep it local.

## Install Modes

By default, the installer symlinks this checkout's skill directories into the
target runtime. That is best while developing the skills because local edits are
reflected immediately.

```bash
./install.sh both --mode symlink
```

Use copy mode when you want the installed runtime files to stay fixed even if
this checkout changes:

```bash
./install.sh both --mode copy
```

For tests or custom home directories:

```bash
./install.sh codex --home /tmp/handoff-home --mode copy
```

For custom skill sources:

```bash
./install.sh codex --source /path/to/skills --mode symlink
```

## What This Repo Ships

```text
install.sh
skills/
  handoff/
    SKILL.md
  get-handoff/
    SKILL.md
```

There is no Python package on `master`. The current product surface is the
skills plus a shell installer.

The earlier Python package, tests, and internal planning docs are preserved on
the `python-package-docs` branch for future experimentation.

## Design Principles

- Tool-neutral: snapshots are plain files, not hidden runtime state.
- Agent-readable: the next agent can inspect every piece of transferred state.
- Small by default: the handoff is concise enough to paste, review, or merge.
- Honest about limits: hidden model activations are not portable; durable state
is.
- Useful with one agent, stronger with many: single-session resume, multi-agent
merge, and human review all use the same files.

## Frequently Asked Questions

### Is this a backup of the whole chat?

No. It is a structured continuation brief. The goal is not to preserve every
token; the goal is to preserve the parts needed to continue correctly.

### Does it require Codex and Claude to agree on an API?

No. The skills tell agents how to read and write plain files. That keeps the
handoff independent of any one model or runtime.

### Can I use it with only one runtime?

Yes. It is useful even if you only use Codex or only use Claude. The main value
is making agent state explicit and resumable.

### Can I merge multiple agents' work?

Yes. `/get-handoff A,B` reads both snapshots, uses the newest snapshot for the
primary continuation state, and keeps older snapshots as supporting context.

### Should `.handoff/` be committed?

Usually no. Treat it like local session state unless your team intentionally
wants to share a handoff artifact through Git.