# portable-handoff

Portable handoff state for cross-agent resume.

## Commands

```bash
PYTHONPATH=src python -m handoff.cli checkpoint --root /path/to/repo
PYTHONPATH=src python -m handoff.cli resume --root /path/to/repo
```

## Behavior

- `.handoff/` is canonical
- OMX state is imported only when available
- hidden model state is not portable
