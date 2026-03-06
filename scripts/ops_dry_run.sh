#!/usr/bin/env bash
set -euo pipefail

missing=()
for f in daily_report.py mobile_api.py generate_vm_infrastructure_report.py generate_service_health_report.py; do
  if [[ ! -f "$f" ]]; then
    missing+=("$f")
  fi
done

if (( ${#missing[@]} > 0 )); then
  echo "{\"status\":\"fail\",\"reason\":\"missing files: ${missing[*]}\"}"
  exit 1
fi

echo "{\"status\":\"pass\",\"reason\":\"ops dry-run checks passed\"}"
