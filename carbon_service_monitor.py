#!/usr/bin/env python3
"""
Carbon Service Health Monitor - Production API Integration
Real-time monitoring for Carbon Receipt and Carbon Footprint services
"""

import asyncio
import aiohttp
import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ServiceStatus(Enum):
    """Service status enumeration"""
    OK = "ok"
    WARNING = "warning"
    ERROR = "error"
    UNKNOWN = "unknown"

@dataclass
class ServiceHealthData:
    """Service health data structure"""
    service_name: str
    status: ServiceStatus
    response_time_ms: float
    uptime: str
    database_status: str
    db_latency_ms: int
    last_updated: str
    sub_services: Dict[str, str]
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)
        result['status'] = self.status.value
        return result

@dataclass
class LogEntry:
    """Log entry structure for real API calls"""
    timestamp: str
    level: str
    service: str
    message: str
    response_time_ms: Optional[float] = None
    status_code: Optional[int] = None
    endpoint: str = ""
    details: Dict[str, Any] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)

class CarbonServiceMonitor:
    """Production Carbon Services Health Monitor"""
    
    def __init__(self):
        self.api_endpoints = {
            'carbon_receipt': 'https://uat-carbonreceipt.one.th/api/v1/health',
            'carbon_footprint': 'https://uat-carbonfootprint.one.th/api/v2/health'
        }
        
        # Cache for service data
        self.cache = {
            'carbon_receipt': None,
            'carbon_footprint': None,
            'last_updated': None,
            'historical_data': [],
            'logs': [],
            'metrics': {
                'total_requests': 0,
                'successful_requests': 0,
                'failed_requests': 0,
                'avg_response_time': 0.0
            }
        }
        
        # Keep last 100 log entries
        self.max_logs = 100
        
        # Session for HTTP requests
        self.session = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session with SSL disabled for UAT environment"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30)  # Increased timeout for slow UAT APIs
            # Disable SSL verification for UAT environment with self-signed certificates
            connector = aiohttp.TCPConnector(ssl=False)
            self.session = aiohttp.ClientSession(timeout=timeout, connector=connector)
        return self.session
    
    async def _fetch_service_health(self, service_name: str, url: str) -> ServiceHealthData:
        """Fetch health data from a single service"""
        start_time = time.time()
        
        try:
            session = await self._get_session()
            
            async with session.get(url) as response:
                response_time_ms = (time.time() - start_time) * 1000
                
                if response.status == 200:
                    data = await response.json()
                    
                    # Parse response based on service type
                    if service_name == 'carbon_receipt':
                        sub_services = data.get('service', {})
                        # Check etax_api_response for errors
                        service_response = data.get('service_response', {})
                        etax_response = service_response.get('etax_api_response', {})
                        if etax_response.get('status') == 'ER':
                            status = ServiceStatus.WARNING
                        else:
                            status = ServiceStatus.OK if data.get('status') == 'ok' else ServiceStatus.ERROR
                    else:
                        sub_services = data.get('service', {})
                        status = ServiceStatus.OK if data.get('status') == 'ok' else ServiceStatus.ERROR
                    
                    # Create log entry for successful request
                    log_entry = LogEntry(
                        timestamp=datetime.now().isoformat(),
                        level="SUCCESS",
                        service=service_name,
                        message=f"Health check successful - Status: {data.get('status')}",
                        response_time_ms=response_time_ms,
                        status_code=response.status,
                        endpoint=url,
                        details={
                            'uptime': data.get('uptime'),
                            'db_latency': data.get('db_latency_ms'),
                            'sub_services_count': len(sub_services)
                        }
                    )
                    self._add_log(log_entry)
                    
                    return ServiceHealthData(
                        service_name=service_name,
                        status=status,
                        response_time_ms=response_time_ms,
                        uptime=data.get('uptime', 'unknown'),
                        database_status=data.get('database', 'unknown'),
                        db_latency_ms=data.get('db_latency_ms', 0),
                        last_updated=datetime.now().isoformat(),
                        sub_services=sub_services
                    )
                else:
                    # HTTP error
                    error_msg = f"HTTP {response.status}: {await response.text()}"
                    self._add_error_log(service_name, url, response_time_ms, error_msg, response.status)
                    
                    return ServiceHealthData(
                        service_name=service_name,
                        status=ServiceStatus.ERROR,
                        response_time_ms=response_time_ms,
                        uptime="unknown",
                        database_status="error",
                        db_latency_ms=0,
                        last_updated=datetime.now().isoformat(),
                        sub_services={},
                        error_message=error_msg
                    )
                    
        except asyncio.TimeoutError:
            response_time_ms = (time.time() - start_time) * 1000
            error_msg = "Request timeout (10s)"
            self._add_error_log(service_name, url, response_time_ms, error_msg, None)
            
            return ServiceHealthData(
                service_name=service_name,
                status=ServiceStatus.ERROR,
                response_time_ms=response_time_ms,
                uptime="unknown",
                database_status="timeout",
                db_latency_ms=0,
                last_updated=datetime.now().isoformat(),
                sub_services={},
                error_message=error_msg
            )
            
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            error_msg = f"Connection error: {str(e)}"
            self._add_error_log(service_name, url, response_time_ms, error_msg, None)
            
            return ServiceHealthData(
                service_name=service_name,
                status=ServiceStatus.ERROR,
                response_time_ms=response_time_ms,
                uptime="unknown",
                database_status="error",
                db_latency_ms=0,
                last_updated=datetime.now().isoformat(),
                sub_services={},
                error_message=error_msg
            )
    
    def _add_log(self, log_entry: LogEntry):
        """Add log entry to cache"""
        self.cache['logs'].append(log_entry)
        
        # Keep only last N entries
        if len(self.cache['logs']) > self.max_logs:
            self.cache['logs'] = self.cache['logs'][-self.max_logs:]
        
        # Update metrics
        self.cache['metrics']['total_requests'] += 1
        self.cache['metrics']['successful_requests'] += 1
    
    def _add_error_log(self, service_name: str, url: str, response_time_ms: float, error_msg: str, status_code: Optional[int]):
        """Add error log entry"""
        log_entry = LogEntry(
            timestamp=datetime.now().isoformat(),
            level="ERROR",
            service=service_name,
            message=f"Health check failed: {error_msg}",
            response_time_ms=response_time_ms,
            status_code=status_code,
            endpoint=url,
            details={'error': error_msg}
        )
        self._add_log(log_entry)
        
        # Update metrics
        self.cache['metrics']['failed_requests'] += 1
    
    async def fetch_all_services(self) -> Dict[str, ServiceHealthData]:
        """Fetch health data from all services concurrently"""
        tasks = []
        
        for service_name, url in self.api_endpoints.items():
            task = self._fetch_service_health(service_name, url)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        service_data = {}
        total_response_time = 0
        successful_count = 0
        
        for i, result in enumerate(results):
            service_name = list(self.api_endpoints.keys())[i]
            
            if isinstance(result, Exception):
                logger.error(f"Error fetching {service_name}: {result}")
                # Create error service data
                service_data[service_name] = ServiceHealthData(
                    service_name=service_name,
                    status=ServiceStatus.ERROR,
                    response_time_ms=0.0,
                    uptime="unknown",
                    database_status="error",
                    db_latency_ms=0,
                    last_updated=datetime.now().isoformat(),
                    sub_services={},
                    error_message=str(result)
                )
            else:
                service_data[service_name] = result
                total_response_time += result.response_time_ms
                if result.status == ServiceStatus.OK:
                    successful_count += 1
        
        # Update cache
        self.cache['carbon_receipt'] = service_data.get('carbon_receipt')
        self.cache['carbon_footprint'] = service_data.get('carbon_footprint')
        self.cache['last_updated'] = datetime.now().isoformat()
        
        # Update average response time
        if len(service_data) > 0:
            self.cache['metrics']['avg_response_time'] = total_response_time / len(service_data)
        
        # Store historical data (last 24 hours)
        historical_entry = {
            'timestamp': datetime.now().isoformat(),
            'services': {name: data.to_dict() for name, data in service_data.items()}
        }
        self.cache['historical_data'].append(historical_entry)
        
        # Keep only last 24 hours (assuming check every 30 seconds = 2880 entries per day)
        max_historical = 2880
        if len(self.cache['historical_data']) > max_historical:
            self.cache['historical_data'] = self.cache['historical_data'][-max_historical:]
        
        return service_data
    
    def get_summary_metrics(self) -> Dict[str, Any]:
        """Get summary metrics for dashboard"""
        total_services = 0
        healthy_services = 0
        warning_services = 0
        error_services = 0
        
        # Count services from last fetch
        if self.cache['carbon_receipt']:
            receipt_status = self.cache['carbon_receipt'].status
            receipt_sub_services = len(self.cache['carbon_receipt'].sub_services)
            total_services += receipt_sub_services + 1  # +1 for main service
            
            if receipt_status == ServiceStatus.OK:
                healthy_services += receipt_sub_services + 1
            elif receipt_status == ServiceStatus.WARNING:
                warning_services += 1
                healthy_services += receipt_sub_services  # Assume sub-services are OK
            else:
                error_services += receipt_sub_services + 1
        
        if self.cache['carbon_footprint']:
            footprint_status = self.cache['carbon_footprint'].status
            footprint_sub_services = len(self.cache['carbon_footprint'].sub_services)
            total_services += footprint_sub_services + 1
            
            if footprint_status == ServiceStatus.OK:
                healthy_services += footprint_sub_services + 1
            elif footprint_status == ServiceStatus.WARNING:
                warning_services += 1
                healthy_services += footprint_sub_services
            else:
                error_services += footprint_sub_services + 1
        
        availability = (healthy_services / total_services * 100) if total_services > 0 else 0
        
        return {
            'total_services': total_services,
            'healthy_services': healthy_services,
            'warning_services': warning_services,
            'error_services': error_services,
            'availability_percentage': round(availability, 1),
            'total_requests': self.cache['metrics']['total_requests'],
            'successful_requests': self.cache['metrics']['successful_requests'],
            'failed_requests': self.cache['metrics']['failed_requests'],
            'success_rate': round((self.cache['metrics']['successful_requests'] / max(1, self.cache['metrics']['total_requests'])) * 100, 1),
            'avg_response_time': round(self.cache['metrics']['avg_response_time'], 1),
            'last_updated': self.cache['last_updated']
        }
    
    def get_logs(self, level_filter: str = None, service_filter: str = None, limit: int = 50) -> List[Dict]:
        """Get filtered logs"""
        logs = self.cache['logs']
        
        # Apply filters
        if level_filter:
            logs = [log for log in logs if log.level == level_filter]
        
        if service_filter:
            logs = [log for log in logs if log.service == service_filter]
        
        # Sort by timestamp (newest first) and limit
        logs = sorted(logs, key=lambda x: x.timestamp, reverse=True)[:limit]
        
        return [log.to_dict() for log in logs]
    
    async def close(self):
        """Close HTTP session"""
        if self.session and not self.session.closed:
            await self.session.close()

# Global monitor instance
carbon_monitor = CarbonServiceMonitor()

async def get_carbon_service_data():
    """Get current service data"""
    try:
        return await carbon_monitor.fetch_all_services()
    except Exception as e:
        logger.error(f"Error in get_carbon_service_data: {e}")
        # Return empty data structure on error
        return {}

def get_carbon_service_data_sync():
    """Sync wrapper for getting carbon service data"""
    try:
        import asyncio
        
        # Check if there's already an event loop running
        try:
            loop = asyncio.get_running_loop()
            # If we're already in an async context, this is problematic
            logger.warning("Already in async context, using thread executor")
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(lambda: asyncio.run(get_carbon_service_data()))
                return future.result(timeout=35)  # 35 second timeout
        except RuntimeError:
            # No running loop, safe to create new one
            return asyncio.run(get_carbon_service_data())
            
    except Exception as e:
        logger.error(f"Error in sync wrapper: {e}")
        return {}

def get_carbon_service_summary():
    """Get service summary metrics"""
    return carbon_monitor.get_summary_metrics()

def get_carbon_service_logs(level_filter=None, service_filter=None, limit=50):
    """Get filtered service logs"""
    return carbon_monitor.get_logs(level_filter, service_filter, limit)

async def cleanup_carbon_monitor():
    """Cleanup function for graceful shutdown"""
    await carbon_monitor.close()

if __name__ == "__main__":
    # Test the monitor
    async def test_monitor():
        try:
            print("🧪 Testing Carbon Service Monitor...")
            
            # Fetch data
            services = await get_carbon_service_data()
            
            print("\n📊 Service Health Results:")
            for name, data in services.items():
                print(f"  {name}: {data.status.value} ({data.response_time_ms:.1f}ms)")
                print(f"    Uptime: {data.uptime}")
                print(f"    Sub-services: {len(data.sub_services)}")
                for sub_name, sub_status in data.sub_services.items():
                    print(f"      - {sub_name}: {sub_status}")
                print()
            
            # Get summary
            summary = get_carbon_service_summary()
            print(f"📈 Summary:")
            print(f"  Total Services: {summary['total_services']}")
            print(f"  Healthy: {summary['healthy_services']}")
            print(f"  Warning: {summary['warning_services']}")
            print(f"  Error: {summary['error_services']}")
            print(f"  Availability: {summary['availability_percentage']}%")
            print(f"  Avg Response Time: {summary['avg_response_time']}ms")
            
            # Get recent logs
            logs = get_carbon_service_logs(limit=5)
            print(f"\n📋 Recent Logs ({len(logs)} entries):")
            for log in logs:
                print(f"  [{log['timestamp']}] {log['level']} - {log['service']}: {log['message']}")
            
        finally:
            await cleanup_carbon_monitor()
    
    # Run test
    asyncio.run(test_monitor())