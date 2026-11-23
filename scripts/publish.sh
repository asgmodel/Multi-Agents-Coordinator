#!/usr/bin/env bash
# Owner-controlled, main-only GitHub publish; never creates other branches.
set -euo pipefail
repo="${1:-}"
mode="${2:---dry-run}"
if [[ ! "$repo" =~ ^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$ ]]; then
  echo 'Usage: bash scripts/publish.sh owner/repo [--dry-run|--apply]' >&2
  exit 2
fi
if [[ "$mode" == "--dry-run" ]]; then
  printf 'Would push current main to https://github.com/%s.git (no other branches)\n' "$repo"
  exit 0
fi
if [[ "$mode" != "--apply" || "${OWNER_APPROVED:-}" != 'yes' ]]; then
  echo 'Apply requires OWNER_APPROVED=yes and --apply' >&2
  exit 2
fi
if ! git rev-parse --show-toplevel >/dev/null 2>&1; then
  echo 'Not a Git worktree; clone the repository first' >&2
  exit 2
fi
if [[ "$(git branch --show-current)" != "main" ]]; then
  echo 'Refusing to publish: only main is allowed' >&2
  exit 2
fi
origin="https://github.com/$repo.git"
if [[ "$(git remote get-url origin)" != "$origin" ]]; then
  echo 'Origin must match GitHub destination; refusing to modify remote' >&2
  exit 2
fi
git push origin main
