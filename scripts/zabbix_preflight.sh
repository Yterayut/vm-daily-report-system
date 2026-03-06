#!/usr/bin/env bash
set -euo pipefail

MODE="optional"
if [[ "${ZABBIX_PREFLIGHT_REQUIRED:-false}" == "true" ]]; then
  MODE="required"
fi

python3 - <<'PY'
import json
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

result = {
    "status": "pass",
    "mode": "optional",
    "connected": False,
    "vm_count": 0,
    "source": "zabbix",
    "reason": "",
}

try:
    from fetch_zabbix_data import EnhancedZabbixClient
    client = EnhancedZabbixClient()
    ok = client.connect()
    result["connected"] = bool(ok)
    if ok:
        hosts = client.fetch_hosts() or []
        result["vm_count"] = len(hosts)
        result["reason"] = f"connected, vm_count={len(hosts)}"
    else:
        result["status"] = "fail"
        result["reason"] = "zabbix connect failed"
    try:
        client.disconnect()
    except Exception:
        pass
except Exception as exc:
    result["status"] = "fail"
    result["reason"] = f"preflight error: {exc}"

print(json.dumps(result, ensure_ascii=False))

if result["status"] == "fail":
    sys.exit(1)
PY
