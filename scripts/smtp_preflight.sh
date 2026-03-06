#!/usr/bin/env bash
set -euo pipefail

python3 - <<'PY'
import json
import os
import smtplib
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

server = os.getenv("SMTP_SERVER", "")
port_raw = os.getenv("SMTP_PORT", "587")
username = os.getenv("EMAIL_USERNAME", "")
password = os.getenv("EMAIL_PASSWORD", "")
use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"

result = {
    "status": "pass",
    "authenticated": False,
    "reason": "",
}

try:
    port = int(port_raw)
except ValueError:
    result["status"] = "fail"
    result["reason"] = "SMTP_PORT must be numeric"
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(1)

if not server or not username or not password:
    result["status"] = "fail"
    result["reason"] = "missing SMTP_SERVER/EMAIL_USERNAME/EMAIL_PASSWORD"
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(1)

try:
    with smtplib.SMTP(server, port, timeout=20) as smtp:
        smtp.ehlo()
        if use_tls:
            smtp.starttls()
            smtp.ehlo()
        smtp.login(username, password)
    result["authenticated"] = True
    result["reason"] = "smtp login success"
except Exception as exc:
    result["status"] = "fail"
    result["reason"] = f"smtp auth failed: {exc}"

print(json.dumps(result, ensure_ascii=False))
if result["status"] == "fail":
    sys.exit(1)
PY
