# portable-handoff

Portable agent handoff skills for Codex and Claude.

## What This Installs

- `/handoff [agent?]`
- `/get-handoff A,B`

The skills store portable context under `.handoff/` so one agent session can
save a concise state snapshot and another agent can resume from it.

## Install

Install into Codex:

```bash
./install.sh codex
```

Install into Claude:

```bash
./install.sh claude
```

Install into both runtimes:

```bash
./install.sh both
```

By default, the installer symlinks this checkout's skill directories so local
edits are reflected immediately. Use copies instead when you want installed
skills to remain fixed:

```bash
./install.sh both --mode copy
```

Restart Codex or Claude after installing so the runtime reloads available
skills.

## Usage

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

## Repository Layout

```text
install.sh
skills/
  handoff/
    SKILL.md
  get-handoff/
    SKILL.md
```

The previous Python package and internal planning docs are preserved on the
`python-package-docs` branch.
