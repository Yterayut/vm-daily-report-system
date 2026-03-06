# Config Decommission Phase 3 Spec

Version: v1.0
Date: 2026-03-06

## Objective
- Move from archive-only cleanup to controlled delete after quarantine.
- Add config contract test for pre-run validation and deterministic failure reasons.

## Scope
- Add `scripts/config_contract_test.py`
- Add `scripts/delete_quarantined_batch.sh`
- Add this spec doc

## Safety Policy
- Deletion is never default; dry-run is default mode.
- Delete only inside `archive/config_decommission_*`.
- Require explicit confirmation string to apply delete.
- Require quarantine age threshold before delete.
- Always write manifest/report to `output/`.

## Config Contract Rules
- Required keys: `ZABBIX_URL`, `ZABBIX_USER`, `ZABBIX_PASS`, `SMTP_SERVER`, `SMTP_PORT`, `EMAIL_USERNAME`, `EMAIL_PASSWORD`, `SENDER_EMAIL`.
- `SMTP_PORT` must be numeric and 1..65535.
- When `EMAIL_DRY_RUN=false`, `TO_EMAILS` must not be empty.
- Emit JSON with `status`, `errors`, `warnings`.

## Delete After Quarantine Rules
- Candidate directories: `archive/config_decommission_*`
- Directory age must be >= `MIN_AGE_HOURS` (default 24)
- Apply mode requires:
  - arg1 = `apply`
  - arg2 = `DELETE`
- Dry-run prints candidate files and writes report only.

## Rollback
- Before delete, keep manifests from archive/apply phase.
- If uncertain, keep in archive and do not apply delete.

## Exit Criteria
- Contract test returns pass for current runtime config.
- Delete script dry-run works and lists eligible candidates.
- Apply delete works with explicit confirmation and reports deleted count.
