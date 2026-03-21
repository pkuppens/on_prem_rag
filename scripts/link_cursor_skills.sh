#!/usr/bin/env bash
# Creates .cursor/skills -> ../pkuppens/skills (symlink). See docs/technical/SKILLS_SETUP.md.
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TARGET="${REPO_ROOT}/../pkuppens/skills"
LINK="${REPO_ROOT}/.cursor/skills"
if [[ ! -d "$TARGET" ]]; then
  echo "Skills target not found: $TARGET" >&2
  echo "Clone https://github.com/pkuppens/pkuppens next to this repo." >&2
  exit 1
fi
mkdir -p "${REPO_ROOT}/.cursor"
rm -rf "$LINK"
ln -sfn "$(cd "$TARGET" && pwd)" "$LINK"
echo "Linked .cursor/skills -> $(readlink -f "$LINK" 2>/dev/null || readlink "$LINK")"
