# Portable Handoff Design

## Purpose

Design a tool-agnostic handoff system that lets one coding agent session stop and another resume with high-fidelity project continuity across Claude Code, Codex, and similar tools.

The system is intended to preserve durable project context with low token overhead. It must be usable without OMX/OMC, while taking advantage of OMX/OMC if available.

## Problem Statement

Current agent sessions hold important context in a mix of:

- chat history
- hidden model state
- local files
- runtime-specific session state
- repo metadata

This makes cross-tool resume unreliable. A user can often recover files and plans, but not the current working state, recent decisions, verification status, or the exact next step. The result is token waste, repeated discovery, and inconsistent execution after migration.

## Goals

- Preserve durable session context across tools with low ongoing token cost.
- Make the system tool-agnostic by default.
- Support richer import when OMX/OMC is installed.
- Distinguish clearly between state that can be migrated with high fidelity and state that cannot.
- Keep the source of truth on disk in a canonical, inspectable format.
- Support explicit checkpoint/restore and low-cost always-on structured sync.

## Non-Goals

- Perfect cloning of hidden model state.
- Bit-for-bit recreation of a prior context window.
- Dependence on any one runtime or plugin ecosystem.
- Continuous full-transcript summarization.
- Replacing git, issue trackers, or formal documentation systems.

## User Promise

This system migrates durable project state, structured execution context, project memory, and recent conversational context across tools.

It does not clone opaque internal model state, hidden reasoning state, or tool-private runtime context that was never externalized.

If richer local tooling is available, adapters improve fidelity. Otherwise the system falls back to canonical raw state stored in the repository.

## Migration Guarantees

### High-fidelity portable state

These can be migrated nearly exactly if written into the handoff system:

- current goal
- current status
- exact next action
- task list
- active plan
- decisions and rationale
- verification state
- files read
- files touched
- repo metadata
- extracted constraints from instruction files
- project memory entries
- recent conversation summary
- short raw conversation tail

### Reconstructed state

These can be reconstructed, but not perfectly preserved:

- “what mattered most” in the prior context window
- ordering or emphasis inferred from summaries
- current mode inferred from adapter state
- active file priority inferred from recent reads/touches

### Non-portable state

These cannot be migrated perfectly:

- hidden model reasoning state
- exact context-window weighting and salience
- tool-runtime-private state that was never externalized
- private subagent cognition unless explicitly saved
- exact pause/resume semantics at the internal model level

## Design Principles

1. Canonical files over hidden memory
2. Tool-agnostic core, optional adapters
3. Low steady-state token cost
4. Explicit provenance for imported state
5. Replace session-local state, merge stable project memory
6. Recompute constraints from live files when possible
7. Keep restore surfaces compact and human-auditable

## Chosen Architecture

Use a tool-agnostic canonical handoff store under `.handoff/`, plus optional adapters.

### Core model

The canonical model is split into:

- session state
- execution state
- project memory
- instruction constraints
- provenance

### Runtime model

The runtime uses:

- always-on structured sync for small, durable state
- explicit checkpoint bundles for cross-tool migration
- on-demand restore packet generation

### Adapter model

Adapters are optional import/export helpers. They enrich fidelity but never become the source of truth.

v1 includes:

- raw filesystem adapter
- OMX/OMC adapter

Future adapters may include:

- Claude Code-specific metadata import
- Codex-specific metadata import
- external issue/PR/task systems

## Canonical Storage Layout

The canonical root is:

```text
.handoff/
  restore.md
  manifest.json
  session/
    current.json
    recent-summary.md
    conversation-tail.md
    next-action.md
    status.md
  tasks/
    tasks.json
  plans/
    active-plan.md
    plan-index.json
  memory/
    project-memory.json
    memory-merge-log.jsonl
  context/
    files-read.json
    files-touched.json
    constraints.json
    instruction-aliases.json
  verification/
    verification.md
    checks.json
  artifacts/
    exports/
    imports/
```

## File Semantics

### `restore.md`

The single cross-tool landing file. A new tool should read this first.

It should contain:

- current goal
- current status
- active constraints
- active plan
- open tasks
- important decisions
- files to read first
- verification state
- exact next action
- portability guarantees and limits

### `manifest.json`

Schema versioning, timestamps, active adapter information, and integrity metadata.

### `session/current.json`

Current session-local state:

- goal
- status
- active mode if known
- timestamp
- last checkpoint time
- last adapter used

### `session/recent-summary.md`

Compact semantic summary of recent work, intended to be cheap to read and regenerate.

### `session/conversation-tail.md`

Short raw tail of recent conversation plus minimal annotations. This exists for nuance continuity, not as a full transcript archive.

### `session/next-action.md`

One exact next step for the next tool or operator.

### `tasks/tasks.json`

Canonical task list and status tracking. This should be the structured source for open/completed/in-progress tasks.

### `plans/active-plan.md`

The active plan or a normalized extract of the active plan. The underlying source plan may still live elsewhere.

### `plans/plan-index.json`

References to known plan/spec artifacts and which one is active.

### `memory/project-memory.json`

Long-term reusable project memory:

- architecture notes
- conventions
- stable gotchas
- repeated decisions worth preserving
- durable environment facts

### `memory/memory-merge-log.jsonl`

Append-only log of imports, dedup decisions, and provenance changes.

### `context/files-read.json`

Ordered recent files read or inspected, with timestamps and importance hints.

### `context/files-touched.json`

Ordered recent files changed or intended to change.

### `context/constraints.json`

Extracted normalized constraints from instruction surfaces, not raw file dumps.

### `context/instruction-aliases.json`

Maps equivalent instruction surfaces, such as:

- `AGENTS.md`
- `CLAUDE.md`

If one should stand in for another, the system may use symlinks or alias metadata rather than duplicating content.

### `verification/verification.md`

Human-readable verification summary: what was checked, what passed, what remains uncertain.

### `verification/checks.json`

Machine-readable verification entries:

- command
- result
- timestamp
- scope
- expected versus actual

## Instruction File Strategy

`AGENTS.md` and `CLAUDE.md` should be treated as equivalent instruction surfaces when used as agent-control files.

For these files:

- prefer symlink or alias normalization where practical
- do not duplicate full content unnecessarily
- extract and store normalized constraints in `constraints.json`

For other context files:

- store file path
- store extracted constraints or relevant facts
- do not store full snapshots by default

This keeps token cost low and makes the system robust if source files change.

## State Buckets and Merge Rules

## Session State

Contains:

- goal
- status
- next action
- recent summary
- recent raw tail
- active mode if known

Rule: latest session wins.

On import:

- replace goal
- replace status
- replace next action
- replace recent summary
- replace conversation tail

Reason: session state is inherently current, not cumulative.

## Execution State

Contains:

- tasks
- active plan
- files read
- files touched
- verification checks

Rules:

- tasks: merge by stable id/title, preserve status progression
- active plan: one active plan only, archive others by reference
- files read/touched: ordered dedup preserving recency
- verification entries: merge by check identity, prefer newest result

## Project Memory

Contains long-lived reusable knowledge.

Rule: merge with dedup and provenance.

Behavior:

- merge imported and existing entries
- deduplicate semantically where possible
- preserve source, timestamp, and adapter metadata
- record merge decisions in `memory-merge-log.jsonl`

This policy should be user-configurable in the future. v1 uses merge+dedup as the default.

## Instruction Constraints

Rule:

- recompute extracted constraints from live source files when available
- if files are unavailable, fall back to last extracted snapshot
- never blindly merge raw instruction file text

## Provenance

Each imported fact should record:

- source path
- adapter
- capture time
- whether it was copied, extracted, inferred, or summarized

This is necessary for debugging merge behavior and maintaining trust.

## Always-On Sync Model

Always-on sync should be limited to structured state updates.

Continuously maintained:

- `tasks/tasks.json`
- `session/current.json`
- `session/next-action.md`
- `context/files-read.json`
- `context/files-touched.json`
- `verification/checks.json`
- `memory/project-memory.json`
- `context/constraints.json`

Updated less frequently:

- `session/recent-summary.md`
- `session/conversation-tail.md`
- `restore.md`

This keeps steady-state token cost low because the system mostly performs local file writes rather than repeated summarization.

## Checkpoint Flow

Checkpoint behavior:

1. Read canonical `.handoff/` state
2. Import richer state from adapters if available
3. Normalize into canonical schema
4. Refresh:
   - recent summary
   - short raw tail
   - restore packet
5. Write timestamped bundle under `artifacts/exports/`

The export bundle is for portability and audit. `.handoff/` remains the live source of truth.

## Resume Flow

Resume behavior:

1. Detect available sources:
   - `.handoff/`
   - OMX/OMC state if present
   - repo instruction files
   - git metadata if available
2. Validate schema/version compatibility
3. Merge imported state into canonical form
4. Recompute constraints from live files where possible
5. Generate or refresh `restore.md`
6. Present the compact restore brief to the active tool

## Conversation Portability Strategy

Conversation portability uses:

- a compact recent summary
- a short raw tail plus minimal annotations

Recommended v1 raw tail policy:

- keep only the last 3 to 8 relevant turns
- apply a hard size ceiling
- preserve only user/assistant content relevant to active work
- exclude noisy logs by default

This preserves recent nuance without trying to migrate an entire transcript.

## Token Cost Strategy

The core token strategy is:

- sync structure continuously
- compile narrative only on checkpoint/resume
- never continuously compress the full transcript

This is the main optimization that makes the system practical.

## OMX/OMC Adapter in v1

If OMX/OMC is available, the adapter should import from:

- `.omx/notepad.md`
- `.omx/plans/*`
- `.omx/state/*`
- `.omx/project-memory.json` if present
- `.omx/logs/*` only for optional activity summarization

The adapter should map these into canonical `.handoff/` state. It should not treat `.omx/` as the lasting source of truth.

If OMX/OMC is unavailable, the system should operate in raw mode using:

- `.handoff/`
- repo files
- instruction files
- git metadata where available

## Why Tool-Agnostic Core + OMX Adapter

This approach:

- avoids hard dependence on OMX/OMC
- keeps the system portable
- improves fidelity when richer local state exists
- supports future adapters without redesigning the core model

## Failure Modes and Risk Handling

### Risk: stale extracted constraints

Mitigation:

- recompute from live files on resume when available
- keep source paths and timestamps

### Risk: summary drift or hallucinated state

Mitigation:

- prefer structured state as the durable source
- keep summaries derived from canonical files
- never let summary overwrite factual structured records

### Risk: overuse of conversation tail

Mitigation:

- cap raw tail size
- use summary as the primary semantic bridge

### Risk: tool-specific lock-in

Mitigation:

- keep `.handoff/` canonical
- isolate adapters behind import/export boundaries

### Risk: merge corruption in project memory

Mitigation:

- provenance tracking
- append-only merge log
- future support for replace/append/merge policies

## Open Design Constraints for Implementation

- v1 should not depend on a single runtime
- v1 should include OMX/OMC adapter support if present
- v1 should remain usable in a plain repo with no adapters
- all canonical state must remain human-inspectable
- migration must be honest about what is reconstructed versus preserved

## Recommended v1 Scope

Implement:

- canonical `.handoff/` layout
- schema versioning and manifest
- structured always-on sync
- explicit checkpoint and resume
- restore packet generation
- raw mode
- OMX/OMC adapter
- merge+dedup project memory behavior
- path + extracted constraints for non-instruction context files
- instruction aliasing for `AGENTS.md` and `CLAUDE.md`

Exclude from v1:

- full transcript archive as primary restore mechanism
- deep semantic dedup via heavy LLM use on every update
- tool-specific direct runtime resume
- cloning hidden model state

## ADR

- **Decision:** Build a tool-agnostic canonical handoff layer under `.handoff/` with an optional OMX/OMC adapter in v1.
- **Drivers:** portability, low token cost, high-fidelity durable state, honest migration semantics.
- **Alternatives considered:** OMX-only storage; raw checkpoint-only mode; full session journal first.
- **Why chosen:** best balance of portability, fidelity, and implementation complexity.
- **Consequences:** adapter interfaces and normalization logic must exist from the start; hidden state remains non-portable.
- **Follow-ups:** define schemas; define adapter interfaces; define restore packet format; define merge/dedup behavior in implementation detail.
