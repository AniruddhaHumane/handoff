#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_INPUT="${1:-$(pwd)}"
TARGET_ROOT="$(python -c 'import os,sys; print(os.path.abspath(sys.argv[1]))' "$TARGET_INPUT")"

cd "$ROOT_DIR"

printf 'Structured handoff exported for:\n  %s\n\n' "$TARGET_ROOT"
printf 'Use this handoff block as context in the destination model.\n\n'
PYTHONPATH=src python -m handoff.cli export --root "$TARGET_ROOT"
