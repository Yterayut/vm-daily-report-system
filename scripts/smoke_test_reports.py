#!/usr/bin/env python3
import json
import os
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

result = {
    "status": "pass",
    "reason": "",
    "vm_pdf": None,
    "service_pdf": None,
    "vm_count": 0,
    "zabbix_connected": False,
    "source": "unknown",
}

try:
    from load_env import load_env_file
    load_env_file()
except Exception:
    pass

try:
    from fetch_zabbix_data import EnhancedZabbixClient, calculate_enhanced_summary
except Exception as exc:
    result["status"] = "fail"
    result["reason"] = f"import fetch_zabbix_data failed: {exc}"
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(1)

# Step 1: collect VM data
vm_data = []
summary = {
    "total": 0,
    "online": 0,
    "offline": 0,
    "online_percent": 0.0,
    "offline_percent": 0.0,
    "performance": {
        "avg_cpu": 0.0,
        "avg_memory": 0.0,
        "avg_disk": 0.0,
        "peak_cpu": 0.0,
        "peak_memory": 0.0,
        "peak_disk": 0.0,
    },
    "alerts": {"critical": 0, "warning": 0, "ok": 0},
}

client = EnhancedZabbixClient()
try:
    connected = bool(client.connect())
    result["zabbix_connected"] = connected
    if connected:
        hosts = client.fetch_hosts() or []
        vm_data = client.enrich_host_data(hosts) if hosts else []
        result["vm_count"] = len(vm_data)
        result["source"] = "zabbix"
        if vm_data:
            summary = calculate_enhanced_summary(vm_data)
    else:
        result["source"] = "fallback"
except Exception as exc:
    result["source"] = "fallback"
    result["reason"] = f"zabbix error: {exc}"
finally:
    try:
        client.disconnect()
    except Exception:
        pass

if not vm_data:
    # deterministic fallback dataset for smoke
    vm_data = [{
        "name": "smoke-vm-1",
        "hostname": "smoke-vm-1",
        "status": 0,
        "available": 1,
        "cpu_load": 12.5,
        "memory_used": 30.0,
        "disk_used": 25.0,
        "ip": "127.0.0.1",
    }]
    summary = {
        "total": 1,
        "online": 1,
        "offline": 0,
        "online_percent": 100.0,
        "offline_percent": 0.0,
        "performance": {
            "avg_cpu": 12.5,
            "avg_memory": 30.0,
            "avg_disk": 25.0,
            "peak_cpu": 12.5,
            "peak_memory": 30.0,
            "peak_disk": 25.0,
        },
        "alerts": {"critical": 0, "warning": 0, "ok": 1},
    }

required_real = os.getenv("ZABBIX_PREFLIGHT_REQUIRED", "false").lower() == "true"
if required_real and (not result["zabbix_connected"] or result["source"] != "zabbix"):
    result["status"] = "fail"
    result["reason"] = "required real data mode but zabbix not connected"
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(1)
if required_real and result["vm_count"] <= 0:
    result["status"] = "fail"
    result["reason"] = "required real data mode but vm_count=0"
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(1)

# Step 2: generate reports
output_dir = Path(os.getenv("REPORT_OUTPUT_DIR", "output"))
template_dir = Path(os.getenv("REPORT_TEMPLATE_DIR", "templates"))
static_dir = Path(os.getenv("REPORT_STATIC_DIR", "static"))
output_dir.mkdir(parents=True, exist_ok=True)

try:
    from generate_vm_infrastructure_report import VMInfrastructureReportGenerator
    vm_generator = VMInfrastructureReportGenerator(
        template_dir=str(template_dir),
        output_dir=str(output_dir),
        static_dir=str(static_dir),
    )
    vm_filename = f"VM_Infrastructure_Report_Smoke_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    vm_pdf = vm_generator.generate_vm_infrastructure_report(vm_data=vm_data, summary=summary, output_filename=vm_filename)
    if vm_pdf and Path(vm_pdf).exists():
        result["vm_pdf"] = str(vm_pdf)
    else:
        raise RuntimeError("VM PDF generation failed")
except Exception as exc:
    result["status"] = "fail"
    result["reason"] = f"vm report smoke failed: {exc}"
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(1)

try:
    from service_health_checker import get_service_health_data
    from generate_service_health_report import ServiceHealthReportGenerator
    service_data = get_service_health_data()
    service_generator = ServiceHealthReportGenerator(
        template_dir=str(template_dir),
        output_dir=str(output_dir),
        static_dir=str(static_dir),
    )
    svc_filename = f"Service_Health_Report_Smoke_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    service_pdf = service_generator.generate_service_health_report(
        service_health_data=service_data,
        output_filename=svc_filename,
    )
    if service_pdf and Path(service_pdf).exists():
        result["service_pdf"] = str(service_pdf)
    else:
        raise RuntimeError("Service PDF generation failed")
except Exception as exc:
    result["status"] = "fail"
    result["reason"] = f"service report smoke failed: {exc}"
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(1)

print(json.dumps(result, ensure_ascii=False))
