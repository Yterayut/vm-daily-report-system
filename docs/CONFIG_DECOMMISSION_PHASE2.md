# Config Decommission Phase 2

Date: 2026-03-06

## What changed
- Upgraded inventory rules to detect more legacy candidates.
- Added confidence-based recommendation levels:
  - `keep`
  - `archive_safe` (high confidence)
  - `archive_review`
  - `manual_review`
- Decommission script now archives only `archive_safe` with confidence >= 90.

## Safety
- Default mode is dry-run.
- No deletion; archive move only.
- `.env` and core runtime files are never auto-archived.

## Commands
- Build inventory:
  - `python3 scripts/config_inventory.py`
- Dry-run archive batch:
  - `./scripts/config_decommission.sh`
- Apply archive batch:
  - `./scripts/config_decommission.sh apply`
