#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${1:-.}"
cd "$ROOT_DIR"

python3 - <<'PY'
import os
from pyzabbix import ZabbixAPI
from load_env import load_env_file

load_env_file()

required = ["ZABBIX_URL", "ZABBIX_USER", "ZABBIX_PASS"]
missing = [k for k in required if not os.getenv(k)]
if missing:
    print("FAIL: missing required env vars:", ", ".join(missing))
    raise SystemExit(1)

url = os.getenv("ZABBIX_URL", "")
user = os.getenv("ZABBIX_USER", "")
password = os.getenv("ZABBIX_PASS", "")
timeout = int(os.getenv("ZABBIX_TIMEOUT", "30"))

print("Zabbix preflight: url={} user={} timeout={}".format(url, user, timeout))

try:
    zapi = ZabbixAPI(url)
    zapi.timeout = timeout
    zapi.login(user=user, password=password)
    hosts = zapi.host.get(output=["hostid"], limit=1)
    print("PASS: Zabbix authentication successful, host_probe_count={}".format(len(hosts)))
except Exception as e:
    msg = str(e)
    print("FAIL: Zabbix authentication failed:", msg)
    if "Incorrect user name or password" in msg or "temporarily blocked" in msg:
        print("HINT: verify ZABBIX_USER/ZABBIX_PASS and ensure account is not locked.")
        print("HINT: current user='{}'".format(user))
    if user.strip().lower() in {"test", "admin"} and password.strip().lower() in {"test", "zabbix"}:
        print("HINT: detected default-like credentials; replace with real service account.")
    raise SystemExit(1)
PY
