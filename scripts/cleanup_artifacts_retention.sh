#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

MODE="${1:-dry-run}"
RETENTION_DAYS="${RETENTION_DAYS:-90}"
TARGET_DIRS_RAW="${TARGET_DIRS:-output}"

if ! [[ "$RETENTION_DAYS" =~ ^[0-9]+$ ]]; then
  echo "ERROR: RETENTION_DAYS must be numeric"
  exit 1
fi

IFS=' ' read -r -a TARGET_DIRS <<< "$TARGET_DIRS_RAW"
STAMP="$(date +%Y%m%d_%H%M%S)"
REPORT="output/cleanup_retention_${STAMP}.txt"
mkdir -p output

ALLOWLIST=(
  "test_gate_*.json"
  "run_summary_*.json"
  "config_inventory_*.json"
  "config_inventory_*.md"
  "config_decommission_*.txt"
  "delete_quarantine_*.txt"
)

printf '# Retention cleanup report (%s)\n' "$STAMP" > "$REPORT"
printf 'mode=%s\nretention_days=%s\n' "$MODE" "$RETENTION_DAYS" >> "$REPORT"
printf 'target_dirs=%s\n' "$TARGET_DIRS_RAW" >> "$REPORT"

CANDIDATES=()
for dir in "${TARGET_DIRS[@]}"; do
  [[ -d "$dir" ]] || continue
  for pattern in "${ALLOWLIST[@]}"; do
    while IFS= read -r f; do
      [[ -z "$f" ]] && continue
      CANDIDATES+=("$f")
    done < <(find "$dir" -maxdepth 1 -type f -name "$pattern" -mtime "+$RETENTION_DAYS" | sort)
  done
done

# unique
mapfile -t CANDIDATES < <(printf "%s\n" "${CANDIDATES[@]:-}" | awk 'NF' | sort -u)

printf 'candidate_count=%s\n' "${#CANDIDATES[@]}" >> "$REPORT"
for f in "${CANDIDATES[@]}"; do
  printf 'candidate=%s\n' "$f" >> "$REPORT"
done

echo "[retention] mode=$MODE"
echo "[retention] retention_days=$RETENTION_DAYS"
echo "[retention] target_dirs=$TARGET_DIRS_RAW"
echo "[retention] candidate_count=${#CANDIDATES[@]}"
echo "[retention] report=$REPORT"

if [[ "$MODE" != "apply" ]]; then
  echo "[retention] dry-run only"
  exit 0
fi

DELETED=0
for f in "${CANDIDATES[@]}"; do
  base="$(basename "$f")"
  case "$base" in
    test_gate_*.json|run_summary_*.json|config_inventory_*.json|config_inventory_*.md|config_decommission_*.txt|delete_quarantine_*.txt)
      rm -f "$f"
      printf 'deleted=%s\n' "$f" >> "$REPORT"
      DELETED=$((DELETED + 1))
      ;;
    *)
      echo "ERROR: unsafe file match: $f"
      exit 1
      ;;
  esac
done

printf 'deleted_count=%s\n' "$DELETED" >> "$REPORT"
echo "[retention] deleted_count=$DELETED"
