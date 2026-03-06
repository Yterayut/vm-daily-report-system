#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

mkdir -p output
sample="output/test_gate_99999999_000000_000000000_0000000.json"

cat > "$sample" <<JSON
{
  "run_id": "test-fail-alert",
  "overall_status": "FAIL",
  "summary": {
    "zabbix_auth": "fail",
    "smtp_auth": "pass",
    "vm_count": 0,
    "mail_sent": "dry_run",
    "error_count": 1
  },
  "gates": [
    {"gate":"ConfigContract","status":"fail","mode":"required","reason":"synthetic test"}
  ]
}
JSON

echo "[alert-test] synthetic artifact=$sample"
ENABLE_GATE_FAILURE_ALERTS=true GATE_ALERT_DRY_RUN=true python3 ./scripts/notify_gate_failure.py
