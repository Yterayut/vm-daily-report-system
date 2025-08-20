#!/usr/bin/env python3
"""
Service Health Monitoring System
Integrates with VM Daily Report Dashboard
"""

import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
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
        
        # Demo mode flag - set to True when real endpoints are not accessible
        self.demo_mode = True
        
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
        
        try:
            response = requests.get(
                config["url"], 
                timeout=config["timeout"],
                headers={"User-Agent": "VM-Dashboard-Health-Checker/1.0"}
            )
            
            response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            if response.status_code == 200:
                health_data = response.json()
                return self._parse_health_response(health_data, response_time, config)
            else:
                return self._create_error_response(
                    f"HTTP {response.status_code}: {response.text[:100]}", 
                    response_time, 
                    config
                )
                
        except requests.exceptions.Timeout:
            response_time = config["timeout"] * 1000
            return self._create_error_response("Request timeout", response_time, config)
        
        except requests.exceptions.ConnectionError:
            response_time = (time.time() - start_time) * 1000
            return self._create_error_response("Connection error", response_time, config)
        
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return self._create_error_response(str(e), response_time, config)
    
    def _parse_health_response(self, data: Dict[str, Any], response_time: float, config: Dict[str, Any]) -> Dict[str, Any]:
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
            "error": None
        }
    
    def _create_error_response(self, error_message: str, response_time: float, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create standardized error response"""
        return {
            "name": config["name"],
            "type": config["type"],
            "status": "error",
            "health_level": "critical",
            "database": "unknown",
            "db_latency_ms": 0,
            "response_time_ms": round(response_time, 2),
            "uptime": "unknown",
            "endpoints": {},
            "last_check": datetime.now().isoformat(),
            "url": config["url"],
            "error": error_message
        }
    
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
        
        availability = (healthy_count / total_count * 100) if total_count > 0 else 0
        
        # Determine overall status
        if critical_count > 0:
            overall_status = "critical"
        elif warning_count > 0:
            overall_status = "warning"
        else:
            overall_status = "healthy"
        
        return {
            "total_count": total_count,
            "healthy_count": healthy_count,
            "warning_count": warning_count,
            "critical_count": critical_count,
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
    print(f"   Availability: {results['summary']['availability_percentage']}%")
    print(f"   Overall Status: {results['summary']['overall_status']}")
    
    print(f"\n🔍 Individual Services:")
    for service_id, service_data in results["services"].items():
        status_emoji = "✅" if service_data["health_level"] == "healthy" else "⚠️" if service_data["health_level"] == "warning" else "❌"
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
