#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: ./install.sh <codex|claude|both> [--mode symlink|copy] [--home DIR] [--source DIR]

Installs the handoff and get-handoff skills into a local agent runtime.

Options:
  --mode symlink   Link installed skills to this checkout. Default.
  --mode copy      Copy skill files into the target runtime.
  --home DIR       Override HOME for testing or custom installs.
  --source DIR     Use a custom source directory containing skill folders.
  -h, --help       Show this help.
USAGE
}

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
runtime=""
mode="symlink"
home_dir="${HOME:-}"
source_dir="${script_dir}/skills"

while [ "$#" -gt 0 ]; do
  case "$1" in
    codex|claude|both)
      if [ -n "$runtime" ]; then
        echo "runtime already set: ${runtime}" >&2
        exit 2
      fi
      runtime="$1"
      ;;
    --mode)
      if [ "$#" -lt 2 ]; then
        echo "--mode requires symlink or copy" >&2
        exit 2
      fi
      mode="$2"
      shift
      ;;
    --home)
      if [ "$#" -lt 2 ]; then
        echo "--home requires a directory" >&2
        exit 2
      fi
      home_dir="$2"
      shift
      ;;
    --source)
      if [ "$#" -lt 2 ]; then
        echo "--source requires a directory" >&2
        exit 2
      fi
      source_dir="$2"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
  shift
done

if [ -z "$runtime" ]; then
  usage >&2
  exit 2
fi

if [ -z "$home_dir" ]; then
  echo "HOME is unset; pass --home DIR" >&2
  exit 2
fi

case "$mode" in
  symlink|copy) ;;
  *)
    echo "unsupported mode: ${mode}" >&2
    exit 2
    ;;
esac

case "$source_dir" in
  /*) ;;
  *) source_dir="${PWD}/${source_dir}" ;;
esac

skill_names=("handoff" "get-handoff")

validate_source() {
  local name
  for name in "${skill_names[@]}"; do
    if [ ! -f "${source_dir}/${name}/SKILL.md" ]; then
      echo "${source_dir} must contain ${name}/SKILL.md" >&2
      exit 1
    fi
  done
}

target_root_for() {
  case "$1" in
    codex) printf '%s\n' "${home_dir}/.codex/skills" ;;
    claude) printf '%s\n' "${home_dir}/.claude/skills" ;;
    *)
      echo "unsupported runtime: $1" >&2
      exit 2
      ;;
  esac
}

replace_target() {
  local target="$1"
  if [ -L "$target" ] || [ -f "$target" ]; then
    rm -f "$target"
  elif [ -d "$target" ]; then
    rm -rf "$target"
  fi
}

install_runtime() {
  local runtime_name="$1"
  local target_root
  local name
  local source
  local target

  target_root="$(target_root_for "$runtime_name")"
  mkdir -p "$target_root"

  for name in "${skill_names[@]}"; do
    source="${source_dir}/${name}"
    target="${target_root}/${name}"
    replace_target "$target"

    if [ "$mode" = "symlink" ]; then
      ln -s "$source" "$target"
    else
      cp -R "$source" "$target"
    fi

    printf 'installed %s -> %s\n' "$name" "$target"
  done
}

validate_source

case "$runtime" in
  both)
    install_runtime codex
    install_runtime claude
    ;;
  codex|claude)
    install_runtime "$runtime"
    ;;
esac
