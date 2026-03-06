#!/usr/bin/env bash
set -euo pipefail

python3 - <<'PY'
import json
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

required = os.getenv("PRODUCTION_POLICY_REQUIRED", "false").lower() == "true"
mode = "required" if required else "optional"

violations = []

if os.getenv("CREDENTIAL_HARDENING_REQUIRED", "false").lower() != "true":
    violations.append("CREDENTIAL_HARDENING_REQUIRED must be true")
if os.getenv("ZABBIX_PREFLIGHT_REQUIRED", "false").lower() != "true":
    violations.append("ZABBIX_PREFLIGHT_REQUIRED must be true")
if os.getenv("SMTP_PREFLIGHT_REQUIRED", "false").lower() != "true":
    violations.append("SMTP_PREFLIGHT_REQUIRED must be true")
if os.getenv("ENABLE_LEGACY_EMAIL_FIX", "false").lower() == "true":
    violations.append("ENABLE_LEGACY_EMAIL_FIX must be false")
if required and os.getenv("EMAIL_DRY_RUN", "true").lower() != "false":
    violations.append("EMAIL_DRY_RUN must be false in required production mode")

status = "pass"
reason = "production policy check ok"
if violations:
    status = "fail" if required else "warn"
    reason = "; ".join(violations)

print(json.dumps({
    "status": status,
    "mode": mode,
    "reason": reason,
}, ensure_ascii=False))

if status == "fail":
    sys.exit(1)
PY
