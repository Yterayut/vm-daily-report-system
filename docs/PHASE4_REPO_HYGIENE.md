# Phase 4 Repo Hygiene (Safe Rollout)

Date: 2026-03-06

## Goal
- Reduce root-directory clutter without impacting runtime paths.
- Keep rollback easy by moving files only (no destructive delete).

## What This Phase Changes
- Adds a controlled cleanup script:
  - `scripts/repo_hygiene_phase4.sh`
- Moves legacy notes from root into:
  - `docs/legacy_notes/`
- Moves backup/misc clutter from root into:
  - `archive/legacy_root_cleanup/`
- Prevents accidental git inclusion of moved legacy notes:
  - `.gitignore` includes `docs/legacy_notes/`

## Why It Is Safe
- Runtime files in active flow are not moved:
  - `daily_report.py`
  - `mobile_api.py`
  - `generate_service_health_report.py`
  - `generate_vm_infrastructure_report.py`
  - `carbon_service_monitor.py`
  - `enhanced_alert_system.py`
  - `load_env.py`
- Script supports dry-run first:
  - `./scripts/repo_hygiene_phase4.sh`

## Runbook
1. Preview actions:
```bash
./scripts/repo_hygiene_phase4.sh
```
2. Apply moves:
```bash
./scripts/repo_hygiene_phase4.sh --apply
```
3. Validate runtime:
```bash
python3 -m py_compile daily_report.py mobile_api.py load_env.py
ENABLE_NEW_SERVICE_SOURCE=true EMAIL_DRY_RUN=true LINE_NOTIFICATIONS_ENABLED=false TO_EMAILS=yterayut@gmail.com python3 daily_report.py --simple
```

## Rollback
- Restore files from moved locations with `mv` back to root.
- Since cleanup is move-only, rollback does not require code revert.

## Scope Notes
- This phase intentionally does not delete files.
- Further cleanup of old scripts/tests should be a separate gated phase.
