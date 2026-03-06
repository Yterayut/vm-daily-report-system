#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

python3 - <<'PY'
import os
import sys
from pathlib import Path

root = Path.cwd()
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

try:
    from load_env import load_env_file
    load_env_file()
except Exception:
    pass

errors = []

def check_true(key: str):
    val = os.getenv(key, "false")
    if val.strip().lower() != "true":
        errors.append(f"{key} must be true (current='{val}')")

check_true("PRODUCTION_POLICY_REQUIRED")
check_true("CREDENTIAL_HARDENING_REQUIRED")
check_true("ZABBIX_PREFLIGHT_REQUIRED")
check_true("SMTP_PREFLIGHT_REQUIRED")

email_dry_run = os.getenv("EMAIL_DRY_RUN", "false")
if email_dry_run.strip().lower() != "false":
    errors.append(f"EMAIL_DRY_RUN must be false for production run (current='{email_dry_run}')")

if os.getenv("ENABLE_LEGACY_EMAIL_FIX", "false").strip().lower() == "true":
    errors.append("ENABLE_LEGACY_EMAIL_FIX must be false")

if errors:
    print("Production lockdown preflight: FAIL")
    for e in errors:
        print(f" - {e}")
    sys.exit(1)

print("Production lockdown preflight: PASS")
PY
