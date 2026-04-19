## What does this PR do?

<!-- Brief description of the skill or installer change and why it is needed. -->

## Type of change

- [ ] Skill behavior
- [ ] Installer
- [ ] Documentation
- [ ] GitHub metadata / CI
- [ ] Breaking change

## Related issues

Closes #<!-- issue number -->

## Verification

<!-- Include the commands you ran and what reviewers should check. -->

- [ ] `bash -n install.sh`
- [ ] `./install.sh both --home "$(mktemp -d)" --mode copy`
- [ ] Manually reviewed installed `SKILL.md` files

## Checklist

- [ ] The README still matches the install flow
- [ ] Skill files remain under `skills/<name>/SKILL.md`
- [ ] No local `.handoff/`, `.omx/`, `.omc/`, `.codex`, or `.claude` state is committed
