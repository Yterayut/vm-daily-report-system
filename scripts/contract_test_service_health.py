#!/usr/bin/env python3
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

result = {
    "status": "pass",
    "reason": "",
    "required_keys": ["summary"],
    "checked_endpoint": "/api/services/health",
}

try:
    from mobile_api import app
except Exception as exc:
    result["status"] = "fail"
    result["reason"] = f"import mobile_api failed: {exc}"
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(1)

try:
    with app.test_client() as client:
        resp = client.get("/api/services/health")
        if resp.status_code != 200:
            raise RuntimeError(f"unexpected status={resp.status_code}")
        payload = resp.get_json(silent=True)
        if not isinstance(payload, dict):
            raise RuntimeError("payload is not an object")

        if "summary" not in payload:
            raise RuntimeError("missing summary")

        summary = payload.get("summary", {})
        # keep tolerant because legacy versions vary key names
        one_of_total = any(k in summary for k in ("total_services", "total", "total_count"))
        if not one_of_total:
            raise RuntimeError("summary missing total field")

        result["summary_keys"] = sorted(summary.keys())
        result["status_code"] = resp.status_code

except Exception as exc:
    result["status"] = "fail"
    result["reason"] = str(exc)
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(1)

print(json.dumps(result, ensure_ascii=False))
