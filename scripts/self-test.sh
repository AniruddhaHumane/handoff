#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "== Full test suite =="
PYTHONPATH=src python -m unittest discover -s tests -v

echo
echo "== Manual smoke test =="
tmp1="$(mktemp -d)"
PYTHONPATH=src python -m handoff.cli checkpoint --root "$tmp1"
PYTHONPATH=src python -m handoff.cli resume --root "$tmp1"
test -f "$tmp1/.handoff/restore.md"
echo "restore.md exists: OK"
rm -rf "$tmp1"

echo
echo "== OMX import test =="
tmp2="$(mktemp -d)"
mkdir -p "$tmp2/.omx/plans" "$tmp2/.omx/state"

cat > "$tmp2/.omx/project-memory.json" <<'JSON'
{
  "entries": [
    {
      "key": "omx:decision",
      "value": "Imported from OMX",
      "sources": ["omx"],
      "updated_at": "2026-04-09T01:00:00Z"
    }
  ]
}
JSON

cat > "$tmp2/.omx/state/session.json" <<'JSON'
{
  "cwd": "/tmp/demo",
  "session_id": "demo-session"
}
JSON

cat > "$tmp2/.omx/plans/demo-plan.md" <<'MD'
# Demo Plan

- Imported OMX plan task
MD

cat > "$tmp2/.omx/notepad.md" <<'MD'
## WORKING MEMORY
[2026-04-09T01:00:00Z] Imported OMX notes are available.
MD

PYTHONPATH=src python -m handoff.cli checkpoint --root "$tmp2" >/dev/null

grep -q "Imported from OMX" "$tmp2/.handoff/memory/project-memory.json"
grep -q "Imported OMX plan task" "$tmp2/.handoff/restore.md"
echo "OMX import merge: OK"
rm -rf "$tmp2"

echo
echo "== Canonical state preservation test =="
tmp3="$(mktemp -d)"
mkdir -p \
  "$tmp3/.handoff/session" \
  "$tmp3/.handoff/tasks" \
  "$tmp3/.handoff/plans" \
  "$tmp3/.handoff/memory" \
  "$tmp3/.handoff/context" \
  "$tmp3/.handoff/verification"

cat > "$tmp3/.handoff/session/current.json" <<'JSON'
{
  "goal": "My seeded goal",
  "status": "working",
  "next_action": "Keep this action",
  "active_mode": null,
  "timestamp": "2026-04-09T00:00:00Z",
  "last_checkpoint_at": null,
  "last_adapter_used": "raw"
}
JSON

cat > "$tmp3/.handoff/tasks/tasks.json" <<'JSON'
{"tasks":["Keep canonical task"]}
JSON

cat > "$tmp3/.handoff/memory/project-memory.json" <<'JSON'
{
  "entries": [
    {
      "key": "local:decision",
      "value": "Keep canonical local decision",
      "sources": ["local"],
      "updated_at": "2026-04-09T00:00:00Z"
    }
  ]
}
JSON

cat > "$tmp3/.handoff/manifest.json" <<'JSON'
{
  "schema_version": "1",
  "active_adapter": "raw",
  "created_at": "2026-04-09T00:00:00Z",
  "updated_at": "2026-04-09T00:00:00Z",
  "last_checkpoint_at": null,
  "last_resume_at": null,
  "integrity": {}
}
JSON

cat > "$tmp3/.handoff/plans/plan-index.json" <<'JSON'
{"active": null, "plans": []}
JSON

cat > "$tmp3/.handoff/context/files-read.json" <<'JSON'
{"files": []}
JSON

cat > "$tmp3/.handoff/context/files-touched.json" <<'JSON'
{"files": []}
JSON

cat > "$tmp3/.handoff/context/constraints.json" <<'JSON'
{"sources": [], "rules": []}
JSON

cat > "$tmp3/.handoff/context/instruction-aliases.json" <<'JSON'
{"aliases": []}
JSON

cat > "$tmp3/.handoff/verification/checks.json" <<'JSON'
{"checks": []}
JSON

printf '# Restore Brief\n\nstale restore\n' > "$tmp3/.handoff/restore.md"
: > "$tmp3/.handoff/session/recent-summary.md"
: > "$tmp3/.handoff/session/conversation-tail.md"
: > "$tmp3/.handoff/session/next-action.md"
: > "$tmp3/.handoff/session/status.md"
: > "$tmp3/.handoff/plans/active-plan.md"
: > "$tmp3/.handoff/verification/verification.md"
: > "$tmp3/.handoff/memory/memory-merge-log.jsonl"

PYTHONPATH=src python -m handoff.cli checkpoint --root "$tmp3" >/dev/null

grep -q "My seeded goal" "$tmp3/.handoff/session/current.json"
grep -q '"algorithm": "sha256"' "$tmp3/.handoff/manifest.json"
echo "Canonical preservation + manifest repair: OK"
rm -rf "$tmp3"

echo
echo "All self-tests passed."
