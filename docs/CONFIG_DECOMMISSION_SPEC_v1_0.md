# Spec: Config Inventory & Safe Decommission

Version: v1.0  
Date: 2026-03-06  
Strategy: inventory-first, archive-before-delete, rollback-ready

## 1) Objective
- Identify config files that are active, legacy, or unknown.
- Prevent accidental deletion of runtime-critical files.
- Provide a safe archive workflow with dry-run default.

## 2) Scope
In scope:
- `scripts/config_inventory.py`
- `scripts/config_decommission.sh`
- `docs/CONFIG_DECOMMISSION_SPEC_v1_0.md`

Out of scope:
- Hard delete of files in this phase.
- Runtime refactor or service behavior changes.

## 3) Safety Rules
- Default mode is dry-run.
- Only files classified as `archive` are movable by automation.
- `.env` and core run/gate files are never auto-moved.
- Every move writes manifest for rollback.

## 4) Workflow
1. Run inventory:
   - `python3 scripts/config_inventory.py`
2. Review generated artifacts in `output/`:
   - `config_inventory_<timestamp>.json`
   - `config_inventory_<timestamp>.md`
3. Run decommission dry-run:
   - `./scripts/config_decommission.sh`
4. Apply archive move only after review:
   - `./scripts/config_decommission.sh apply output/config_inventory_<timestamp>.json`

## 5) Rollback
- Move files back from `archive/config_decommission_<timestamp>/`
- Use manifest file generated in output.

## 6) Exit Criteria
- Inventory artifact generated successfully.
- Decommission dry-run shows deterministic candidate list.
- Apply mode only moves `archive` candidates and writes manifest.
