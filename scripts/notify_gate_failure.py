#!/usr/bin/env python3
"""Send lightweight gate failure alert via SMTP (opt-in)."""

from __future__ import annotations

import json
import os
import smtplib
from email.mime.text import MIMEText
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output"

if os.getenv("ENABLE_GATE_FAILURE_ALERTS", "false").lower() != "true":
    print("gate-failure-alert: disabled")
    raise SystemExit(0)

latest = sorted(OUT.glob("test_gate_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
if not latest:
    print("gate-failure-alert: no gate artifact")
    raise SystemExit(0)

artifact = latest[0]
try:
    payload = json.loads(artifact.read_text(encoding="utf-8"))
except Exception:
    print("gate-failure-alert: cannot parse artifact")
    raise SystemExit(0)

if str(payload.get("overall_status", "")).upper() == "PASS":
    print("gate-failure-alert: gate passed")
    raise SystemExit(0)

smtp_server = os.getenv("SMTP_SERVER", "")
smtp_port = int(os.getenv("SMTP_PORT", "587"))
username = os.getenv("EMAIL_USERNAME", "")
password = os.getenv("EMAIL_PASSWORD", "")
recipient = os.getenv("GATE_ALERT_EMAIL", os.getenv("TO_EMAILS", "").split(",")[0].strip())
sender = os.getenv("SENDER_EMAIL", username)

if os.getenv("GATE_ALERT_DRY_RUN", "false").lower() == "true":
    print(f"gate-failure-alert: dry-run -> would send to {recipient or '<missing-recipient>'}")
    print(f"gate-failure-alert: artifact={artifact}")
    raise SystemExit(0)

if not all([smtp_server, username, password, recipient, sender]):
    print("gate-failure-alert: missing SMTP settings or recipient")
    raise SystemExit(0)

subject = f"[ALERT] Phase5 Gate FAILED ({payload.get('run_id', 'unknown')})"
body = (
    f"Gate failed\n"
    f"Run ID: {payload.get('run_id')}\n"
    f"Status: {payload.get('overall_status')}\n"
    f"Artifact: {artifact}\n"
    f"Summary: {json.dumps(payload.get('summary', {}), ensure_ascii=False)}\n"
)

msg = MIMEText(body, "plain", "utf-8")
msg["Subject"] = subject
msg["From"] = sender
msg["To"] = recipient

try:
    with smtplib.SMTP(smtp_server, smtp_port, timeout=20) as smtp:
        smtp.starttls()
        smtp.login(username, password)
        smtp.send_message(msg)
    print(f"gate-failure-alert: sent to {recipient}")
except Exception as exc:
    print(f"gate-failure-alert: failed to send ({exc})")
