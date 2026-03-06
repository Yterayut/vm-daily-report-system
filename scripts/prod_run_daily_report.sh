#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python3}"
LOG_DIR="${LOG_DIR:-logs}"
mkdir -p "$LOG_DIR"

DRY_RUN=false
STRICT_GUARD="${STRICT_GUARD:-false}"

for arg in "$@"; do
  case "$arg" in
    --dry-run)
      DRY_RUN=true
      ;;
    --strict)
      STRICT_GUARD=true
      ;;
  esac
done

if [[ "$STRICT_GUARD" == "true" ]]; then
  export ENABLE_STRICT_ENV_GUARD=true
fi

if [[ "$DRY_RUN" == "true" ]]; then
  export EMAIL_DRY_RUN=true
  export LINE_NOTIFICATIONS_ENABLED=false
  echo "[prod-run] DRY RUN enabled (EMAIL_DRY_RUN=true)"
else
  # Production default: real send mode unless explicitly dry-run.
  export EMAIL_DRY_RUN=false
  export PRODUCTION_POLICY_REQUIRED=true
  export CREDENTIAL_HARDENING_REQUIRED=true
  export ZABBIX_PREFLIGHT_REQUIRED=true
  export SMTP_PREFLIGHT_REQUIRED=true
  export ENABLE_STRICT_ENV_GUARD=true
  export ENABLE_LEGACY_EMAIL_FIX=false
fi

echo "[prod-run] root=$ROOT_DIR"
echo "[prod-run] python=$PYTHON_BIN"
echo "[prod-run] strict_env_guard=${ENABLE_STRICT_ENV_GUARD:-false}"

if [[ "$DRY_RUN" != "true" ]]; then
  ./scripts/production_lockdown_preflight.sh
fi

exec "$PYTHON_BIN" daily_report.py --simple
