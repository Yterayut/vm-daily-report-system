#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

MODE="${1:-dry-run}"
CRON_SCHEDULE="${RETENTION_CRON_SCHEDULE:-15 2 * * *}"
LOG_FILE="${RETENTION_CRON_LOG:-logs/retention_cron.log}"

mkdir -p logs

cmd="cd $ROOT_DIR && RETENTION_APPLY=\${RETENTION_APPLY:-false} RETENTION_DAYS=\${RETENTION_DAYS:-90} ./scripts/run_retention_job.sh >> $LOG_FILE 2>&1"
entry="$CRON_SCHEDULE $cmd"

echo "[retention-cron] mode=$MODE"
echo "[retention-cron] schedule=$CRON_SCHEDULE"
echo "[retention-cron] entry=$entry"

if [[ "$MODE" != "apply" ]]; then
  echo "[retention-cron] dry-run only; not modifying crontab"
  exit 0
fi

current="$(crontab -l 2>/dev/null || true)"
if grep -Fq "$cmd" <<< "$current"; then
  echo "[retention-cron] existing entry found; no change"
  exit 0
fi

{
  printf '%s\n' "$current"
  printf '%s\n' "$entry"
} | crontab -

echo "[retention-cron] installed"
