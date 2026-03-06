#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

RETENTION_APPLY="${RETENTION_APPLY:-false}"
RETENTION_DAYS="${RETENTION_DAYS:-90}"

if [[ "${RETENTION_APPLY,,}" == "true" ]]; then
  mode="apply"
else
  mode="dry-run"
fi

echo "[retention-job] mode=$mode retention_days=$RETENTION_DAYS"
RETENTION_DAYS="$RETENTION_DAYS" ./scripts/cleanup_artifacts_retention.sh "$mode"
