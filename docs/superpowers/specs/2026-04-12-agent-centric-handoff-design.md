# Agent-Centric Handoff Design

## Purpose

Design an agent-agnostic handoff system whose primary UX is two skills:

- `/handoff`
- `/get-handoff`

The system should let a new agent resume work from one or more prior agents with minimal user effort and maximal durable context, without relying on a user-facing CLI.

## Problem Statement

The current implementation is centered on a session-oriented canonical `.handoff/` store plus CLI commands such as `capture`, `checkpoint`, `resume`, and `export`.

That surface is useful for experimentation, but it is not the ideal product shape for a multi-agent environment:

- the user has to move in and out of CLI commands
- the current state model is oriented around one active session, not many named agents
- parallel agents risk colliding if they target one shared handoff state
- downstream agents need a direct import surface, not a manual export/paste workflow

## Goals

- Make the product surface skill-first, not CLI-first
- Make the storage model agent-centric
- Support explicit multi-agent import such as `/get-handoff A,B`
- Keep the implementation agent/runtime agnostic
- Preserve honest limits around hidden model state
- Keep the on-disk state inspectable and mergeable
- Minimize user effort for both capture and resume

## Non-Goals

- Perfect transfer of hidden model state
- Replacing git, docs, or issue trackers
- Solving workstream-level merge semantics in v1
- Supporting shared multi-writer state under one top-level session record
- Keeping the current CLI as a first-class product surface

## Chosen Strategy

Use **agent-centric snapshots** under `.handoff/agents/<agent>/`, plus a merged import artifact under `.handoff/imports/`.

### Primary user flow

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

### Identity model

Identity is **hybrid**:

- `/handoff` uses the current agent identity if the runtime already knows it
- `/handoff <agent>` may explicitly override the name
- after capture, the skill must print the resolved agent name so the user knows what to pass into `/get-handoff`
- `/get-handoff` always requires explicit source agent names

## Why Agent-Centric Instead Of Workstream-Centric

Agent-centric storage avoids multi-writer conflicts. If two agents touch the same workstream, they still write to distinct namespaces. This keeps v1 simple and makes ownership visible.

Workstream-level composition can be added later, but it should be derived from per-agent state rather than replacing it.

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

### `agents/<agent>/snapshot.json`

Canonical structured snapshot for a single named agent.

Suggested fields:

```json
{
  "agent": "A",
  "timestamp": "2026-04-12T00:00:00Z",
  "runtime": "codex",
  "summary": "What was just completed and what matters now.",
  "next_action": "Exact next step.",
  "open_tasks": ["..."],
  "key_decisions": ["..."],
  "blockers": ["..."],
  "files_touched": ["src/..."],
  "files_read_first": ["README.md", "src/..."],
  "verification": ["tests run", "checks pending"],
  "confidence": "medium",
  "uncertainties": ["..."],
  "provenance": {
    "source": "handoff-skill"
  }
}
```

### `agents/<agent>/summary.md`

Human-readable rendering of the snapshot. This is not the source of truth.

### `imports/current-get-handoff.json`

Structured merged import artifact produced by `/get-handoff`.

### `imports/current-get-handoff.md`

Compact landing document for the receiving agent. This is the first file a resumed agent should read.

## `/handoff` Skill Contract

The `/handoff` skill runs inside the current live agent session and externalizes a rich snapshot for one agent.

### Required capture fields

- summary
- next action
- open tasks
- key decisions
- blockers
- files touched
- files to read first
- verification state
- confidence / uncertainty
- timestamp
- resolved agent name

### Behavior

1. Resolve the agent name from explicit argument or session-default identity
2. Summarize the current live session into the canonical snapshot fields
3. Write `.handoff/agents/<agent>/snapshot.json`
4. Write `.handoff/agents/<agent>/summary.md`
5. Update any shared durable context if still relevant
6. Print a completion message that includes the resolved agent name

### Required completion message

The skill must end with something equivalent to:

```text
handoff saved for agent: A
```

## `/get-handoff` Skill Contract

The `/get-handoff` skill reads one or more named agent snapshots and produces one merged resume context for the current agent.

### Invocation

```text
/get-handoff A,B
```

### Behavior

1. Parse the requested source agent names
2. Read each `.handoff/agents/<agent>/snapshot.json`
3. Sort snapshots by timestamp descending
4. Produce a merged import artifact
5. Write `.handoff/imports/current-get-handoff.json`
6. Write `.handoff/imports/current-get-handoff.md`
7. Return the merged resume context

## Merge Semantics

v1 uses **newest wins** for authoritative top-level state.

That means:

- the newest snapshot becomes the primary source for scalar fields such as `summary`, `next_action`, and `confidence`
- older snapshots are not discarded; they are included as supporting context in the merged artifact
- the receiving agent sees one primary resume brief plus an appendix of older contributing agent snapshots

This keeps conflict handling simple while preserving context.

## Shared Durable Context

Some data is not inherently agent-local and should remain shared:

- extracted constraints
- durable project memory
- stable architecture notes

This shared state should live under `.handoff/shared/` and be referenced by both skills.

## Portability Boundary

### Portable with high fidelity

- explicit summaries
- next actions
- decisions
- blockers
- file references
- verification notes
- durable project memory
- instruction-derived constraints

### Partially portable

- relative salience of facts in the prior context window
- emphasis implied by the source session
- nuanced “what I was about to do” unless captured explicitly

### Not portable

- hidden model reasoning state
- opaque tool-private runtime state never written down
- exact internal pause/resume position of the source agent

## Cleanup Direction

This design intentionally retires the current CLI-first product surface. The remaining product should be:

- `/handoff`
- `/get-handoff`

Internal library code may still exist to support canonical reading, writing, and merging, but end-user docs, tests, and packaging should no longer present CLI commands as the primary interface.

## Testing Strategy

The implementation should be verified through:

- unit tests for snapshot write/read/merge behavior
- skill asset tests for `/handoff` and `/get-handoff`
- fixture-driven tests for newest-wins imports
- integration tests that simulate `A -> C` and `A + B -> C`
- cleanup tests that ensure obsolete CLI surfaces are removed from docs and packaging

## Follow-Up

The next implementation plan should:

- remove the public CLI surface
- refactor the canonical store from session-centric to agent-centric
- add the two skill assets and their installation packaging
- rewrite docs and tests around the skill-first workflow
