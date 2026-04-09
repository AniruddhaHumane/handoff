# Session Capture to Claude Design

## Purpose

Design a high-fidelity handoff flow that captures live Codex session context into the canonical `.handoff/` state and then generates a paste-ready prompt for Claude Code.

The goal is to close the gap between:

- durable filesystem handoff already supported by `portable-handoff`
- user expectation of “hand this current conversation to Claude Code”

This feature must improve practical transfer fidelity while staying honest about the limits of cross-tool migration.

## Problem Statement

The current implementation can:

- persist `.handoff/`
- import optional `.omx/` state
- render `restore.md`
- generate a simple Claude-facing wrapper prompt

However, it cannot directly capture the current live Codex conversation or session intent unless the user manually seeds `.handoff/session/current.json`, `.handoff/tasks/tasks.json`, or `.handoff/memory/project-memory.json`.

As a result, running:

```bash
./scripts/handoff-to-claude.sh /path/to/repo
```

works mechanically but often produces a weak restore brief if the live session context was never externalized.

The missing capability is a session-aware capture step that runs while Codex still has the live conversation context.

## Goals

- Add a live-session capture surface for Codex that externalizes current conversation state into `.handoff/`
- Preserve the current tool-agnostic architecture
- Keep the user flow minimal and CLI-first
- Support interactive fallback when `.handoff` is too sparse
- Improve Codex-to-Claude transition fidelity without claiming perfect session cloning
- Persist captured context as durable state, not transient prompt-only data

## Non-Goals

- Automatic shared-memory transfer between Codex and Claude Code
- Direct runtime injection into Claude Code sessions
- Full transcript migration by default
- Perfect transfer of hidden reasoning or context-window state
- Dependence on OMX for the feature to work

## User Promise

This feature provides a high-fidelity reconstructed handoff from a live Codex session into Claude Code by capturing:

- current summary
- next action
- open tasks
- key decisions

and merging them with the existing canonical `.handoff/` state.

It does not clone hidden model state or directly restore the current Codex chat inside Claude Code.

## Chosen Approach

Use **Option A**:

- a session-aware Codex skill captures live context into `.handoff/`
- a Python CLI command `to-claude` renders the handoff prompt
- if `.handoff` is too sparse, `to-claude` prompts interactively for a short summary and saves it

This approach gives the best practical transfer fidelity while keeping the product explicit, tool-agnostic, and testable.

## Product Surface

### Primary commands

The feature introduces these user-facing surfaces:

- a Codex skill that performs live capture into `.handoff/`
- a CLI command:

```bash
PYTHONPATH=src python -m handoff.cli to-claude --root /path/to/repo
```

### Relationship between the two

- The **skill** is the high-fidelity capture path used while the live Codex session still exists.
- The **CLI** is the durable export path and fallback.
- `to-claude` must still work even if the skill was never used.
- Using the skill first should make `to-claude` materially better.

## Capture Data Model

The feature extends `.handoff/` with a small session-capture layer.

### Canonical files

```text
.handoff/
  session/
    current.json
    capture-history.jsonl
    recent-summary.md
    next-action.md
```

### Captured payload

By default, the live capture should write:

- `summary`
- `next_action`
- `open_tasks`
- `key_decisions`

This is the approved default capture payload.

### Current state shape

`session/current.json` should be extended to include:

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

This keeps capture data inside the current canonical session state rather than inventing a parallel state model.

### Capture history shape

`session/capture-history.jsonl` should append one entry per capture event:

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

The current state is overwritten with the latest capture, while history is append-only.

## Capture Behavior

The approved behavior is:

- **update current state**
- **append history**

That means each capture should:

1. overwrite the latest captured session state in `session/current.json`
2. append a structured history event to `session/capture-history.jsonl`

This provides both a clean source of truth and an audit trail.

## Render Rules

`restore.md` should render from normalized current state, not by replaying capture history.

### Render priority

The renderer should prefer:

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
   - imported OMX notes/tasks/memory

### Merge rules

When rendering:

- captured `next_action` replaces the current `next_action`
- captured `open_tasks` merge with canonical tasks using dedup
- captured `key_decisions` merge with decision-like memory values using dedup
- capture history is not rendered directly

This keeps restore output current and compact.

## `to-claude` CLI UX

### Command

```bash
PYTHONPATH=src python -m handoff.cli to-claude --root /path/to/repo
```

### Behavior

`to-claude` should:

1. read the canonical `.handoff/` state
2. determine whether the current handoff state is rich enough
3. if rich enough:
   - refresh `restore.md` if needed
   - print the paste-ready Claude prompt
4. if too sparse:
   - prompt interactively for a short summary
   - prompt for next action
   - optionally prompt for open tasks and key decisions
   - save those values into `.handoff/session/current.json`
   - append a `capture-history.jsonl` event
   - regenerate `restore.md`
   - print the Claude prompt

### “Rich enough” heuristic

The handoff state is considered good enough if:

- `goal` or `captured_summary` is non-empty
- `next_action` is non-empty
- and at least one of these exists:
  - open tasks
  - key decisions
  - project memory entries
  - adapter-imported context

If that threshold is not met, interactive prompting is required.

### Interactive fallback

When prompting is needed, the required fields are:

- summary
- next action

The optional fields are:

- open tasks
- key decisions

The approved behavior is that prompted summary content should be saved into `.handoff`, not used transiently for a one-off prompt.

## Claude Prompt Output

`to-claude` should print a paste-ready prompt block, for example:

```text
Read .handoff/restore.md first.
Then use .handoff/ as the source of truth for the current goal, status, tasks, memory, and next action.
Refresh only the files you actually need after reading the restore brief.
Continue from the recorded next action instead of rediscovering context.
```

This remains explicit and reliable. The tool should not pretend to inject state into Claude Code automatically.

## Skill Responsibilities

The session-aware Codex skill should:

- read the current live Codex session context
- summarize the current state into the approved payload:
  - summary
  - next action
  - open tasks
  - key decisions
- write the payload into `session/current.json`
- append a capture event to `capture-history.jsonl`
- regenerate `restore.md` or trigger the same canonical refresh path that `to-claude` uses

The skill should not invent a second storage surface outside `.handoff/`.

## What This Feature Can Transfer Better

With the skill-based live capture, the system can now transfer with much better fidelity:

- current objective
- current next action
- key open tasks
- key decisions from the current live conversation
- existing canonical memory and task state
- optional OMX imports

This is the best practical approximation of “current chat transfer” that fits the architecture.

## What Still Cannot Be Transferred Perfectly

Even with the skill:

- hidden reasoning remains non-portable
- exact context-window weighting remains non-portable
- full transcript semantics are not transferred by default
- Claude still starts a new session and reconstructs from saved artifacts

The product promise must remain:

- **high-fidelity reconstructed continuity**

and not:

- **perfect live session transfer**

## Risks and Mitigations

### Risk: user thinks `to-claude` transfers hidden chat state

Mitigation:

- keep docs explicit that this is a filesystem + capture handoff
- avoid language suggesting session injection or exact cloning

### Risk: duplicate or stale captured tasks and decisions

Mitigation:

- overwrite current state on each capture
- append history separately
- dedupe at render time

### Risk: sparse `.handoff` still produces weak output

Mitigation:

- add the “rich enough” heuristic
- prompt interactively when needed

### Risk: capture skill and CLI diverge

Mitigation:

- both should write into the same canonical state keys
- both should reuse the same restore refresh logic

## Recommended v1 Scope

Implement:

- session-aware Codex capture skill
- `handoff.cli to-claude`
- `capture-history.jsonl`
- `session/current.json` extensions for captured fields
- interactive fallback when state is too sparse
- persistent saving of prompted summary data
- restore rendering from captured state

Exclude from v1:

- transcript-tail capture by default
- direct Claude Code integration or launch
- automatic hook-driven capture
- multi-tool shared-memory transport

## ADR

- **Decision:** Add a live Codex capture skill plus a `to-claude` CLI command with interactive fallback.
- **Drivers:** user expectation of session handoff, higher fidelity than filesystem-only handoff, minimal-step CLI workflow, durable saved state.
- **Alternatives considered:** standalone CLI inference only; split `capture` and `to-claude` commands; shell-wrapper-only UX.
- **Why chosen:** best balance of fidelity, explicitness, and maintainability.
- **Consequences:** the system gains a session-aware surface while preserving the tool-agnostic canonical store.
- **Follow-ups:** design the exact CLI flags; define “rich enough” implementation details; add tests for interactive prompting and capture-history rendering.
