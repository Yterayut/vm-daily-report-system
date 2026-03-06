#!/usr/bin/env python3
"""Config contract test with machine-readable output."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from load_env import load_env_file
    load_env_file()
except Exception:
    pass

REQUIRED = [
    "ZABBIX_URL",
    "ZABBIX_USER",
    "ZABBIX_PASS",
    "SMTP_SERVER",
    "SMTP_PORT",
    "EMAIL_USERNAME",
    "EMAIL_PASSWORD",
    "SENDER_EMAIL",
]

errors: List[str] = []
warnings: List[str] = []

for k in REQUIRED:
    if not os.getenv(k, "").strip():
        errors.append(f"missing required key: {k}")

smtp_port_raw = os.getenv("SMTP_PORT", "")
if smtp_port_raw:
    try:
        port = int(smtp_port_raw)
        if port < 1 or port > 65535:
            errors.append("SMTP_PORT out of range 1..65535")
    except ValueError:
        errors.append("SMTP_PORT must be numeric")

email_dry_run = os.getenv("EMAIL_DRY_RUN", "true").strip().lower() == "true"
to_emails = [x.strip() for x in os.getenv("TO_EMAILS", "").split(",") if x.strip()]
if not email_dry_run and not to_emails:
    errors.append("TO_EMAILS must not be empty when EMAIL_DRY_RUN=false")

legacy_fix = os.getenv("ENABLE_LEGACY_EMAIL_FIX", "false").strip().lower() == "true"
if legacy_fix:
    warnings.append("ENABLE_LEGACY_EMAIL_FIX=true (not recommended)")

status = "pass" if not errors else "fail"
result = {
    "status": status,
    "errors": errors,
    "warnings": warnings,
}
print(json.dumps(result, ensure_ascii=False))

if status != "pass":
    sys.exit(1)
