#!/usr/bin/env bash
set -euo pipefail

MODE="dry-run"
if [[ "${1:-}" == "--apply" ]]; then
  MODE="apply"
fi

ROOT_DIR="${2:-.}"
cd "$ROOT_DIR"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "ERROR: must run inside git repository"
  exit 2
fi

DOC_DIR="docs/legacy_notes"
ARCHIVE_DIR="archive/legacy_root_cleanup"
mkdir -p "$DOC_DIR" "$ARCHIVE_DIR/backups" "$ARCHIVE_DIR/misc" "$ARCHIVE_DIR/github_clean"

move_path() {
  local src="$1"
  local dst="$2"
  if [[ ! -e "$src" ]]; then
    return 0
  fi
  if [[ "$MODE" == "dry-run" ]]; then
    echo "DRY-RUN mv '$src' -> '$dst'"
  else
    mkdir -p "$(dirname "$dst")"
    mv "$src" "$dst"
    echo "MOVED '$src' -> '$dst'"
  fi
}

echo "Repo hygiene mode: $MODE"

# 1) Move non-source markdown notes from repo root to docs/legacy_notes
for f in *.md; do
  [[ -e "$f" ]] || continue
  case "$f" in
    README.md|SECURITY.md)
      continue
      ;;
  esac
  move_path "$f" "$DOC_DIR/$f"
done

# 2) Move backup/snapshot files from root to archive
for pattern in "*.backup" "*.backup.*" "*.bak" "*.old" "*.orig"; do
  for f in $pattern; do
    [[ -e "$f" ]] || continue
    move_path "$f" "$ARCHIVE_DIR/backups/$f"
  done
done

# 3) Move known odd/misc clutter from root
for f in "=3.8.0"; do
  [[ -e "$f" ]] || continue
  move_path "$f" "$ARCHIVE_DIR/misc/$f"
done

# 4) Move legacy helper folder if present
if [[ -d "github_clean" ]]; then
  move_path "github_clean" "$ARCHIVE_DIR/github_clean"
fi

if [[ "$MODE" == "dry-run" ]]; then
  echo "Dry-run complete. Re-run with --apply to execute moves."
else
  echo "Apply complete."
fi
