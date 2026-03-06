# Phase 5 Test Gate

สคริปต์หลัก: `scripts/phase5_test_gate.sh`

## เป้าหมาย
- ตรวจ compile/smoke/contract/preflight ก่อน deploy
- รองรับโหมด `optional` และ `required` ต่อ gate
- สร้าง artifact JSON สำหรับ audit/rollback decision

## Gate Sequence
1. Compile (`required`)
2. Secret scan (`optional` ถ้าไม่มี `gitleaks`)
3. Production policy preflight (`PRODUCTION_POLICY_REQUIRED`)
4. Credential hardening preflight (`CREDENTIAL_HARDENING_REQUIRED`)
5. Zabbix preflight (`ZABBIX_PREFLIGHT_REQUIRED`)
6. SMTP preflight (`SMTP_PREFLIGHT_REQUIRED`)
7. Contract test `/api/services/health` (`required`)
8. Smoke report generation (`required`)
9. Ops dry-run (`required`)

## Real Data Enforcement
เมื่อ `ZABBIX_PREFLIGHT_REQUIRED=true` จะบังคับเพิ่มว่า:
- `zabbix_connected=true`
- `vm_count > 0`
- `source == "zabbix"`

ถ้าไม่ผ่านจะ fail gate ทันที แม้สร้าง PDF ได้

## Artifact
บันทึกที่ `output/test_gate_<run_id>.json`

โครงสร้างหลัก:
- `run_id`, `timestamp_start`, `timestamp_end`, `duration_sec`
- `mode.production_policy|credential_hardening|zabbix_preflight|smtp_preflight`
- `overall_status`
- `summary.zabbix_auth|smtp_auth|vm_count|mail_sent|error_count`
- `gates[]` (gate/status/mode/reason)

## ตัวอย่างการรัน
Soft mode:
```bash
PRODUCTION_POLICY_REQUIRED=false \
CREDENTIAL_HARDENING_REQUIRED=false \
ZABBIX_PREFLIGHT_REQUIRED=false \
SMTP_PREFLIGHT_REQUIRED=false \
./scripts/phase5_test_gate.sh .
```

Strict mode:
```bash
PRODUCTION_POLICY_REQUIRED=true \
CREDENTIAL_HARDENING_REQUIRED=true \
ZABBIX_PREFLIGHT_REQUIRED=true \
SMTP_PREFLIGHT_REQUIRED=true \
./scripts/phase5_test_gate.sh .
```
