#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${1:-.}"
cd "$ROOT_DIR"

python3 - <<'PY'
import os
from load_env import load_env_file

load_env_file()

required_mode = os.getenv("CREDENTIAL_HARDENING_REQUIRED", "false").lower() == "true"

user = (os.getenv("ZABBIX_USER") or "").strip()
password = (os.getenv("ZABBIX_PASS") or "").strip()

issues = []

if not user or not password:
    issues.append("ZABBIX_USER/ZABBIX_PASS missing")

default_users = {"admin", "test", "administrator"}
default_passwords = {"zabbix", "test", "admin", "password", "123456"}

if user.lower() in default_users:
    issues.append("ZABBIX_USER appears default-like ('{}')".format(user))

if password.lower() in default_passwords:
    issues.append("ZABBIX_PASS appears default-like")

if len(password) < 8:
    issues.append("ZABBIX_PASS length < 8")

if issues:
    print("Credential hardening preflight: FAIL")
    for item in issues:
        print(" - {}".format(item))
    if required_mode:
        raise SystemExit(1)
    print("Credential hardening preflight: WARN only (set CREDENTIAL_HARDENING_REQUIRED=true to enforce)")
else:
    print("Credential hardening preflight: PASS")
PY
