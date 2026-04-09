# portable-handoff

Portable handoff state for cross-agent resume.

## Commands

```bash
PYTHONPATH=src python -m handoff.cli checkpoint --root /path/to/repo
PYTHONPATH=src python -m handoff.cli resume --root /path/to/repo
PYTHONPATH=src python -m handoff.cli to-claude --root /path/to/repo
```

## Self Test

```bash
chmod +x scripts/self-test.sh
./scripts/self-test.sh
```

## Codex To Claude Code Workflow

Preferred path:

1. While still in Codex, use the live capture skill if you want the highest-fidelity handoff.
2. Then run:

```bash
PYTHONPATH=src python -m handoff.cli to-claude --root /path/to/repo
```

If the current `.handoff` state is already rich enough, the command prints the Claude Code prompt immediately.

If the state is too sparse, it interactively prompts for:

- summary
- next action
- optional open tasks
- optional key decisions

and saves that data into `.handoff/session/current.json` before regenerating `restore.md`.

Current guarantees:

- `portable-handoff` persists durable context into `.handoff/`
- it can optionally import `.omx/` state during refresh
- it can generate a paste-ready Claude prompt
- it does **not** automatically inject context into Claude Code
- it does **not** transfer hidden model state, only externalized project state

## Convenience Wrapper

To refresh the handoff bundle for a target repository and print the exact prompt to paste into Claude Code:

```bash
chmod +x scripts/handoff-to-claude.sh
./scripts/handoff-to-claude.sh /path/to/repo
```

If you run it from inside the target repository, you can omit the path:

```bash
/path/to/portable-handoff/scripts/handoff-to-claude.sh
```

## Behavior

- `.handoff/` is canonical
- OMX state is imported only when available
- hidden model state is not portable
