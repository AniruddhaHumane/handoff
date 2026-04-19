# Contributing

This branch ships the handoff skills and a shell installer.

## Branching

- Branch off `master` for skill and installer changes.
- Keep changes focused and reviewable.

## Verification

Before opening a pull request, run:

```bash
bash -n install.sh
tmp="$(mktemp -d)"
./install.sh both --home "$tmp" --mode copy
```

Then confirm these files exist:

```text
$tmp/.codex/skills/handoff/SKILL.md
$tmp/.codex/skills/get-handoff/SKILL.md
$tmp/.claude/skills/handoff/SKILL.md
$tmp/.claude/skills/get-handoff/SKILL.md
```

## Pull Requests

- Fill out the PR template.
- Include the verification you ran.
- Do not commit local `.handoff/`, `.omx/`, `.omc/`, or runtime install
  directories.
