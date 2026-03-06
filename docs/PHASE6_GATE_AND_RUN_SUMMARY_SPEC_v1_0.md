# Phase 6 Spec: Gate Integration + Run Summary

Version: v1.0
Date: 2026-03-06

## Objective
- Enforce configuration contract in release gate before runtime smoke.
- Emit daily machine-readable run summary for operational tracking.

## Scope
- Update `scripts/phase5_test_gate.sh`
- Add this spec doc

## Changes
1. Add gate `ConfigContract` (required)
   - Runs `python3 scripts/config_contract_test.py`
   - Fails fast on config contract violations

2. Keep existing API contract + smoke gates
   - `ContractServiceHealth` remains required
   - Smoke remains required

3. Add run summary artifact
   - Path: `output/run_summary_<YYYY-MM-DD>.json`
   - Fields:
     - `run_id`
     - `timestamp_start`
     - `timestamp_end`
     - `duration_sec`
     - `overall_status`
     - `zabbix_auth`
     - `smtp_auth`
     - `vm_count`
     - `mail_sent`
     - `error_count`

## Safety
- Non-destructive change only.
- Existing gate artifact format retained.

## Validation
- `bash -n scripts/phase5_test_gate.sh`
- `python3 scripts/config_contract_test.py`
- `./scripts/phase5_test_gate.sh .` (soft mode)
- Verify `output/run_summary_<date>.json` exists and valid JSON
