#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${1:-.}"
cd "$ROOT_DIR"

RUN_ID="$(date +%Y%m%d_%H%M%S)_$(date +%N)_$$"
START_TS="$(date -Iseconds)"
OUTPUT_DIR="output"
ARTIFACT_PATH="$OUTPUT_DIR/test_gate_${RUN_ID}.json"
RUN_SUMMARY_PATH="$OUTPUT_DIR/run_summary_$(date +%F).json"
mkdir -p "$OUTPUT_DIR"

PRODUCTION_POLICY_REQUIRED="${PRODUCTION_POLICY_REQUIRED:-false}"
CREDENTIAL_HARDENING_REQUIRED="${CREDENTIAL_HARDENING_REQUIRED:-false}"
ZABBIX_PREFLIGHT_REQUIRED="${ZABBIX_PREFLIGHT_REQUIRED:-false}"
SMTP_PREFLIGHT_REQUIRED="${SMTP_PREFLIGHT_REQUIRED:-false}"

GATE_LOG="$(mktemp)"
OVERALL_STATUS="PASS"
ERROR_COUNT=0

ZABBIX_AUTH="unknown"
SMTP_AUTH="unknown"
VM_COUNT=0
MAIL_SENT="unknown"

mode_of() {
  local required="$1"
  if [[ "$required" == "true" ]]; then
    echo "required"
  else
    echo "optional"
  fi
}

record_gate() {
  local gate="$1"
  local status="$2"
  local mode="$3"
  local reason="$4"
  printf '%s\t%s\t%s\t%s\n' "$gate" "$status" "$mode" "$reason" >> "$GATE_LOG"
}

write_artifact() {
  local end_ts duration
  end_ts="$(date -Iseconds)"
  duration="$(( $(date +%s) - $(date -d "$START_TS" +%s 2>/dev/null || date +%s) ))"

  python3 - "$GATE_LOG" "$ARTIFACT_PATH" "$RUN_SUMMARY_PATH" "$RUN_ID" "$START_TS" "$end_ts" "$duration" "$OVERALL_STATUS" \
    "$PRODUCTION_POLICY_REQUIRED" "$CREDENTIAL_HARDENING_REQUIRED" "$ZABBIX_PREFLIGHT_REQUIRED" "$SMTP_PREFLIGHT_REQUIRED" \
    "$ZABBIX_AUTH" "$SMTP_AUTH" "$VM_COUNT" "$MAIL_SENT" "$ERROR_COUNT" <<'PY'
import json
import sys

(
 gate_log, artifact_path, run_summary_path, run_id, ts_start, ts_end, duration_sec, overall,
 production_policy_required, cred_required, zbx_required, smtp_required,
 zabbix_auth, smtp_auth, vm_count, mail_sent, error_count,
) = sys.argv[1:]

def mode(v):
    return "required" if str(v).lower() == "true" else "optional"

gates = []
with open(gate_log, "r", encoding="utf-8") as fh:
    for line in fh:
        line = line.rstrip("\n")
        if not line:
            continue
        gate, status, gate_mode, reason = line.split("\t", 3)
        gates.append({
            "gate": gate,
            "status": status,
            "mode": gate_mode,
            "reason": reason,
        })

artifact = {
    "run_id": run_id,
    "timestamp_start": ts_start,
    "timestamp_end": ts_end,
    "duration_sec": int(duration_sec) if str(duration_sec).isdigit() else None,
    "overall_status": overall,
    "mode": {
        "production_policy": mode(production_policy_required),
        "credential_hardening": mode(cred_required),
        "zabbix_preflight": mode(zbx_required),
        "smtp_preflight": mode(smtp_required),
    },
    "summary": {
        "zabbix_auth": zabbix_auth,
        "smtp_auth": smtp_auth,
        "vm_count": int(vm_count) if str(vm_count).isdigit() else 0,
        "mail_sent": mail_sent,
        "error_count": int(error_count) if str(error_count).isdigit() else 0,
    },
    "gates": gates,
}

with open(artifact_path, "w", encoding="utf-8") as fh:
    json.dump(artifact, fh, ensure_ascii=False, indent=2)

run_summary = {
    "run_id": run_id,
    "timestamp_start": ts_start,
    "timestamp_end": ts_end,
    "duration_sec": int(duration_sec) if str(duration_sec).isdigit() else None,
    "overall_status": overall,
    "zabbix_auth": zabbix_auth,
    "smtp_auth": smtp_auth,
    "vm_count": int(vm_count) if str(vm_count).isdigit() else 0,
    "mail_sent": mail_sent,
    "error_count": int(error_count) if str(error_count).isdigit() else 0,
}

with open(run_summary_path, "w", encoding="utf-8") as fh:
    json.dump(run_summary, fh, ensure_ascii=False, indent=2)

print(artifact_path)
PY
}

finalize() {
  local artifact
  artifact="$(write_artifact)"
  echo "[ARTIFACT] $artifact"
}
trap finalize EXIT

run_gate_cmd() {
  local gate="$1" required="$2" cmd="$3" out_file="$4"
  local mode
  mode="$(mode_of "$required")"
  echo "[GATE] $gate mode=$mode"

  if bash -c "$cmd" > "$out_file" 2>&1; then
    record_gate "$gate" "pass" "$mode" "ok"
    return 0
  fi

  local reason
  reason="$(tail -n 5 "$out_file" | tr '\n' ';' | sed 's/"/\\"/g')"
  if [[ "$mode" == "optional" ]]; then
    record_gate "$gate" "warn" "$mode" "optional_failed: $reason"
    return 0
  fi

  record_gate "$gate" "fail" "$mode" "$reason"
  OVERALL_STATUS="FAIL"
  ERROR_COUNT=$((ERROR_COUNT + 1))
  exit 1
}

# Gate 1: Compile
run_gate_cmd "Compile" "true" "python3 -m py_compile daily_report.py mobile_api.py load_env.py generate_service_health_report.py generate_vm_infrastructure_report.py" "$(mktemp)"

# Gate 2: Secret scan (best effort)
if command -v gitleaks >/dev/null 2>&1; then
  run_gate_cmd "SecretScan" "true" "gitleaks detect --source . --no-git --verbose" "$(mktemp)"
else
  record_gate "SecretScan" "warn" "optional" "gitleaks_not_installed"
fi

# Gate 3: Production policy preflight
OUT3="$(mktemp)"
run_gate_cmd "ProductionPolicyPreflight" "$PRODUCTION_POLICY_REQUIRED" "./scripts/production_policy_preflight.sh" "$OUT3"

# Gate 4: Credential hardening preflight
OUT4="$(mktemp)"
run_gate_cmd "CredentialHardeningPreflight" "$CREDENTIAL_HARDENING_REQUIRED" "./scripts/credential_hardening_preflight.sh" "$OUT4"

# Gate 5: Zabbix preflight
OUT5="$(mktemp)"
run_gate_cmd "ZabbixPreflight" "$ZABBIX_PREFLIGHT_REQUIRED" "./scripts/zabbix_preflight.sh" "$OUT5"
if [[ -s "$OUT5" ]]; then
  ZABBIX_AUTH="$(python3 - <<'PY' "$OUT5"
import json,sys
try:
    raw = open(sys.argv[1], 'r', encoding='utf-8').read().strip().splitlines()
    payload = raw[-1] if raw else "{}"
    d=json.loads(payload)
    print('pass' if d.get('connected') else 'fail')
except Exception:
    print('unknown')
PY
)"
  VM_COUNT="$(python3 - <<'PY' "$OUT5"
import json,sys
try:
    raw = open(sys.argv[1], 'r', encoding='utf-8').read().strip().splitlines()
    payload = raw[-1] if raw else "{}"
    d=json.loads(payload)
    print(int(d.get('vm_count',0)))
except Exception:
    print(0)
PY
)"
fi

# Gate 6: SMTP preflight
OUT6="$(mktemp)"
run_gate_cmd "SMTPPreflight" "$SMTP_PREFLIGHT_REQUIRED" "./scripts/smtp_preflight.sh" "$OUT6"
if [[ -s "$OUT6" ]]; then
  SMTP_AUTH="$(python3 - <<'PY' "$OUT6"
import json,sys
try:
    raw = open(sys.argv[1], 'r', encoding='utf-8').read().strip().splitlines()
    payload = raw[-1] if raw else "{}"
    d=json.loads(payload)
    print('pass' if d.get('authenticated') else 'fail')
except Exception:
    print('unknown')
PY
)"
fi

# Gate 7: Config contract
run_gate_cmd "ConfigContract" "true" "python3 ./scripts/config_contract_test.py" "$(mktemp)"

# Gate 8: Service health contract
run_gate_cmd "ContractServiceHealth" "true" "python3 ./scripts/contract_test_service_health.py" "$(mktemp)"

# Gate 9: Smoke
OUT8="$(mktemp)"
run_gate_cmd "SmokeReports" "true" "python3 ./scripts/smoke_test_reports.py" "$OUT8"
if [[ -s "$OUT8" ]]; then
  VM_COUNT_SMOKE="$(python3 - <<'PY' "$OUT8"
import json,sys
try:
    raw = open(sys.argv[1], 'r', encoding='utf-8').read().strip().splitlines()
    payload = raw[-1] if raw else "{}"
    d=json.loads(payload)
    print(int(d.get('vm_count',0)))
except Exception:
    print(0)
PY
)"
  if [[ "$VM_COUNT_SMOKE" =~ ^[0-9]+$ ]] && (( VM_COUNT_SMOKE > VM_COUNT )); then
    VM_COUNT="$VM_COUNT_SMOKE"
  fi

  if [[ "$ZABBIX_PREFLIGHT_REQUIRED" == "true" ]]; then
    REQUIRED_OK="$(python3 - <<'PY' "$OUT8"
import json,sys
try:
    raw = open(sys.argv[1], 'r', encoding='utf-8').read().strip().splitlines()
    payload = raw[-1] if raw else "{}"
    d=json.loads(payload)
    ok = bool(d.get('zabbix_connected')) and int(d.get('vm_count',0)) > 0 and d.get('source') == 'zabbix'
    print('true' if ok else 'false')
except Exception:
    print('false')
PY
)"
    if [[ "$REQUIRED_OK" != "true" ]]; then
      record_gate "SmokeReportsDataCheck" "fail" "required" "required real vm data check failed"
      OVERALL_STATUS="FAIL"
      ERROR_COUNT=$((ERROR_COUNT + 1))
      exit 1
    else
      record_gate "SmokeReportsDataCheck" "pass" "required" "real vm data validated"
    fi
  fi
fi

# Gate 10: Ops dry run
run_gate_cmd "OpsDryRun" "true" "./scripts/ops_dry_run.sh" "$(mktemp)"

if [[ "$OVERALL_STATUS" == "PASS" ]]; then
  MAIL_SENT="dry_run"
  echo "[RESULT] PASS"
else
  echo "[RESULT] FAIL"
fi
