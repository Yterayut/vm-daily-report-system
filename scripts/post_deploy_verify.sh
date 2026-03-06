#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

STAMP="$(date +%Y%m%d_%H%M%S)"
REPORT="output/post_deploy_verify_${STAMP}.txt"
mkdir -p output

echo "# Post Deploy Verification ($STAMP)" > "$REPORT"

status=0

check_file() {
  local pattern="$1"
  local label="$2"
  local latest
  latest="$(ls -1t $pattern 2>/dev/null | head -n1 || true)"
  if [[ -n "$latest" ]]; then
    echo "PASS: $label -> $latest" | tee -a "$REPORT"
  else
    echo "FAIL: $label missing ($pattern)" | tee -a "$REPORT"
    status=1
  fi
}

check_file "output/test_gate_*.json" "gate artifact"
check_file "output/run_summary_*.json" "run summary"

if [[ -f output/run_summary_$(date +%F).json ]]; then
  python3 - <<'PY' "output/run_summary_$(date +%F).json" | tee -a "$REPORT"
import json,sys
p=sys.argv[1]
d=json.load(open(p,'r',encoding='utf-8'))
required=['overall_status','zabbix_auth','smtp_auth','vm_count','mail_sent','error_count']
missing=[k for k in required if k not in d]
if missing:
    print('FAIL: run summary missing keys:', ','.join(missing))
    raise SystemExit(1)
print('PASS: run summary schema ok')
print('INFO: overall_status=',d.get('overall_status'))
print('INFO: vm_count=',d.get('vm_count'))
PY
  if [[ ${PIPESTATUS[0]} -ne 0 ]]; then
    status=1
  fi
fi

echo "report=$REPORT"
exit $status
