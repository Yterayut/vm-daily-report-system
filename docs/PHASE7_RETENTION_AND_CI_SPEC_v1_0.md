# Phase 7 Spec: Retention Policy + CI Run Summary Artifact

Version: v1.0
Date: 2026-03-06

## Objective
- Add deterministic retention cleanup for operational artifacts.
- Ensure CI uploads both gate artifact and daily run summary artifact.

## Scope
- Add `scripts/cleanup_artifacts_retention.sh`
- Update `.github/workflows/phase5-test-gate.yml`
- Add this spec doc

## Retention Policy
Default retention days: `90`

Targets (allowlist):
- `output/test_gate_*.json`
- `output/run_summary_*.json`
- `output/config_inventory_*.json`
- `output/config_inventory_*.md`
- `output/config_decommission_*.txt`
- `output/delete_quarantine_*.txt`

Modes:
- `dry-run` (default): list candidates only
- `apply`: delete only allowlisted files older than retention

Safety:
- No wildcard delete outside allowlist
- Works only in declared target dirs (default: `output`)
- Emits cleanup report to `output/cleanup_retention_<timestamp>.txt`

## CI Changes
In `phase5-test-gate.yml` upload step:
- Keep `output/test_gate_*.json`
- Add `output/run_summary_*.json`

## Validation
- `bash -n scripts/cleanup_artifacts_retention.sh`
- Dry-run against synthetic old/new files
- Apply mode on synthetic files only
- Verify CI yaml syntax remains valid
