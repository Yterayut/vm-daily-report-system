# Production Lockdown Spec (Phase 1-5)

Version: v1.0
Date: 2026-03-06

## Goals
- Enforce strict production gates and runtime posture.
- Ensure production job sends real email (`EMAIL_DRY_RUN=false`) unless explicitly dry-run.
- Add safe retention schedule workflow (dry-run first).
- Add gate-fail alerting with artifact references.
- Provide actionable branch protection policy artifacts.

## Scope
- `scripts/production_lockdown_preflight.sh` (new)
- `scripts/prod_run_daily_report.sh` (update)
- `scripts/run_retention_job.sh` (new)
- `scripts/notify_gate_failure.py` (new)
- `scripts/phase5_test_gate.sh` (update)
- `.env.prod.template` (update)
- `docs/PRODUCTION_LOCKDOWN_PHASE1_5_SPEC_v1_0.md` (new)
- `docs/BRANCH_PROTECTION_POLICY.md` (new)
- `.github/CODEOWNERS` (new)

## Requirement Mapping
1) Strict gates in production
- preflight requires:
  - `PRODUCTION_POLICY_REQUIRED=true`
  - `CREDENTIAL_HARDENING_REQUIRED=true`
  - `ZABBIX_PREFLIGHT_REQUIRED=true`
  - `SMTP_PREFLIGHT_REQUIRED=true`

2) Production email mode
- `prod_run_daily_report.sh` defaults to `EMAIL_DRY_RUN=false`
- `--dry-run` explicitly overrides to true

3) Retention schedule safe rollout
- `run_retention_job.sh` default dry-run
- apply only when `RETENTION_APPLY=true`

4) Alert on gate failure
- `phase5_test_gate.sh` calls `notify_gate_failure.py` on failure (opt-in)

5) GitHub protection policy
- add `docs/BRANCH_PROTECTION_POLICY.md`
- add `.github/CODEOWNERS` to support required reviews

## Validation
- `bash -n` for new shell scripts
- `python3 -m py_compile` for new python scripts
- `./scripts/production_lockdown_preflight.sh` pass/fail behavior
- `./scripts/prod_run_daily_report.sh --dry-run` still works
- `./scripts/run_retention_job.sh` dry-run generates report

## Non-goal
- No secret rotation in this phase (kept as current, per request)
