#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${1:-.}"
cd "$ROOT_DIR"

python3 - <<'PY'
import os
from load_env import load_env_file

load_env_file()

required_mode = os.getenv("PRODUCTION_POLICY_REQUIRED", "false").lower() == "true"

checks = []
issues = []


def expect(name, expected):
    value = (os.getenv(name) or "").strip().lower()
    checks.append((name, value, expected))
    if value != expected:
        issues.append(f"{name} must be '{expected}' (current='{value or 'unset'}')")

expect("ENABLE_STRICT_ENV_GUARD", "true")
expect("CREDENTIAL_HARDENING_REQUIRED", "true")
expect("ZABBIX_PREFLIGHT_REQUIRED", "true")
expect("EMAIL_DRY_RUN", "false")
expect("ENABLE_LEGACY_EMAIL_FIX", "false")

# Base field checks
if not (os.getenv("TO_EMAILS") or "").strip():
    issues.append("TO_EMAILS must not be empty")

smtp_port_raw = (os.getenv("SMTP_PORT") or "").strip()
if smtp_port_raw:
    try:
        smtp_port = int(smtp_port_raw)
        if smtp_port < 1 or smtp_port > 65535:
            issues.append("SMTP_PORT must be in range 1..65535")
    except ValueError:
        issues.append("SMTP_PORT must be integer")
else:
    issues.append("SMTP_PORT missing")

# Zabbix credential hygiene
z_user = (os.getenv("ZABBIX_USER") or "").strip().lower()
z_pass = (os.getenv("ZABBIX_PASS") or "").strip().lower()
default_users = {"admin", "test", "administrator"}
default_passwords = {"zabbix", "test", "admin", "password", "123456"}
if z_user in default_users:
    issues.append("ZABBIX_USER appears default-like")
if z_pass in default_passwords:
    issues.append("ZABBIX_PASS appears default-like")
if len(z_pass) < 8:
    issues.append("ZABBIX_PASS length must be >= 8")

if issues:
    print("Production policy preflight: FAIL")
    for item in issues:
        print(" -", item)
    if required_mode:
        raise SystemExit(1)
    print("Production policy preflight: WARN only (set PRODUCTION_POLICY_REQUIRED=true to enforce)")
else:
    print("Production policy preflight: PASS")
PY
