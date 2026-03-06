#!/usr/bin/env python3
"""
Service health adapter layer (single source of truth).
Transforms carbon_service_monitor payload to structures used by:
- reports
- mobile API
- alert formatting
"""

from datetime import datetime
from typing import Dict, Any, List

from carbon_service_monitor import (
    get_carbon_service_data_sync,
    get_carbon_service_summary,
    get_carbon_service_logs,
)


def _normalize_status(raw: str) -> str:
    value = (raw or "").strip().lower()
    if value in {"ok", "healthy", "up"}:
        return "ok"
    if value in {"warning", "degraded"}:
        return "warning"
    if value in {"error", "critical", "down", "timeout"}:
        return "error"
    # Parse values such as "status code 401"
    if "status code" in value or value.isdigit():
        return "warning"
    return "unknown"


def _service_to_dict(service_obj: Any) -> Dict[str, Any]:
    """Normalize carbon_service_monitor object/dict to dict."""
    if isinstance(service_obj, dict):
        return service_obj
    if hasattr(service_obj, "to_dict"):
        return service_obj.to_dict()
    return {
        "status": getattr(service_obj, "status", "unknown"),
        "response_time_ms": getattr(service_obj, "response_time_ms", 0),
        "database_status": getattr(service_obj, "database_status", "unknown"),
        "db_latency_ms": getattr(service_obj, "db_latency_ms", 0),
        "uptime": getattr(service_obj, "uptime", "unknown"),
        "sub_services": getattr(service_obj, "sub_services", {}) or {},
    }


def _service_groups_from_core() -> Dict[str, Any]:
    services = get_carbon_service_data_sync() or {}
    summary = get_carbon_service_summary() or {}
    logs = get_carbon_service_logs(limit=50) or []

    groups = {}
    for key, svc_raw in services.items():
        svc = _service_to_dict(svc_raw)
        env = "prd" if "prd" in key else "uat"
        svc_type = "Carbon Footprint" if "footprint" in key else "Carbon Receipt"
        title = f"{svc_type} - INFRA {env.upper()}"
        icon = "🌍" if "footprint" in key else "🌱"

        sub_services = []
        for sub_name, sub_status in (svc.get("sub_services") or {}).items():
            display_name = "E-Tax Software" if "etax" in sub_name.lower() else sub_name
            status_text = str(sub_status).replace(",", "").strip()
            sub_services.append(
                {
                    "name": display_name,
                    "status": status_text,
                    "key": sub_name.lower().replace(" ", "_"),
                }
            )

        groups[key] = {
            "title": title,
            "icon": icon,
            "main_service": {
                "name": svc_type,
                "status": _normalize_status(svc.get("status", "unknown")),
                "response_time": float(svc.get("response_time_ms", 0) or 0),
                "database": svc.get("database_status", "unknown"),
                "db_latency_ms": int(svc.get("db_latency_ms", 0) or 0),
                "uptime": svc.get("uptime", "unknown"),
            },
            "sub_services": sub_services,
        }

    payload = {
        "groups": groups,
        "summary": {
            "total_services": int(summary.get("total_services", 0) or 0),
            "healthy_services": int(summary.get("healthy_services", 0) or 0),
            "warning_services": int(summary.get("warning_services", 0) or 0),
            "error_services": int(summary.get("error_services", 0) or 0),
            "availability_percentage": float(summary.get("availability_percentage", 0.0) or 0.0),
            "overall_status": (
                "healthy"
                if float(summary.get("availability_percentage", 0.0) or 0.0) >= 95
                else "warning"
                if float(summary.get("availability_percentage", 0.0) or 0.0) >= 80
                else "critical"
            ),
        },
        "logs": logs,
        "last_updated": summary.get("last_updated") or datetime.now().isoformat(),
    }
    return payload


def get_mobile_services_health_payload() -> Dict[str, Any]:
    """Payload used by /api/services/* endpoints."""
    return _service_groups_from_core()


def get_service_health_data() -> Dict[str, Any]:
    """Payload used by reports/summary views."""
    api_data = _service_groups_from_core()
    services: Dict[str, Any] = {}

    total_response = 0.0
    total_db_latency = 0.0
    count = 0
    healthy = 0
    warning = 0
    critical = 0

    for group_key, group_data in api_data.get("groups", {}).items():
        main = group_data.get("main_service") or {}
        status = _normalize_status(main.get("status", "unknown"))
        if status == "ok":
            healthy += 1
        elif status == "warning":
            warning += 1
        else:
            critical += 1

        total_response += float(main.get("response_time", 0) or 0)
        total_db_latency += float(main.get("db_latency_ms", 0) or 0)
        count += 1

        services[group_key] = {
            "name": group_data.get("title", group_key),
            "status": status,
            "database": main.get("database", "unknown"),
            "db_latency_ms": float(main.get("db_latency_ms", 0) or 0),
            "response_time": float(main.get("response_time", 0) or 0),
            "uptime": main.get("uptime", "unknown"),
            "icon": group_data.get("icon", "🔧"),
            "sub_services": group_data.get("sub_services", []),
        }

    total = count
    availability = round((healthy / total) * 100, 1) if total else 0.0
    return {
        "services": services,
        "summary": {
            "total": total,
            "healthy": healthy,
            "warning": warning,
            "critical": critical,
            "availability": availability,
            "overall_status": "healthy" if critical == 0 and warning == 0 else "warning" if critical == 0 else "critical",
            # compatibility keys
            "total_count": total,
            "healthy_count": healthy,
            "warning_count": warning,
            "critical_count": critical,
            "availability_percentage": availability,
        },
        "performance": {
            "avg_response_time": (total_response / total) if total else 0.0,
            "avg_db_latency": (total_db_latency / total) if total else 0.0,
        },
        "demo_mode": False,
        "last_check": api_data.get("last_updated"),
        "last_updated": api_data.get("last_updated"),
    }


def get_service_alerts() -> List[Dict[str, Any]]:
    alerts: List[Dict[str, Any]] = []
    data = get_service_health_data()
    for service in data.get("services", {}).values():
        status = _normalize_status(service.get("status", "unknown"))
        if status == "error":
            alerts.append(
                {
                    "severity": "CRITICAL",
                    "service_name": service.get("name", "unknown"),
                    "message": "Service status is critical/error",
                }
            )
        elif status == "warning":
            alerts.append(
                {
                    "severity": "WARNING",
                    "service_name": service.get("name", "unknown"),
                    "message": "Service status is degraded/warning",
                }
            )
    return alerts
