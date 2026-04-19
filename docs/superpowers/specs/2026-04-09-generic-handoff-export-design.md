# Generic Handoff Export Design

## Purpose

Design a generic handoff flow that captures live session context into the canonical `.handoff/` state and exports a structured LLM-readable handoff block that any downstream model can consume.

The system must not be Claude-specific or Codex-specific at the architectural level. It should support one-to-many handoff: the source model and the destination model may vary across Codex, Claude, Kimi, Grok, Copilot, or future tools.

## Problem Statement

The current implementation already supports:

- canonical `.handoff/` state
- optional `.omx/` imports
- checkpoint/resume refresh
- restore rendering
- a `to-claude` path that prints a Claude-oriented prompt

That is useful, but the product boundary is too target-specific. A true handoff system should not treat Claude as the defining export format, because the same structured context should be exportable to multiple downstream models.

The missing abstraction is:

- a generic live-capture surface
- a generic export command
- a generic structured handoff file for LLM consumption

## Goals

- Make the handoff architecture target-agnostic
- Keep `.handoff/` canonical
- Support one live-capture skill implementation in Codex first
- Export a generic structured LLM-readable handoff artifact
- Keep the user flow minimal and CLI-first
- Preserve honest limits around hidden model state

## Non-Goals

- Automatic shared runtime memory between tools
- Perfect session cloning across models
- Direct integration with every target model in v1
- Packaging/distribution work in this design pass

## User Promise

This feature provides a high-fidelity reconstructed handoff by:

- capturing live session context when available
- merging it into canonical `.handoff` state
- exporting a structured, model-readable handoff document

The export is generic. Specific models consume it as input, but the handoff data model is not owned by any one model vendor.

## Chosen Approach

Use a **generic core + one concrete live-capture implementation**:

- generic `$handoff` skill contract
- generic `handoff export` CLI command
- generic structured export file: `.handoff/llm-handoff.md`
- Codex live-capture skill implementation first

This keeps the architecture correct while limiting initial implementation scope.

## Product Surface

### Skill surface

The skill should be named:

- `$handoff`

This name is generic and should remain valid regardless of source or destination model.

### CLI surface

The export command should be:

```bash
PYTHONPATH=src python -m handoff.cli export --root /path/to/repo
```

In the future, packaging may make this available as:

```bash
handoff export --root /path/to/repo
```

### Export file

The canonical exported file should be:

```text
.handoff/llm-handoff.md
```

The CLI should:

- write the file
- print the same content to stdout

## Live Capture Scope

The initial live-capture implementation is Codex-only, but the contract must be generic.

That means:

- the skill behavior and state schema should not mention Codex-specific concepts except in provenance
- future Claude/Kimi/Grok/Copilot skill implementations should be able to write into the same format

## Capture Data Model

The feature builds on the existing capture-capable session model.

### Canonical files

```text
.handoff/
  session/
    current.json
    capture-history.jsonl
    live-capture.md
    conversation-tail.md   # optional
  llm-handoff.md
```

### Captured payload

Default live capture payload:

- summary
- next action
- open tasks
- key decisions

Optional with `--include-tail`:

- short recent conversation tail

### Current session shape

`session/current.json` should continue to hold the latest captured state:

```json
{
  "goal": "...",
  "status": "...",
  "next_action": "...",
  "active_mode": null,
  "timestamp": "...",
  "last_checkpoint_at": "...",
  "last_adapter_used": "raw",
  "captured_summary": "...",
  "captured_open_tasks": ["..."],
  "captured_key_decisions": ["..."]
}
```

### Capture history shape

`session/capture-history.jsonl` should append one event per capture:

```json
{
  "timestamp": "...",
  "source": "codex-skill",
  "summary": "...",
  "next_action": "...",
  "open_tasks": ["..."],
  "key_decisions": ["..."]
}
```

The `source` field is provenance, not a schema specialization.

## Human-Readable Note

The live-capture flow should also write:

```text
.handoff/session/live-capture.md
```

Suggested content:

```md
# Live Capture

## Summary
...

## Next Action
...

## Open Tasks
- ...

## Key Decisions
- ...

## Source
Captured from live session at ...
```

This file is for human inspection. It is not the source of truth.

## Export File Shape

The generic exported file should be:

```text
.handoff/llm-handoff.md
```

It should be structured, readable by humans, and easy for downstream LLMs to follow.

### Default exported sections

The default export should include:

1. Summary
2. Next Action
3. Open Tasks
4. Key Decisions
5. Constraints

This matches the approved default export payload.

### Suggested shape

```md
# LLM Handoff

## Summary
...

## Next Action
...

## Open Tasks
- ...

## Key Decisions
- ...

## Constraints
- ...

## Notes
- Use `.handoff/` as canonical state.
- Hidden model state is not portable.
```

This is intentionally generic. Claude can read it. Codex can read it. Future targets can also read it.

## Render Rules

The export should be rendered from normalized current state, not from replaying history.

### Render priority

1. `session/current.json`
   - `goal`
   - `status`
   - `next_action`
   - `captured_summary`
   - `captured_open_tasks`
   - `captured_key_decisions`

2. canonical supporting state
   - `tasks/tasks.json`
   - `memory/project-memory.json`
   - `context/constraints.json`

3. optional adapter-derived content
   - imported OMX context

### Merge rules

When exporting:

- next action comes from current state
- open tasks merge captured tasks and canonical tasks with dedup
- key decisions merge captured decisions and memory-derived decisions with dedup
- constraints come from canonical extracted constraints
- capture history is not rendered directly

## `handoff export` CLI UX

### Command

```bash
PYTHONPATH=src python -m handoff.cli export --root /path/to/repo
```

### Behavior

`handoff export` should:

1. refresh canonical state
2. determine whether the handoff state is rich enough
3. if rich enough:
   - render `.handoff/llm-handoff.md`
   - print it to stdout
4. if too sparse:
   - prompt interactively for a short summary
   - prompt for next action
   - optionally prompt for open tasks and key decisions
   - persist those values into canonical state
   - regenerate the export file
   - print it to stdout

### Richness heuristic

The state is rich enough if:

- `goal` or `captured_summary` is non-empty
- `next_action` is non-empty
- and at least one of these exists:
  - captured open tasks
  - captured key decisions
  - canonical tasks
  - project memory entries
  - imported adapter context

If not, interactive prompting is required.

### Interactive fallback

Required fields:

- summary
- next action

Optional fields:

- open tasks
- key decisions

Prompted values must be saved into canonical state, not used only transiently.

## Skill Responsibilities

The `$handoff` skill should:

- read the live session context
- summarize it into:
  - summary
  - next action
  - open tasks
  - key decisions
- update `session/current.json`
- append `capture-history.jsonl`
- write `live-capture.md`
- optionally write `conversation-tail.md` when `--include-tail` is requested
- refresh canonical state
- write `.handoff/llm-handoff.md`
- print the exported handoff text

This should be implemented first for Codex, but the contract must remain generic.

## Optional `--include-tail`

The live-capture skill should support:

- `--include-tail`

Default:

- do not capture raw conversation tail

With flag:

- write a short recent conversation tail into `.handoff/session/conversation-tail.md`

This is off by default to keep token and noise costs down.

## What This Improves

With the generic capture/export flow:

- live session context can be externalized before the session ends
- the export becomes reusable across multiple target models
- the system stops treating Claude as the defining output contract
- the handoff becomes much closer to “capture this conversation for another model”

## What Still Cannot Be Transferred Perfectly

Even with live capture:

- hidden reasoning remains non-portable
- exact context-window weighting remains non-portable
- full transcript semantics are not transferred by default
- target models still reconstruct from saved artifacts

The honest product promise remains:

- **high-fidelity reconstructed handoff**

not:

- **exact session migration**

## Risks and Mitigations

### Risk: architecture stays implicitly Claude-shaped

Mitigation:

- use generic names:
  - `$handoff`
  - `handoff export`
  - `.handoff/llm-handoff.md`

### Risk: Codex-specific capture leaks into the schema

Mitigation:

- keep source model only as provenance
- keep payload schema model-neutral

### Risk: sparse state still produces weak exports

Mitigation:

- use the richness heuristic
- prompt interactively when necessary

### Risk: note file becomes the actual state source

Mitigation:

- keep `live-capture.md` human-facing only
- render from canonical structured state

## Recommended v1 Scope

Implement:

- generic export command
- generic export file
- generic `$handoff` skill contract
- Codex live-capture implementation first
- interactive fallback
- `live-capture.md`
- optional `--include-tail`

Exclude from v1:

- multiple concrete target renderers
- packaging/distribution
- automatic Claude/Copilot-specific integration
- transcript-tail capture by default

## ADR

- **Decision:** Reframe the feature as generic capture plus generic structured export, with one concrete live-capture implementation in Codex first.
- **Drivers:** one-to-many handoff architecture, target independence, reusable file format, honest long-term design.
- **Alternatives considered:** Claude-specific prompt export; generic text only with no live skill; multi-target implementation in v1.
- **Why chosen:** best balance of correct architecture and practical delivery scope.
- **Consequences:** the current Claude-specific language should eventually be reduced in favor of generic export naming; future targets can layer on top without schema change.
- **Follow-ups:** update the implementation plan to replace `to-claude` with generic export, decide whether to rename the existing CLI now or introduce aliases first, and define the Codex skill implementation details.
