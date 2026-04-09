#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_INPUT="${1:-$(pwd)}"
TARGET_ROOT="$(python -c 'import os,sys; print(os.path.abspath(sys.argv[1]))' "$TARGET_INPUT")"

cd "$ROOT_DIR"

printf 'Portable handoff refreshed for:\n  %s\n\n' "$TARGET_ROOT"
printf 'Paste this into Claude Code:\n\n'
PYTHONPATH=src python -m handoff.cli to-claude --root "$TARGET_ROOT"
