# Production Sign-off Checklist

Date: 2026-03-12  
Project: vm-daily-report-system  
Scope: Phase 1-8 rollout validation (ops + gate + retention + alert)

## 1) GitHub Protection and CI

- [ ] Branch protection enforced on `main` in GitHub settings
- [ ] Required checks configured:
  - [ ] `phase5-test-gate / gate (soft)`
  - [ ] `phase5-test-gate / gate (strict)`
- [x] `.github/CODEOWNERS` exists in repository
- [x] Workflow uploads both artifacts:
  - [x] `output/test_gate_*.json`
  - [x] `output/run_summary_*.json`

Status: **Partial** (needs GitHub admin action; local agent cannot apply settings without admin token/CLI access)

## 2) Controlled Production Rollout

- [x] Retention dry-run executed (`./scripts/run_retention_job.sh`)
- [x] Retention apply executed (`RETENTION_APPLY=true ./scripts/run_retention_job.sh`)
- [x] Retention cron dry-run preview executed (`./scripts/install_retention_cron.sh`)
- [x] Retention cron installed (`./scripts/install_retention_cron.sh apply`)
- [x] Crontab entry present (`15 2 * * * ... run_retention_job.sh ...`)
- [x] Gate failure alert dry-run test executed (`./scripts/test_gate_failure_alert.sh`)
- [x] Gate failure alert real-send test executed (via env-loaded wrapper)

Evidence:
- `output/cleanup_retention_20260312_115222.txt`
- `output/test_gate_99999999_000000_000000000_0000000.json`

Status: **Done** (with real-send test successful)

## 3) Verification Suite

- [x] Shell syntax checks (`bash -n`) passed for gate/ops/decommission scripts
- [x] Python compile checks passed for:
  - `scripts/notify_gate_failure.py`
  - `scripts/config_contract_test.py`
  - `load_env.py`, `daily_report.py`, `mobile_api.py`, `service_health_checker.py`, `service_health_monitor.py`
- [x] Phase5 gate soft mode passed
- [ ] Phase5 gate strict mode passed
- [x] `run_summary_2026-03-12.json` exists and schema-valid
- [x] Post-deploy verify passed
- [x] API smoke checks repeated 3 times:
  - `/api/services/health`
  - `/api/services/summary`
- [x] Service monitor dry-run checks:
  - `python3 service_health_monitor.py --dry-run`
  - `python3 service_health_monitor.py --test`

Evidence:
- `output/test_gate_20260312_114946_734107974_1071711.json` (soft pass)
- `output/test_gate_20260312_115258_387549233_1073391.json` (soft pass latest)
- `output/run_summary_2026-03-12.json` (PASS)
- `output/post_deploy_verify_20260312_115336.txt` (PASS)

Status: **Mostly done**

## 4) Known Blockers

1. Strict gate currently fails at `CredentialHardeningPreflight` due default-like runtime credentials:
   - `ZABBIX_USER appears default-like`
   - `ZABBIX_PASS appears default-like`
2. Direct production run (`./scripts/prod_run_daily_report.sh`) fails strict runtime guard for same reason.
3. GitHub branch protection enforcement is pending admin-side configuration.

## 5) Release Decision

- Overall: **Conditional Go**
- Go conditions before final PRD sign-off:
  1. Replace strict-sensitive credentials in `.env` with non-default production values.
  2. Re-run strict gate until PASS.
  3. Apply and verify branch protection required checks on GitHub.

