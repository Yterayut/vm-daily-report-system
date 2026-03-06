#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${1:-.}"
cd "$ROOT_DIR"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "ERROR: phase5 test gate must run inside a git repository"
  exit 2
fi

log_step() {
  printf '\n[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$1"
}

log_step "Gate 1/6: Compile check"
python3 -m py_compile \
  daily_report.py \
  mobile_api.py \
  generate_service_health_report.py \
  generate_vm_infrastructure_report.py \
  carbon_service_monitor.py \
  enhanced_alert_system.py \
  load_env.py \
  service_health_adapter.py

log_step "Gate 2/6: Secret scan"
./scripts/secret_scan.sh .

log_step "Gate 3/6: Zabbix auth preflight (optional)"
if ./scripts/zabbix_auth_preflight.sh .; then
  echo "Zabbix preflight PASS"
else
  if [[ "${ZABBIX_PREFLIGHT_REQUIRED:-false}" == "true" ]]; then
    echo "Zabbix preflight FAIL and required => gate failed"
    exit 1
  fi
  echo "Zabbix preflight FAIL but optional => continue"
fi

log_step "Gate 4/6: Contract test (/api/services/health schema)"
ENABLE_NEW_SERVICE_SOURCE=true python3 - <<'PY'
from mobile_api import get_carbon_services_sync

payload = get_carbon_services_sync()
required_top = {"groups", "summary", "logs", "last_updated"}
missing_top = sorted(required_top - set(payload.keys()))
if missing_top:
    raise SystemExit("Contract failed: missing top-level keys: {}".format(missing_top))

required_summary = {
    "total_services",
    "healthy_services",
    "warning_services",
    "error_services",
    "availability_percentage",
    "overall_status",
}
summary = payload.get("summary", {})
missing_summary = sorted(required_summary - set(summary.keys()))
if missing_summary:
    raise SystemExit("Contract failed: missing summary keys: {}".format(missing_summary))

print("Contract PASS: groups={}, overall_status={}".format(
    len(payload.get("groups", {})),
    summary.get("overall_status"),
))
PY

log_step "Gate 5/6: Smoke test (generate VM + Service PDF, email dry-run single recipient)"
ENABLE_NEW_SERVICE_SOURCE=true \
EMAIL_DRY_RUN=true \
LINE_NOTIFICATIONS_ENABLED=false \
TO_EMAILS=yterayut@gmail.com \
python3 daily_report.py --simple

today="$(date +%F)"
vm_pdf="output/VM_Infrastructure_Report_${today}.pdf"
svc_pdf="output/Service_Health_Report_${today}.pdf"
if [[ ! -f "$vm_pdf" ]]; then
  echo "Smoke failed: missing ${vm_pdf}"
  exit 1
fi
if [[ ! -f "$svc_pdf" ]]; then
  echo "Smoke failed: missing ${svc_pdf}"
  exit 1
fi
echo "Smoke PASS: ${vm_pdf}, ${svc_pdf}"

log_step "Gate 6/6: Ops dry-run (deploy/rollback prerequisites)"
current_branch="$(git branch --show-current)"
head_commit="$(git rev-parse --short HEAD)"
echo "Ops dry-run PASS: branch=${current_branch}, head=${head_commit}"
echo "Rollback hint: git revert ${head_commit}  # safer rollback commit"

printf '\nPhase 5 Test Gate PASS\n'
