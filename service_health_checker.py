#!/usr/bin/env python3
"""
Service Health Monitoring System
Integrates with VM Daily Report Dashboard
"""

import requests
import json
import time
import socket
import ssl
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from urllib.parse import urlparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ServiceHealthMonitor:
    """Monitor health of various services via API endpoints"""
    
    def __init__(self):
        self.cache = {
            "data": None,
            "timestamp": None,
            "ttl": 60  # Cache for 60 seconds
        }
        
        # Service endpoints configuration
        self.service_endpoints = {
            "carbon_footprint_uat": {
                "url": "https://uat-carbonfootprint.one.th/api/v2/health",
                "name": "Carbon Footprint (UAT)",
                "type": "api",
                "timeout": 5  # Reduced timeout
            },
            "carbon_footprint_prd": {
                "url": "https://prd-carbonfootprint.one.th/api/v2/health", 
                "name": "Carbon Footprint (PRD)",
                "type": "api",
                "timeout": 5
            },
            "etax_software": {
                "url": "http://10.0.0.223/api/health",
                "name": "E-Tax Software",
                "type": "api",
                "timeout": 3
            },
            "rancher_management": {
                "url": "http://192.168.1.101/api/health",
                "name": "Rancher Management",
                "type": "api", 
                "timeout": 3
            },
            "database_cluster": {
                "url": "http://192.168.10.21/api/health",
                "name": "Database Cluster",
                "type": "database",
                "timeout": 3
            }
        }
        
        # Demo mode flag - disabled by default to use real endpoint data
        self.demo_mode = False
        
        # Demo data for when services are not accessible
        self.demo_services = {
            "carbon_footprint_uat": {
                "name": "Carbon Footprint (UAT)",
                "type": "api",
                "status": "ok",
                "health_level": "healthy",
                "database": "Connect",
                "db_latency_ms": 0,
                "response_time_ms": 45.2,
                "uptime": "29m18s",
                "endpoints": {
                    "one_api_status": "ok",
                    "industrial_api_status": "ok",
                    "report_api_status": "ok"
                },
                "last_check": datetime.now().isoformat(),
                "url": "https://uat-carbonfootprint.one.th/api/v2/health",
                "error": None
            },
            "carbon_footprint_prd": {
                "name": "Carbon Footprint (PRD)",
                "type": "api",
                "status": "ok",
                "health_level": "healthy",
                "database": "Connect",
                "db_latency_ms": 2,
                "response_time_ms": 38.7,
                "uptime": "2d15h42m",
                "endpoints": {
                    "one_api_status": "ok",
                    "industrial_api_status": "ok",
                    "report_api_status": "ok"
                },
                "last_check": datetime.now().isoformat(),
                "url": "https://prd-carbonfootprint.one.th/api/v2/health",
                "error": None
            },
            "etax_software": {
                "name": "E-Tax Software",
                "type": "api",
                "status": "ok",
                "health_level": "healthy",
                "database": "Connect",
                "db_latency_ms": 1,
                "response_time_ms": 23.1,
                "uptime": "5d8h15m",
                "endpoints": {
                    "authentication_status": "ok",
                    "tax_processing_status": "ok",
                    "report_generation_status": "ok"
                },
                "last_check": datetime.now().isoformat(),
                "url": "http://10.0.0.223/api/health",
                "error": None
            },
            "rancher_management": {
                "name": "Rancher Management",
                "type": "api",
                "status": "ok",
                "health_level": "warning",  # Show some variation
                "database": "Connect",
                "db_latency_ms": 125,  # Higher latency for warning
                "response_time_ms": 156.3,
                "uptime": "12d3h27m",
                "endpoints": {
                    "cluster_api_status": "ok",
                    "kubernetes_api_status": "ok",
                    "management_ui_status": "ok"
                },
                "last_check": datetime.now().isoformat(),
                "url": "http://192.168.1.101/api/health",
                "error": None
            },
            "database_cluster": {
                "name": "Database Cluster",
                "type": "database",
                "status": "ok",
                "health_level": "healthy",
                "database": "Connect",
                "db_latency_ms": 3,
                "response_time_ms": 12.8,
                "uptime": "15d22h45m",
                "endpoints": {
                    "postgresql_primary_status": "ok",
                    "mongodb_replica_status": "ok",
                    "redis_cluster_status": "ok"
                },
                "last_check": datetime.now().isoformat(),
                "url": "http://192.168.10.21/api/health",
                "error": None
            }
        }
        
        # Health check thresholds
        self.thresholds = {
            "db_latency_warning": 100,  # ms
            "db_latency_critical": 500,  # ms
            "response_time_warning": 5000,  # ms
            "response_time_critical": 10000,  # ms
            "uptime_warning": 99.0  # percentage
        }
    
    def check_all_services(self) -> Dict[str, Any]:
        """Check health of all configured services"""
        # Check cache first
        if self._is_cache_valid():
            logger.info("Returning cached service health data")
            return self.cache["data"]
        
        logger.info("Checking health of all services...")
        
        # If demo mode is enabled, return demo data
        if self.demo_mode:
            logger.info("Demo mode enabled - using simulated service data")
            results = self.demo_services.copy()
            # Update timestamps
            for service_data in results.values():
                service_data["last_check"] = datetime.now().isoformat()
        else:
            # Real service checking
            results = {}
            for service_id, config in self.service_endpoints.items():
                logger.info(f"Checking {config['name']}...")
                results[service_id] = self._check_single_service(config)
        
        # Calculate summary
        summary = self._calculate_summary(results)
        
        # Update cache
        self.cache["data"] = {
            "services": results,
            "summary": summary,
            "last_check": datetime.now().isoformat(),
            "check_duration": time.time(),
            "demo_mode": self.demo_mode
        }
        self.cache["timestamp"] = datetime.now()
        
        logger.info(f"Service health check completed. {summary['healthy_count']}/{summary['total_count']} services healthy")
        return self.cache["data"]
    
    def _check_single_service(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Check health of a single service endpoint"""
        start_time = time.time()
        preflight = self._run_preflight_probe(config)

        if not preflight["reachable"]:
            response_time = (time.time() - start_time) * 1000
            return self._create_error_response(
                preflight["details"],
                response_time,
                config,
                health_level="unreachable",
                error_type=preflight["reason"],
                probe=preflight
            )
        
        try:
            response = requests.get(
                config["url"], 
                timeout=config["timeout"],
                headers={"User-Agent": "VM-Dashboard-Health-Checker/1.0"}
            )
            
            response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            if response.status_code == 200:
                health_data = response.json()
                return self._parse_health_response(health_data, response_time, config, probe=preflight)
            else:
                if response.status_code in [401, 403]:
                    health_level = "warning"
                    error_type = "auth_failed"
                elif response.status_code >= 500:
                    health_level = "critical"
                    error_type = "http_server_error"
                else:
                    health_level = "warning"
                    error_type = "http_error"
                return self._create_error_response(
                    f"HTTP {response.status_code}: {response.text[:100]}", 
                    response_time, 
                    config,
                    health_level=health_level,
                    error_type=error_type,
                    probe=preflight,
                    status_code=response.status_code
                )
                
        except requests.exceptions.Timeout:
            response_time = config["timeout"] * 1000
            return self._create_error_response(
                "Request timeout",
                response_time,
                config,
                health_level="unreachable",
                error_type="request_timeout",
                probe=preflight
            )
        
        except requests.exceptions.ConnectionError:
            response_time = (time.time() - start_time) * 1000
            return self._create_error_response(
                "Connection error",
                response_time,
                config,
                health_level="unreachable",
                error_type="connection_error",
                probe=preflight
            )
        
        except requests.exceptions.SSLError as e:
            response_time = (time.time() - start_time) * 1000
            return self._create_error_response(
                str(e),
                response_time,
                config,
                health_level="unreachable",
                error_type="ssl_error",
                probe=preflight
            )
        
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return self._create_error_response(
                str(e),
                response_time,
                config,
                health_level="warning",
                error_type="unknown_monitor_error",
                probe=preflight
            )
    
    def _parse_health_response(
        self,
        data: Dict[str, Any],
        response_time: float,
        config: Dict[str, Any],
        probe: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Parse service health response into standardized format"""
        
        # Extract basic health info
        status = data.get("status", "unknown").lower()
        database_status = data.get("database", "unknown")
        db_latency = data.get("db_latency_ms", 0)
        uptime = data.get("uptime", "unknown")
        
        # Extract service-specific endpoints
        services = data.get("service", {})
        if isinstance(services, dict):
            service_endpoints = {
                key: value for key, value in services.items()
                if key.endswith("_status") or key.endswith("_api_status")
            }
        else:
            service_endpoints = {}
        
        # Determine health level
        health_level = self._determine_health_level(status, db_latency, response_time)
        
        return {
            "name": config["name"],
            "type": config["type"],
            "status": status,
            "health_level": health_level,
            "database": database_status,
            "db_latency_ms": db_latency,
            "response_time_ms": round(response_time, 2),
            "uptime": uptime,
            "endpoints": service_endpoints,
            "last_check": datetime.now().isoformat(),
            "url": config["url"],
            "error": None,
            "error_type": None,
            "http_status": 200,
            "probe": probe or self._default_probe()
        }
    
    def _create_error_response(
        self,
        error_message: str,
        response_time: float,
        config: Dict[str, Any],
        health_level: str = "unreachable",
        error_type: str = "connection_error",
        probe: Optional[Dict[str, Any]] = None,
        status_code: Optional[int] = None
    ) -> Dict[str, Any]:
        """Create standardized error response"""
        return {
            "name": config["name"],
            "type": config["type"],
            "status": "error",
            "health_level": health_level,
            "database": "unknown",
            "db_latency_ms": 0,
            "response_time_ms": round(response_time, 2),
            "uptime": "unknown",
            "endpoints": {},
            "last_check": datetime.now().isoformat(),
            "url": config["url"],
            "error": error_message,
            "error_type": error_type,
            "http_status": status_code,
            "probe": probe or self._default_probe()
        }

    def _default_probe(self) -> Dict[str, Any]:
        return {
            "reachable": True,
            "dns_ok": None,
            "tcp_ok": None,
            "ssl_ok": None,
            "reason": None,
            "details": None
        }

    def _run_preflight_probe(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Check DNS/TCP/SSL reachability before API request."""
        parsed = urlparse(config["url"])
        hostname = parsed.hostname
        if not hostname:
            return {
                "reachable": False,
                "dns_ok": False,
                "tcp_ok": False,
                "ssl_ok": False,
                "reason": "invalid_url",
                "details": f"Invalid URL: {config['url']}"
            }

        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        timeout = config.get("timeout", 5)
        probe = {
            "reachable": False,
            "dns_ok": False,
            "tcp_ok": False,
            "ssl_ok": None,
            "reason": None,
            "details": None
        }

        try:
            socket.getaddrinfo(hostname, port)
            probe["dns_ok"] = True
        except socket.gaierror as e:
            probe["reason"] = "dns_failed"
            probe["details"] = f"DNS resolution failed: {e}"
            return probe

        tcp_socket = None
        try:
            tcp_socket = socket.create_connection((hostname, port), timeout=timeout)
            probe["tcp_ok"] = True

            if parsed.scheme == "https":
                context = ssl.create_default_context()
                with context.wrap_socket(tcp_socket, server_hostname=hostname):
                    probe["ssl_ok"] = True
                tcp_socket = None
        except ConnectionRefusedError as e:
            probe["reason"] = "connection_refused"
            probe["details"] = f"TCP connection refused: {e}"
            return probe
        except socket.timeout as e:
            probe["reason"] = "tcp_timeout"
            probe["details"] = f"TCP connection timeout: {e}"
            return probe
        except ssl.SSLError as e:
            probe["reason"] = "ssl_error"
            probe["details"] = f"SSL handshake failed: {e}"
            probe["ssl_ok"] = False
            return probe
        except OSError as e:
            probe["reason"] = "tcp_connect_error"
            probe["details"] = f"TCP connection failed: {e}"
            return probe
        finally:
            if tcp_socket:
                tcp_socket.close()

        probe["reachable"] = True
        return probe
    
    def _determine_health_level(self, status: str, db_latency: int, response_time: float) -> str:
        """Determine overall health level based on metrics"""
        if status != "ok":
            return "critical"
        
        if (db_latency > self.thresholds["db_latency_critical"] or 
            response_time > self.thresholds["response_time_critical"]):
            return "critical"
        
        if (db_latency > self.thresholds["db_latency_warning"] or 
            response_time > self.thresholds["response_time_warning"]):
            return "warning"
        
        return "healthy"
    
    def _calculate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate service health summary"""
        total_count = len(results)
        healthy_count = sum(1 for service in results.values() if service["health_level"] == "healthy")
        warning_count = sum(1 for service in results.values() if service["health_level"] == "warning")
        critical_count = sum(1 for service in results.values() if service["health_level"] == "critical")
        unreachable_count = sum(1 for service in results.values() if service["health_level"] == "unreachable")
        
        availability = (healthy_count / total_count * 100) if total_count > 0 else 0
        
        # Determine overall status
        if critical_count > 0:
            overall_status = "critical"
        elif warning_count > 0:
            overall_status = "warning"
        elif unreachable_count > 0:
            overall_status = "monitoring_issue"
        else:
            overall_status = "healthy"
        
        return {
            "total_count": total_count,
            "healthy_count": healthy_count,
            "warning_count": warning_count,
            "critical_count": critical_count,
            "unreachable_count": unreachable_count,
            "availability_percentage": round(availability, 1),
            "overall_status": overall_status,
            "last_update": datetime.now().isoformat()
        }
    
    def _is_cache_valid(self) -> bool:
        """Check if cached data is still valid"""
        if not self.cache["data"] or not self.cache["timestamp"]:
            return False
        
        age = (datetime.now() - self.cache["timestamp"]).total_seconds()
        return age < self.cache["ttl"]
    
    def get_service_alerts(self) -> list:
        """Get list of service-related alerts"""
        data = self.check_all_services()
        alerts = []
        
        for service_id, service_data in data["services"].items():
            if service_data["health_level"] == "critical":
                alerts.append({
                    "level": "critical",
                    "service": service_data["name"],
                    "message": service_data.get("error", "Service is in critical state"),
                    "timestamp": service_data["last_check"]
                })
            elif service_data["health_level"] == "warning":
                alerts.append({
                    "level": "warning", 
                    "service": service_data["name"],
                    "message": f"High latency: {service_data['db_latency_ms']}ms or slow response: {service_data['response_time_ms']}ms",
                    "timestamp": service_data["last_check"]
                })
            elif service_data["health_level"] == "unreachable":
                alerts.append({
                    "level": "warning",
                    "service": service_data["name"],
                    "message": service_data.get("error", "Monitoring endpoint unreachable"),
                    "timestamp": service_data["last_check"]
                })
        
        return alerts

# Convenience functions for integration
def get_service_health_data():
    """Get service health data - main integration function"""
    monitor = ServiceHealthMonitor()
    return monitor.check_all_services()

def get_service_alerts():
    """Get service alerts - alert integration function"""
    monitor = ServiceHealthMonitor()
    return monitor.get_service_alerts()

# Testing function
def test_service_health():
    """Test function to verify service health monitoring"""
    print("🧪 Testing Service Health Monitoring...")
    
    monitor = ServiceHealthMonitor()
    results = monitor.check_all_services()
    
    print(f"\n📊 Service Health Summary:")
    print(f"   Total Services: {results['summary']['total_count']}")
    print(f"   Healthy: {results['summary']['healthy_count']}")
    print(f"   Warning: {results['summary']['warning_count']}")
    print(f"   Critical: {results['summary']['critical_count']}")
    print(f"   Unreachable: {results['summary'].get('unreachable_count', 0)}")
    print(f"   Availability: {results['summary']['availability_percentage']}%")
    print(f"   Overall Status: {results['summary']['overall_status']}")
    
    print(f"\n🔍 Individual Services:")
    for service_id, service_data in results["services"].items():
        if service_data["health_level"] == "healthy":
            status_emoji = "✅"
        elif service_data["health_level"] == "warning":
            status_emoji = "⚠️"
        elif service_data["health_level"] == "critical":
            status_emoji = "❌"
        else:
            status_emoji = "📡"
        print(f"   {status_emoji} {service_data['name']}: {service_data['status']} ({service_data['response_time_ms']}ms)")
        if service_data["error"]:
            print(f"      Error: {service_data['error']}")
    
    # Test alerts
    alerts = monitor.get_service_alerts()
    if alerts:
        print(f"\n🚨 Active Alerts:")
        for alert in alerts:
            print(f"   {alert['level'].upper()}: {alert['service']} - {alert['message']}")
    else:
        print(f"\n✅ No active service alerts")

if __name__ == "__main__":
    test_service_health()
