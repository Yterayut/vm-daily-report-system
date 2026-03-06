# Phase 8 Spec: Production Ops Rollout (Retention + Gate Alert + Verification)

Version: v1.0
Date: 2026-03-06

## Objective
- Operationalize production controls introduced earlier.
- Provide safe rollout for retention scheduling.
- Provide deterministic verification checklist after deploy.
- Provide a no-risk test path for gate-failure alert.

## Scope
- Add `scripts/install_retention_cron.sh`
- Add `scripts/post_deploy_verify.sh`
- Add `scripts/test_gate_failure_alert.sh`
- Update `scripts/notify_gate_failure.py` to support dry-run test mode
- Update `docs/PRODUCTION_RUNBOOK.md`

## Requirements Mapping
1. Retention schedule safe rollout
- Cron install script supports dry-run by default
- Apply mode explicitly required

2. Gate failure alert rollout
- Test script writes synthetic failed gate artifact
- Alert script supports dry-run mode via env

3. Post-deploy verification
- Machine-assisted checks for latest artifacts and status fields

## Safety
- No destructive change by default
- No real alert email during test unless explicitly enabled

## Validation
- `bash -n` all shell scripts
- `python3 -m py_compile scripts/notify_gate_failure.py`
- `install_retention_cron.sh` dry-run output check
- `test_gate_failure_alert.sh` dry-run output check
- `post_deploy_verify.sh` execution and report
