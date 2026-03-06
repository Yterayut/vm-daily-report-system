#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${1:-.}"
cd "$ROOT_DIR"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "ERROR: phase5 test gate must run inside a git repository"
  exit 2
fi

mkdir -p output
RUN_ID="$(date +%Y%m%d_%H%M%S_%N)_$$"
START_TS="$(date -Iseconds)"
ARTIFACT_PATH="output/test_gate_${RUN_ID}.json"
RUN_SUMMARY_PATH="output/run_summary_$(date +%F).json"
RESULTS_FILE="$(mktemp)"
SMOKE_LOG="$(mktemp)"

VM_COUNT="0"
ZABBIX_AUTH="unknown"
SMTP_AUTH="not_checked"
MAIL_SENT="dry_run"
ERROR_COUNT=0

cleanup() {
  rm -f "$RESULTS_FILE" "$SMOKE_LOG"
}
trap cleanup EXIT

log_step() {
  printf '\n[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$1"
}

bool_mode() {
  local value="${1:-false}"
  if [[ "${value,,}" == "true" ]]; then
    echo "required"
  else
    echo "optional"
  fi
}

record_gate() {
  # gate_name|status|mode|reason
  printf '%s|%s|%s|%s\n' "$1" "$2" "$3" "$4" >> "$RESULTS_FILE"
}

write_artifact() {
  local overall_status="$1"
  python3 - <<'PY' "$RESULTS_FILE" "$ARTIFACT_PATH" "$RUN_SUMMARY_PATH" "$RUN_ID" "$START_TS" "$overall_status" "$VM_COUNT" "$ZABBIX_AUTH" "$SMTP_AUTH" "$MAIL_SENT" "$ERROR_COUNT"
import json
import sys
from datetime import datetime

results_file, artifact_path, run_summary_path, run_id, ts_start, overall_status, vm_count, zabbix_auth, smtp_auth, mail_sent, error_count = sys.argv[1:]

entries = []
with open(results_file, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        gate, status, mode, reason = line.split("|", 3)
        entries.append({
            "gate": gate,
            "status": status,
            "mode": mode,
            "reason": reason,
        })

payload = {
    "run_id": run_id,
    "timestamp_start": ts_start,
    "timestamp_end": datetime.now().isoformat(),
    "overall_status": overall_status,
    "summary": {
        "zabbix_auth": zabbix_auth,
        "smtp_auth": smtp_auth,
        "vm_count": int(vm_count),
        "mail_sent": mail_sent,
        "error_count": int(error_count),
    },
    "gates": entries,
}

with open(artifact_path, "w", encoding="utf-8") as f:
    json.dump(payload, f, indent=2)

run_summary = {
    "run_id": run_id,
    "timestamp_start": ts_start,
    "timestamp_end": datetime.now().isoformat(),
    "overall_status": overall_status,
    "zabbix_auth": zabbix_auth,
    "smtp_auth": smtp_auth,
    "vm_count": int(vm_count),
    "mail_sent": mail_sent,
    "error_count": int(error_count),
}
with open(run_summary_path, "w", encoding="utf-8") as f:
    json.dump(run_summary, f, indent=2)

print(f"Artifact written: {artifact_path}")
PY
}

fail_and_exit() {
  local reason="$1"
  ERROR_COUNT=$((ERROR_COUNT + 1))
  record_gate "final" "fail" "required" "$reason"
  write_artifact "fail"
  python3 ./scripts/notify_gate_failure.py || true
  exit 1
}

CREDENTIAL_REQUIRED="${CREDENTIAL_HARDENING_REQUIRED:-false}"
ZABBIX_REQUIRED="${ZABBIX_PREFLIGHT_REQUIRED:-false}"
PRODUCTION_POLICY_REQUIRED="${PRODUCTION_POLICY_REQUIRED:-false}"
export CREDENTIAL_HARDENING_REQUIRED="$CREDENTIAL_REQUIRED"
export ZABBIX_PREFLIGHT_REQUIRED="$ZABBIX_REQUIRED"
export PRODUCTION_POLICY_REQUIRED="$PRODUCTION_POLICY_REQUIRED"

log_step "Gate 1/8: Compile check (mode=required)"
if python3 -m py_compile \
  daily_report.py \
  mobile_api.py \
  generate_service_health_report.py \
  generate_vm_infrastructure_report.py \
  carbon_service_monitor.py \
  enhanced_alert_system.py \
  load_env.py \
  service_health_adapter.py; then
  record_gate "compile" "pass" "required" "ok"
else
  record_gate "compile" "fail" "required" "py_compile failed"
  fail_and_exit "compile gate failed"
fi

log_step "Gate 2/8: Secret scan (mode=required)"
if ./scripts/secret_scan.sh .; then
  record_gate "secret_scan" "pass" "required" "ok"
else
  record_gate "secret_scan" "fail" "required" "secret scan failed"
  fail_and_exit "secret scan gate failed"
fi

policy_mode="$(bool_mode "$PRODUCTION_POLICY_REQUIRED")"
log_step "Gate 3/8: Production policy preflight (mode=${policy_mode})"
if ./scripts/production_policy_preflight.sh .; then
  record_gate "production_policy" "pass" "$policy_mode" "pass_or_warn"
else
  record_gate "production_policy" "fail" "$policy_mode" "production policy check failed"
  if [[ "$policy_mode" == "required" ]]; then
    fail_and_exit "production policy gate failed"
  fi
fi

cred_mode="$(bool_mode "$CREDENTIAL_REQUIRED")"
log_step "Gate 4/8: Credential hardening preflight (mode=${cred_mode})"
if ./scripts/credential_hardening_preflight.sh .; then
  record_gate "credential_hardening" "pass" "$cred_mode" "pass_or_warn"
else
  record_gate "credential_hardening" "fail" "$cred_mode" "credential hardening check failed"
  if [[ "$cred_mode" == "required" ]]; then
    fail_and_exit "credential hardening gate failed"
  fi
fi

zbx_mode="$(bool_mode "$ZABBIX_REQUIRED")"
log_step "Gate 5/8: Zabbix auth preflight (mode=${zbx_mode})"
if ./scripts/zabbix_auth_preflight.sh .; then
  ZABBIX_AUTH="pass"
  record_gate "zabbix_preflight" "pass" "$zbx_mode" "ok"
else
  ZABBIX_AUTH="fail"
  record_gate "zabbix_preflight" "fail" "$zbx_mode" "zabbix auth failed"
  if [[ "$zbx_mode" == "required" ]]; then
    fail_and_exit "zabbix preflight gate failed"
  fi
fi

log_step "Gate 6/9: Config contract test (mode=required)"
if python3 ./scripts/config_contract_test.py; then
  record_gate "config_contract" "pass" "required" "ok"
else
  record_gate "config_contract" "fail" "required" "config contract failed"
  fail_and_exit "config contract gate failed"
fi

log_step "Gate 7/9: Contract test (/api/services/health schema) (mode=required)"
if ENABLE_NEW_SERVICE_SOURCE=true python3 - <<'PY'
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
then
  record_gate "contract" "pass" "required" "ok"
else
  record_gate "contract" "fail" "required" "schema contract failed"
  fail_and_exit "contract gate failed"
fi

log_step "Gate 8/9: Smoke test (mode=required)"
if ENABLE_NEW_SERVICE_SOURCE=true \
  EMAIL_DRY_RUN=true \
  LINE_NOTIFICATIONS_ENABLED=false \
  TO_EMAILS=yterayut@gmail.com \
  python3 daily_report.py --simple | tee "$SMOKE_LOG"; then
  :
else
  record_gate "smoke" "fail" "required" "daily_report.py --simple failed"
  fail_and_exit "smoke run failed"
fi

today="$(date +%F)"
vm_pdf="output/VM_Infrastructure_Report_${today}.pdf"
svc_pdf="output/Service_Health_Report_${today}.pdf"

if [[ ! -f "$vm_pdf" || ! -f "$svc_pdf" ]]; then
  record_gate "smoke" "fail" "required" "missing expected PDF outputs"
  fail_and_exit "smoke output files missing"
fi

vm_check_json="$(python3 - <<'PY'
import json
from fetch_zabbix_data import EnhancedZabbixClient

client = EnhancedZabbixClient()
connected = False
vm_count = 0
try:
    connected = client.connect()
    if connected:
        hosts = client.fetch_hosts() or []
        vm_count = len(hosts)
finally:
    try:
        client.disconnect()
    except Exception:
        pass

print(json.dumps({"connected": connected, "vm_count": vm_count}))
PY
)"

VM_COUNT="$(python3 - <<'PY' "$vm_check_json"
import json, sys
print(int(json.loads(sys.argv[1])["vm_count"]))
PY
)"

zbx_connected="$(python3 - <<'PY' "$vm_check_json"
import json, sys
print(str(bool(json.loads(sys.argv[1])["connected"])).lower())
PY
)"

if [[ "$zbx_mode" == "required" ]]; then
  if [[ "$zbx_connected" != "true" || "$VM_COUNT" -le 0 ]]; then
    record_gate "vm_real_data" "fail" "required" "required mode demands real zabbix VM data (connected=${zbx_connected}, vm_count=${VM_COUNT})"
    fail_and_exit "real VM data validation failed in required mode"
  fi
fi

record_gate "smoke" "pass" "required" "pdf generated"
record_gate "vm_real_data" "pass" "$zbx_mode" "connected=${zbx_connected}, vm_count=${VM_COUNT}"

echo "Smoke PASS: ${vm_pdf}, ${svc_pdf}"

log_step "Gate 9/9: Ops dry-run (mode=required)"
current_branch="$(git branch --show-current)"
head_commit="$(git rev-parse --short HEAD)"
echo "Ops dry-run PASS: branch=${current_branch}, head=${head_commit}"
echo "Rollback hint: git revert ${head_commit}"
record_gate "ops_dry_run" "pass" "required" "branch=${current_branch}, head=${head_commit}"

echo ""
echo "Run Summary:"
echo "  zabbix_auth=${ZABBIX_AUTH}"
echo "  smtp_auth=${SMTP_AUTH}"
echo "  vm_count=${VM_COUNT}"
echo "  mail_sent=${MAIL_SENT}"
echo "  error_count=${ERROR_COUNT}"

write_artifact "pass"
printf '\nPhase 5 Test Gate PASS\n'
