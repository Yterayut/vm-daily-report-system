#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

MODE="${1:-dry-run}"
INVENTORY_JSON="${2:-}"

if [[ -z "$INVENTORY_JSON" ]]; then
  INVENTORY_JSON="$(ls -1t output/config_inventory_*.json 2>/dev/null | head -n 1 || true)"
fi

if [[ -z "$INVENTORY_JSON" || ! -f "$INVENTORY_JSON" ]]; then
  echo "ERROR: inventory json not found. Run: python3 scripts/config_inventory.py"
  exit 1
fi

STAMP="$(date +%Y%m%d_%H%M%S)"
ARCHIVE_DIR="archive/config_decommission_${STAMP}"
MANIFEST="output/config_decommission_${STAMP}.txt"

mapfile -t TARGETS < <(python3 - <<'PY' "$INVENTORY_JSON"
import json,sys
with open(sys.argv[1], 'r', encoding='utf-8') as f:
    data=json.load(f)
for item in data.get('items', []):
    rec = item.get('recommendation')
    conf = int(item.get('confidence', 0))
    if rec == 'archive_safe' and conf >= 90:
        print(item.get('path'))
PY
)

echo "[decommission] mode=${MODE}"
echo "[decommission] inventory=${INVENTORY_JSON}"
echo "[decommission] archive_safe_candidates=${#TARGETS[@]}"

printf '# Config decommission manifest (%s)\n' "$STAMP" > "$MANIFEST"
for p in "${TARGETS[@]}"; do
  printf '%s\n' "$p" >> "$MANIFEST"
done

echo "[decommission] manifest=${MANIFEST}"

if [[ "$MODE" != "apply" ]]; then
  echo "[decommission] dry-run only, no files moved"
  exit 0
fi

mkdir -p "$ARCHIVE_DIR"
MOVED=0
for p in "${TARGETS[@]}"; do
  if [[ -f "$p" ]]; then
    mkdir -p "$ARCHIVE_DIR/$(dirname "$p")"
    mv "$p" "$ARCHIVE_DIR/$p"
    MOVED=$((MOVED + 1))
  fi
done

echo "[decommission] moved=${MOVED}"
echo "[decommission] archive_dir=${ARCHIVE_DIR}"
