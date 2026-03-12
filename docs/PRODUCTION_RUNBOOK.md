# Production Runbook

## Canonical command
- Standard run:
  - `./scripts/prod_run_daily_report.sh`
- Dry-run (no mail send expected if app respects `EMAIL_DRY_RUN`):
  - `./scripts/prod_run_daily_report.sh --dry-run`
- Strict env guard:
  - `./scripts/prod_run_daily_report.sh --strict`

## Cron recommendation
Use:
- `run_daily_report.sh`

This wrapper is project-relative and writes logs to:
- `logs/cron_daily_report.log`

## Preflight checks before production
1. `python3 -m py_compile load_env.py daily_report.py`
2. `./scripts/smtp_preflight.sh`
3. `./scripts/zabbix_preflight.sh`
4. `./scripts/phase5_test_gate.sh .`
5. `./scripts/production_lockdown_preflight.sh`

## Rollback
If strict guard blocks startup unexpectedly:
1. Set `ENABLE_STRICT_ENV_GUARD=false` in `.env`
2. Re-run `./scripts/prod_run_daily_report.sh`

If wrapper path fails:
1. Run direct fallback:
   - `python3 daily_report.py --simple`

## Temporary Strict Guard Exception (Zabbix default credentials)
- Purpose:
  - Allow strict-mode production run temporarily when `ZABBIX_USER`/`ZABBIX_PASS` are still default-like placeholders.
- Enable:
  - Set `ALLOW_DEFAULT_ZABBIX_CREDENTIALS=true` in `.env`
- Behavior:
  - Strict guard logs warnings for default-like Zabbix credentials, but does not abort startup.
- Exit this exception mode (required after credential rotation):
  1. Update `ZABBIX_USER` and `ZABBIX_PASS` to real non-default production values.
  2. Set `ALLOW_DEFAULT_ZABBIX_CREDENTIALS=false`.
  3. Re-run `./scripts/phase5_test_gate.sh .` and confirm strict checks pass.

## Non-destructive cleanup workflow
- Candidate listing only:
  - `./scripts/archive_legacy_candidates.sh`
- Apply move to archive folder:
  - `./scripts/archive_legacy_candidates.sh apply`

Moved files are stored under:
- `archive/legacy_candidates_<timestamp>/`

## Retention Job Rollout
- Install cron (dry-run preview):
  - `./scripts/install_retention_cron.sh`
- Install cron (apply):
  - `./scripts/install_retention_cron.sh apply`
- Runtime behavior:
  - default `RETENTION_APPLY=false` (dry-run)
  - set `RETENTION_APPLY=true` only after observation period

## Gate Failure Alert Rollout
- Test alert without sending real email:
  - `./scripts/test_gate_failure_alert.sh`
- Enable real alerts:
  - set `ENABLE_GATE_FAILURE_ALERTS=true`
  - set `GATE_ALERT_EMAIL=<ops_email>`
  - keep `GATE_ALERT_DRY_RUN=false`

## Post-Deploy Verification
- Run:
  - `./scripts/post_deploy_verify.sh`
- Output report:
  - `output/post_deploy_verify_<timestamp>.txt`
