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

required = os.getenv("CREDENTIAL_HARDENING_REQUIRED", "false").lower() == "true"
mode = "required" if required else "optional"

issues = []

def is_default_like(value: str) -> bool:
    if not value:
        return True
    low = value.strip().lower()
    blacklist = {
        "admin",
        "zabbix",
        "changeme",
        "your_password",
        "your_username",
        "your_email@gmail.com",
    }
    return low in blacklist or "example" in low

if is_default_like(os.getenv("ZABBIX_USER", "")):
    issues.append("ZABBIX_USER appears default-like")
if is_default_like(os.getenv("ZABBIX_PASS", "")):
    issues.append("ZABBIX_PASS appears default-like")
if is_default_like(os.getenv("EMAIL_USERNAME", "")):
    issues.append("EMAIL_USERNAME appears default-like")
if not os.getenv("EMAIL_PASSWORD", "").strip():
    issues.append("EMAIL_PASSWORD missing")
if os.getenv("ENABLE_LEGACY_EMAIL_FIX", "false").lower() == "true":
    issues.append("ENABLE_LEGACY_EMAIL_FIX must be false")

status = "pass"
reason = "credential policy ok"
if issues:
    status = "fail" if required else "warn"
    reason = "; ".join(issues)

print(json.dumps({
    "status": status,
    "mode": mode,
    "reason": reason,
}, ensure_ascii=False))

if status == "fail":
    sys.exit(1)
PY
