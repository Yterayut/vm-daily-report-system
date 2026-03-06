#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${1:-.}"
cd "$ROOT_DIR"

python3 - <<'PY'
import os
import smtplib
from load_env import load_env_file

load_env_file()

required = ["SMTP_SERVER", "SMTP_PORT", "EMAIL_USERNAME", "EMAIL_PASSWORD"]
missing = [k for k in required if not os.getenv(k)]
if missing:
    print("FAIL: missing required env vars:", ", ".join(missing))
    raise SystemExit(1)

smtp_server = os.getenv("SMTP_SERVER", "")
smtp_port = int(os.getenv("SMTP_PORT", "587"))
username = os.getenv("EMAIL_USERNAME", "")
password = os.getenv("EMAIL_PASSWORD", "")
use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"

timeout = int(os.getenv("SMTP_TIMEOUT", "30"))

print("SMTP preflight: server={} port={} tls={} user={}".format(
    smtp_server, smtp_port, use_tls, username
))

try:
    with smtplib.SMTP(smtp_server, smtp_port, timeout=timeout) as server:
        server.ehlo()
        if use_tls:
            server.starttls()
            server.ehlo()
        server.login(username, password)
    print("PASS: SMTP authentication successful")
except Exception as e:
    print("FAIL: SMTP authentication failed:", e)
    raise SystemExit(1)
PY
