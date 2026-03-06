#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

MODE="${1:-dry-run}"
CONFIRM="${2:-}"
MIN_AGE_HOURS="${MIN_AGE_HOURS:-24}"

STAMP="$(date +%Y%m%d_%H%M%S)"
REPORT="output/delete_quarantine_${STAMP}.txt"
mkdir -p output

if ! [[ "$MIN_AGE_HOURS" =~ ^[0-9]+$ ]]; then
  echo "ERROR: MIN_AGE_HOURS must be numeric"
  exit 1
fi

mapfile -t DIRS < <(find archive -maxdepth 1 -type d -name 'config_decommission_*' 2>/dev/null | sort)

printf '# Delete quarantine report (%s)\n' "$STAMP" > "$REPORT"
printf 'mode=%s\nmin_age_hours=%s\n' "$MODE" "$MIN_AGE_HOURS" >> "$REPORT"

ELIGIBLE_DIRS=()
for d in "${DIRS[@]}"; do
  mtime=$(stat -c %Y "$d")
  now=$(date +%s)
  age_hours=$(( (now - mtime) / 3600 ))
  if (( age_hours >= MIN_AGE_HOURS )); then
    ELIGIBLE_DIRS+=("$d")
  fi
  printf 'dir=%s age_hours=%s eligible=%s\n' "$d" "$age_hours" "$([[ $age_hours -ge $MIN_AGE_HOURS ]] && echo yes || echo no)" >> "$REPORT"
done

echo "[delete-quarantine] mode=$MODE"
echo "[delete-quarantine] min_age_hours=$MIN_AGE_HOURS"
echo "[delete-quarantine] report=$REPORT"
echo "[delete-quarantine] eligible_dirs=${#ELIGIBLE_DIRS[@]}"

# list files in eligible dirs
CANDIDATE_COUNT=0
for d in "${ELIGIBLE_DIRS[@]}"; do
  while IFS= read -r f; do
    [[ -z "$f" ]] && continue
    printf 'candidate=%s\n' "$f" >> "$REPORT"
    CANDIDATE_COUNT=$((CANDIDATE_COUNT + 1))
  done < <(find "$d" -type f | sort)
done

echo "[delete-quarantine] candidate_files=$CANDIDATE_COUNT"

if [[ "$MODE" != "apply" ]]; then
  echo "[delete-quarantine] dry-run only"
  exit 0
fi

if [[ "$CONFIRM" != "DELETE" ]]; then
  echo "ERROR: apply mode requires second arg exactly: DELETE"
  exit 1
fi

DELETED=0
for d in "${ELIGIBLE_DIRS[@]}"; do
  if [[ "$d" != archive/config_decommission_* ]]; then
    echo "ERROR: unsafe target directory: $d"
    exit 1
  fi
  while IFS= read -r f; do
    [[ -z "$f" ]] && continue
    rm -f "$f"
    printf 'deleted=%s\n' "$f" >> "$REPORT"
    DELETED=$((DELETED + 1))
  done < <(find "$d" -type f | sort)

done

echo "[delete-quarantine] deleted_files=$DELETED"
printf 'deleted_files=%s\n' "$DELETED" >> "$REPORT"
