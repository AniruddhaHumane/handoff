# portable-handoff

Portable handoff state for cross-agent resume.

## Commands

```bash
PYTHONPATH=src python -m handoff.cli checkpoint --root /path/to/repo
PYTHONPATH=src python -m handoff.cli resume --root /path/to/repo
PYTHONPATH=src python -m handoff.cli export --root /path/to/repo
```

## Self Test

```bash
chmod +x scripts/self-test.sh
./scripts/self-test.sh
```

## Generic Handoff Workflow

Preferred path:

1. While still in the source model session, use the `$handoff` live capture skill when available.
2. Then run:

```bash
PYTHONPATH=src python -m handoff.cli export --root /path/to/repo
```

This writes `.handoff/llm-handoff.md` and prints the same structured handoff block to stdout.

If the current `.handoff` state is already rich enough, export prints immediately.

If the state is too sparse, it interactively prompts for:

- summary
- next action
- optional open tasks
- optional key decisions

and saves that data into `.handoff/session/current.json` before regenerating the export.

Current guarantees:

- `portable-handoff` persists durable context into `.handoff/`
- it can optionally import `.omx/` state during refresh
- it can generate a generic structured LLM-readable handoff block
- it does **not** automatically inject context into another model runtime
- it does **not** transfer hidden model state, only externalized project state

## Compatibility Wrapper

The existing wrapper is still available for compatibility while the product surface migrates:

```bash
chmod +x scripts/handoff-to-claude.sh
./scripts/handoff-to-claude.sh /path/to/repo
```

It now delegates to the same generic export path.

## Behavior

- `.handoff/` is canonical
- OMX state is imported only when available
- hidden model state is not portable
