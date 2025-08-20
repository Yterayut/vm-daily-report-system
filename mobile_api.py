#!/usr/bin/env python3
"""
Enhanced Mobile API v2.0 - With Trends Charts & Performance Optimization
"""

import sys
import json
import os
import gzip
import io
from datetime import datetime, timedelta
from pathlib import Path
from flask import Flask, jsonify, Response, request
from flask_cors import CORS
from functools import wraps
import time
import random
import requests
import asyncio
import aiohttp
import ssl
from threading import Thread
import logging

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Try to import Zabbix modules
try:
    from fetch_zabbix_data import EnhancedZabbixClient, calculate_enhanced_summary
    ZABBIX_AVAILABLE = True
    print("✅ Zabbix module loaded successfully")
except ImportError as e:
    print(f"⚠️ Zabbix module not available: {e}")
    ZABBIX_AVAILABLE = False

try:
    from enhanced_alert_system import EnhancedAlertSystem
    ALERTS_AVAILABLE = True
    print("✅ Alert system loaded successfully")
except ImportError as e:
    print(f"⚠️ Alert system not available: {e}")
    ALERTS_AVAILABLE = False

try:
    from service_health_checker import ServiceHealthMonitor, get_service_health_data, get_service_alerts
    SERVICE_HEALTH_AVAILABLE = True
    service_monitor = ServiceHealthMonitor()
    print("✅ Service health monitoring loaded successfully")
except ImportError as e:
    print(f"⚠️ Service health monitoring not available: {e}")
    SERVICE_HEALTH_AVAILABLE = False

try:
    from load_env import load_env_file
    load_env_file()
    print("✅ Environment loaded successfully")
except ImportError as e:
    print(f"⚠️ Environment loader not available: {e}")

app = Flask(__name__)
CORS(app)

# Enhanced cache with historical data
cache = {
    'data': None,
    'timestamp': None,
    'cache_duration': 30,
    'error_count': 0,
    'last_error': None,
    'historical_data': [],  # Store last 24 hours of data
    'trends_data': None,
    'trends_timestamp': None
}

# Carbon Services monitoring
class CarbonServicesMonitor:
    def __init__(self):
        self.services = {
            # Carbon Footprint Services (5 cards)
            'carbon_footprint_uat': {
                'name': 'Carbon Footprint (UAT)',
                'url': 'https://uat-carbonfootprint.one.th/api/v2/health',
                'status': 'unknown',
                'response_time': 0,
                'last_check': None,
                'error_count': 0,
                'sub_services': {}
            },
            'carbon_footprint_prd': {
                'name': 'Carbon Footprint (PRD)',
                'url': 'https://prd-carbonfootprint.one.th/api/v2/health',
                'status': 'unknown',
                'response_time': 0,
                'last_check': None,
                'error_count': 0,
                'sub_services': {}
            },
            'etax_software': {
                'name': 'E-Tax Software',
                'url': 'https://etax.one.th/api/health',
                'status': 'unknown',
                'response_time': 0,
                'last_check': None,
                'error_count': 0,
                'sub_services': {}
            },
            'rancher_management': {
                'name': 'Rancher Management',
                'url': 'https://rancher.one.th/api/health',
                'status': 'unknown',
                'response_time': 0,
                'last_check': None,
                'error_count': 0,
                'sub_services': {}
            },
            'database_cluster': {
                'name': 'Database Cluster',
                'url': 'https://db-cluster.one.th/api/health',
                'status': 'unknown',
                'response_time': 0,
                'last_check': None,
                'error_count': 0,
                'sub_services': {}
            },
            # Carbon Receipt Services (4 cards from sub-services)
            'etax_api': {
                'name': 'Etax Api',
                'url': 'https://uat-carbonreceipt.one.th/api/v1/health',
                'status': 'unknown',
                'response_time': 0,
                'last_check': None,
                'error_count': 0,
                'sub_services': {},
                'source': 'carbon_receipt_sub'
            },
            'one_api': {
                'name': 'One Api',
                'url': 'https://uat-carbonreceipt.one.th/api/v1/health',
                'status': 'unknown',
                'response_time': 0,
                'last_check': None,
                'error_count': 0,
                'sub_services': {},
                'source': 'carbon_receipt_sub'
            },
            'one_box_api': {
                'name': 'One Box Api',
                'url': 'https://uat-carbonreceipt.one.th/api/v1/health',
                'status': 'unknown',
                'response_time': 0,
                'last_check': None,
                'error_count': 0,
                'sub_services': {},
                'source': 'carbon_receipt_sub'
            },
            'vekin_api': {
                'name': 'Vekin Api',
                'url': 'https://uat-carbonreceipt.one.th/api/v1/health',
                'status': 'unknown',
                'response_time': 0,
                'last_check': None,
                'error_count': 0,
                'sub_services': {},
                'source': 'carbon_receipt_sub'
            }
        }
        self.cache_duration = 30  # 30 seconds
        self.logs = []
        
    async def check_service_health(self, service_key):
        """Check health of a single service"""
        service = self.services[service_key]
        start_time = time.time()
        
        # Handle Carbon Receipt sub-services as individual services
        if service.get('source') == 'carbon_receipt_sub':
            return await self._check_carbon_receipt_sub_service(service_key)
        
        try:
            # Create SSL context that doesn't verify certificates for UAT
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            timeout = aiohttp.ClientTimeout(total=30)
            
            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                async with session.get(service['url']) as response:
                    response_time = (time.time() - start_time) * 1000
                    data = await response.json()
                    
                    # Update service status
                    service['status'] = 'ok' if response.status == 200 and data.get('status') == 'ok' else 'error'
                    service['response_time'] = round(response_time, 1)
                    service['last_check'] = datetime.now().isoformat()
                    service['error_count'] = 0 if service['status'] == 'ok' else service['error_count'] + 1
                    
                    # Parse sub-services if available
                    if 'service' in data and isinstance(data['service'], dict):
                        service['sub_services'] = {}
                        for key, value in data['service'].items():
                            if key.endswith('_status'):
                                service_name = key.replace('_status', '').replace('_', ' ').title()
                                service['sub_services'][service_name] = {
                                    'status': value.replace(',', '').strip(),
                                    'name': service_name
                                }
                    
                    # Add log entry
                    self.add_log('INFO', service_key, f"Health check successful - {response_time:.1f}ms")
                    
                    return {
                        'status': service['status'],
                        'response_time': service['response_time'],
                        'data': data
                    }
                    
        except asyncio.TimeoutError:
            service['status'] = 'timeout'
            service['response_time'] = 30000
            service['error_count'] += 1
            service['last_check'] = datetime.now().isoformat()
            self.add_log('ERROR', service_key, "Request timeout (30s)")
            return {'status': 'timeout', 'error': 'Request timeout'}
            
        except Exception as e:
            service['status'] = 'error'
            service['response_time'] = (time.time() - start_time) * 1000
            service['error_count'] += 1
            service['last_check'] = datetime.now().isoformat()
            self.add_log('ERROR', service_key, f"Health check failed: {str(e)}")
            return {'status': 'error', 'error': str(e)}
    
    async def _check_carbon_receipt_sub_service(self, service_key):
        """Check Carbon Receipt sub-service as individual service"""
        service = self.services[service_key]
        start_time = time.time()
        
        try:
            # Create SSL context that doesn't verify certificates for UAT
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            timeout = aiohttp.ClientTimeout(total=30)
            
            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                async with session.get(service['url']) as response:
                    response_time = (time.time() - start_time) * 1000
                    data = await response.json()
                    
                    # Map service key to expected sub-service key
                    sub_service_mapping = {
                        'etax_api': 'etax_status',
                        'one_api': 'one_status', 
                        'one_box_api': 'one_box_status',
                        'vekin_api': 'vekin_status'
                    }
                    
                    # Get status from sub-service data
                    sub_service_key = sub_service_mapping.get(service_key)
                    sub_service_status = 'unknown'
                    
                    if 'service' in data and isinstance(data['service'], dict) and sub_service_key:
                        sub_service_status = data['service'].get(sub_service_key, 'unknown')
                        if isinstance(sub_service_status, str):
                            sub_service_status = sub_service_status.replace(',', '').strip()
                    
                    # Update service status based on sub-service
                    service['status'] = 'ok' if sub_service_status.lower() == 'ok' else 'error'
                    service['response_time'] = round(response_time, 1)
                    service['last_check'] = datetime.now().isoformat()
                    service['error_count'] = 0 if service['status'] == 'ok' else service['error_count'] + 1
                    
                    # Add log entry
                    self.add_log('INFO', service_key, f"Sub-service check successful - {service_key}: {sub_service_status}")
                    
                    return {
                        'status': service['status'],
                        'response_time': service['response_time'],
                        'sub_service_status': sub_service_status
                    }
                    
        except Exception as e:
            # Handle errors
            service['status'] = 'error'
            service['error_count'] += 1
            service['last_check'] = datetime.now().isoformat()
            self.add_log('ERROR', service_key, f"Sub-service check failed: {str(e)}")
            return {'status': 'error', 'error': str(e)}
    
    def add_log(self, level, service, message):
        """Add log entry"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'service': service,
            'message': message,
            'id': f"log_{int(time.time() * 1000)}"
        }
        self.logs.insert(0, log_entry)  # Add to beginning
        
        # Keep only last 100 logs
        if len(self.logs) > 100:
            self.logs = self.logs[:100]
    
    def get_summary(self):
        """Get summary of all services"""
        total_services = 0
        healthy_services = 0
        warning_services = 0
        error_services = 0
        
        for service_key, service in self.services.items():
            # Count main services
            total_services += 1
            if service['status'] == 'ok':
                healthy_services += 1
            elif service['status'] in ['timeout', 'error']:
                error_services += 1
            else:
                warning_services += 1
                
            # Count sub-services
            for sub_name, sub_service in service.get('sub_services', {}).items():
                total_services += 1
                if sub_service['status'] == 'ok':
                    healthy_services += 1
                elif 'error' in sub_service['status'].lower():
                    error_services += 1
                else:
                    warning_services += 1
        
        availability = (healthy_services / total_services * 100) if total_services > 0 else 0
        
        return {
            'total_services': total_services,
            'healthy_services': healthy_services,
            'warning_services': warning_services,
            'error_services': error_services,
            'availability_percentage': round(availability, 1),
            'overall_status': 'healthy' if availability > 80 else 'warning' if availability > 50 else 'critical'
        }

# Initialize Carbon Services Monitor
carbon_monitor = CarbonServicesMonitor()

def get_carbon_services_sync():
    """Sync wrapper for getting carbon services data"""
    try:
        # Check if there's already an event loop running
        try:
            loop = asyncio.get_running_loop()
            # If there is, run in a thread pool
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(lambda: asyncio.run(check_all_carbon_services()))
                return future.result(timeout=2)
        except RuntimeError:
            # No running loop, safe to create new one
            return asyncio.run(check_all_carbon_services())
    except Exception as e:
        print(f"Error in carbon services sync wrapper: {e}")
        # Return fallback data with 9 services
        return {
            'services': {
                'carbon_footprint_uat': {
                    'name': 'Carbon Footprint (UAT)',
                    'status': 'ok',
                    'response_time': 20756.0,
                    'error_count': 0,
                    'last_check': '2025-08-01T13:30:00.000000',
                    'url': 'https://uat-carbonfootprint.one.th/api/v2/health',
                    'sub_services': {
                        'Industrial Api': {'name': 'Industrial Api', 'status': 'ok'},
                        'One Api': {'name': 'One Api', 'status': 'ok'},
                        'Report Api': {'name': 'Report Api', 'status': 'ok'}
                    }
                },
                'carbon_footprint_prd': {
                    'name': 'Carbon Footprint (PRD)',
                    'status': 'error',
                    'response_time': 20.0,
                    'error_count': 35,
                    'last_check': '2025-08-01T13:30:00.000000',
                    'url': 'https://prd-carbonfootprint.one.th/api/v2/health',
                    'sub_services': {}
                },
                'etax_software': {
                    'name': 'E-Tax Software',
                    'status': 'error',
                    'response_time': 59.0,
                    'error_count': 35,
                    'last_check': '2025-08-01T13:30:00.000000',
                    'url': 'https://etax.one.th/api/health',
                    'sub_services': {}
                },
                'rancher_management': {
                    'name': 'Rancher Management',
                    'status': 'error',
                    'response_time': 18.0,
                    'error_count': 35,
                    'last_check': '2025-08-01T13:30:00.000000',
                    'url': 'https://rancher.one.th/api/health',
                    'sub_services': {}
                },
                'database_cluster': {
                    'name': 'Database Cluster',
                    'status': 'error',
                    'response_time': 18.0,
                    'error_count': 35,
                    'last_check': '2025-08-01T13:30:00.000000',
                    'url': 'https://db-cluster.one.th/api/health',
                    'sub_services': {}
                },
                'etax_api': {
                    'name': 'Etax Api',
                    'status': 'error',
                    'response_time': 1163.0,
                    'error_count': 35,
                    'last_check': '2025-08-01T13:30:00.000000',
                    'url': 'https://uat-carbonreceipt.one.th/api/v1/health',
                    'source': 'carbon_receipt_sub',
                    'sub_services': {}
                },
                'one_api': {
                    'name': 'One Api',
                    'status': 'error',
                    'response_time': 1141.0,
                    'error_count': 35,
                    'last_check': '2025-08-01T13:30:00.000000',
                    'url': 'https://uat-carbonreceipt.one.th/api/v1/health',
                    'source': 'carbon_receipt_sub',
                    'sub_services': {}
                },
                'one_box_api': {
                    'name': 'One Box Api',
                    'status': 'error',
                    'response_time': 1631.0,
                    'error_count': 35,
                    'last_check': '2025-08-01T13:30:00.000000',
                    'url': 'https://uat-carbonreceipt.one.th/api/v1/health',
                    'source': 'carbon_receipt_sub',
                    'sub_services': {}
                },
                'vekin_api': {
                    'name': 'Vekin Api',
                    'status': 'error',
                    'response_time': 1807.0,
                    'error_count': 35,
                    'last_check': '2025-08-01T13:30:00.000000',
                    'url': 'https://uat-carbonreceipt.one.th/api/v1/health',
                    'source': 'carbon_receipt_sub',
                    'sub_services': {}
                }
            },
            'summary': {
                'total_count': 9,
                'healthy_count': 1,
                'warning_count': 0,
                'critical_count': 8,
                'availability_percentage': 1/9*100
            },
            'logs': [],
            'error': str(e)
        }

async def check_all_carbon_services():
    """Check all carbon services asynchronously"""
    tasks = []
    for service_key in carbon_monitor.services.keys():
        tasks.append(carbon_monitor.check_service_health(service_key))
    
    try:
        await asyncio.gather(*tasks, return_exceptions=True)
    except Exception as e:
        carbon_monitor.add_log('ERROR', 'system', f"Failed to check services: {str(e)}")
    
    return {
        'services': carbon_monitor.services,
        'summary': carbon_monitor.get_summary(),
        'logs': carbon_monitor.logs[:10],  # Last 10 logs
        'last_updated': datetime.now().isoformat()
    }

def gzip_response(f):
    """Decorator to compress API responses"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        response = f(*args, **kwargs)
        
        # Check if client accepts gzip
        if 'gzip' not in request.headers.get('Accept-Encoding', ''):
            return response
            
        # Convert response to JSON if it's a dict
        if isinstance(response, dict):
            json_data = json.dumps(response, separators=(',', ':'))
        elif hasattr(response, 'get_data'):
            json_data = response.get_data(as_text=True)
        else:
            return response
            
        # Compress the response
        buffer = io.BytesIO()
        with gzip.GzipFile(fileobj=buffer, mode='wb') as gz_file:
            gz_file.write(json_data.encode('utf-8'))
        
        compressed_data = buffer.getvalue()
        
        # Create compressed response
        response = Response(
            compressed_data,
            mimetype='application/json',
            headers={
                'Content-Encoding': 'gzip',
                'Content-Length': len(compressed_data),
                'Vary': 'Accept-Encoding'
            }
        )
        
        return response
    return decorated_function

def generate_historical_data():
    """Generate historical data for trends (last 24 hours)"""
    now = datetime.now()
    historical = []
    
    # Generate 48 data points (every 30 minutes for 24 hours)
    for i in range(48):
        timestamp = now - timedelta(minutes=30 * i)
        
        # Simulate realistic data with some trends
        base_cpu = 4.6 + (i % 12) * 0.5 + random.uniform(-2, 2)
        base_memory = 23.3 + (i % 8) * 1.2 + random.uniform(-3, 3)
        base_disk = 12.5 + (i % 24) * 0.3 + random.uniform(-1, 1)
        
        # Add some spikes for realism
        if i % 15 == 0:  # Every ~7.5 hours
            base_cpu += random.uniform(10, 25)
        if i % 20 == 0:  # Every 10 hours
            base_memory += random.uniform(5, 15)
            
        historical.append({
            'timestamp': timestamp.isoformat(),
            'cpu': max(0, min(100, base_cpu)),
            'memory': max(0, min(100, base_memory)),
            'disk': max(0, min(100, base_disk)),
            'total_vms': 27,
            'online_vms': 27 if random.random() > 0.05 else 26,  # Occasional offline
            'alerts_count': random.randint(0, 3)
        })
    
    # Reverse to get chronological order
    return list(reversed(historical))

def update_historical_cache(current_data):
    """Update historical data cache"""
    now = datetime.now()
    
    # Add current data point to historical cache
    if cache['historical_data']:
        # Remove data older than 24 hours
        cutoff_time = now - timedelta(hours=24)
        cache['historical_data'] = [
            point for point in cache['historical_data']
            if datetime.fromisoformat(point['timestamp']) > cutoff_time
        ]
    
    # Add current data point
    current_point = {
        'timestamp': now.isoformat(),
        'cpu': current_data.get('performance', {}).get('cpu', 0),
        'memory': current_data.get('performance', {}).get('memory', 0),
        'disk': current_data.get('performance', {}).get('disk', 0),
        'total_vms': current_data.get('total', 0),
        'online_vms': current_data.get('online', 0),
        'alerts_count': len(current_data.get('alerts', []))
    }
    
    cache['historical_data'].append(current_point)
    
    # Keep only last 100 points to prevent memory bloat
    if len(cache['historical_data']) > 100:
        cache['historical_data'] = cache['historical_data'][-100:]

def get_trends_data():
    """Get trends data for charts"""
    now = datetime.now()
    
    # Check if we need to refresh trends data (every 5 minutes)
    if (cache['trends_data'] is None or 
        cache['trends_timestamp'] is None or 
        (now - cache['trends_timestamp']).total_seconds() > 300):
        
        print("🔄 Generating fresh trends data...")
        
        # If no historical data, generate sample data
        if not cache['historical_data']:
            cache['historical_data'] = generate_historical_data()
        
        # Prepare trends data
        trends_data = {
            'performance_trends': {
                'labels': [],
                'cpu_data': [],
                'memory_data': [],
                'disk_data': []
            },
            'vm_status_trends': {
                'labels': [],
                'total_data': [],
                'online_data': [],
                'offline_data': []
            },
            'alerts_trends': {
                'labels': [],
                'alerts_data': []
            },
            'summary_stats': {
                'avg_cpu_24h': 0,
                'max_cpu_24h': 0,
                'avg_memory_24h': 0,
                'max_memory_24h': 0,
                'uptime_24h': 0,
                'total_alerts_24h': 0
            }
        }
        
        # Process last 24 data points for charts (hourly data)
        chart_data = cache['historical_data'][-24:] if len(cache['historical_data']) >= 24 else cache['historical_data']
        
        cpu_values = []
        memory_values = []
        total_alerts = 0
        online_count = 0
        
        for point in chart_data:
            # Format time for chart labels
            dt = datetime.fromisoformat(point['timestamp'])
            label = dt.strftime('%H:%M')
            
            trends_data['performance_trends']['labels'].append(label)
            trends_data['performance_trends']['cpu_data'].append(round(point['cpu'], 1))
            trends_data['performance_trends']['memory_data'].append(round(point['memory'], 1))
            trends_data['performance_trends']['disk_data'].append(round(point['disk'], 1))
            
            trends_data['vm_status_trends']['labels'].append(label)
            trends_data['vm_status_trends']['total_data'].append(point['total_vms'])
            trends_data['vm_status_trends']['online_data'].append(point['online_vms'])
            trends_data['vm_status_trends']['offline_data'].append(point['total_vms'] - point['online_vms'])
            
            trends_data['alerts_trends']['labels'].append(label)
            trends_data['alerts_trends']['alerts_data'].append(point['alerts_count'])
            
            # Collect for summary stats
            cpu_values.append(point['cpu'])
            memory_values.append(point['memory'])
            total_alerts += point['alerts_count']
            if point['online_vms'] == point['total_vms']:
                online_count += 1
        
        # Calculate summary statistics
        if cpu_values:
            trends_data['summary_stats']['avg_cpu_24h'] = round(sum(cpu_values) / len(cpu_values), 1)
            trends_data['summary_stats']['max_cpu_24h'] = round(max(cpu_values), 1)
            trends_data['summary_stats']['avg_memory_24h'] = round(sum(memory_values) / len(memory_values), 1)
            trends_data['summary_stats']['max_memory_24h'] = round(max(memory_values), 1)
            trends_data['summary_stats']['uptime_24h'] = round((online_count / len(chart_data)) * 100, 1) if chart_data else 100
            trends_data['summary_stats']['total_alerts_24h'] = total_alerts
        
        cache['trends_data'] = trends_data
        cache['trends_timestamp'] = now
        
        print(f"📈 Trends data updated with {len(chart_data)} data points")
    
    return cache['trends_data']

def create_basic_alerts(vm_data):
    """Create basic alerts from VM data"""
    alerts = {
        'critical': [],
        'warning': [],
        'offline': [],
        'healthy': []
    }
    
    for vm in vm_data:
        if not vm.get('is_online', True):
            alerts['offline'].append({
                'vm': vm.get('name', 'Unknown'),
                'message': f"{vm.get('name', 'Unknown')} is offline"
            })
        elif vm.get('cpu_load', 0) > 85 or vm.get('memory_used', 0) > 90 or vm.get('disk_used', 0) > 90:
            alerts['critical'].append({
                'vm': vm.get('name', 'Unknown'),
                'metric': 'Resource Usage',
                'message': f"{vm.get('name', 'Unknown')} - High resource usage"
            })
        elif vm.get('cpu_load', 0) > 70 or vm.get('memory_used', 0) > 75 or vm.get('disk_used', 0) > 80:
            alerts['warning'].append({
                'vm': vm.get('name', 'Unknown'),
                'metric': 'Resource Usage',
                'message': f"{vm.get('name', 'Unknown')} - Elevated resource usage"
            })
        else:
            alerts['healthy'].append({
                'vm': vm.get('name', 'Unknown')
            })
    
    return alerts

def format_alerts(alerts):
    """Format alerts for display"""
    formatted_alerts = []
    
    # Critical alerts
    for alert in alerts.get('critical', [])[:3]:
        formatted_alerts.append({
            'type': 'critical',
            'title': f"Critical: {alert.get('metric', 'Alert')}",
            'detail': alert.get('message', 'Critical issue detected'),
            'time': 'Now'
        })
    
    # Warning alerts
    for alert in alerts.get('warning', [])[:2]:
        formatted_alerts.append({
            'type': 'warning',
            'title': f"Warning: {alert.get('metric', 'Alert')}", 
            'detail': alert.get('message', 'Warning condition'),
            'time': '2 min ago'
        })
    
    # Offline alerts
    for alert in alerts.get('offline', [])[:2]:
        formatted_alerts.append({
            'type': 'critical',
            'title': 'VM Offline',
            'detail': alert.get('message', 'VM is offline'),
            'time': 'Now'
        })
    
    # Success message if no alerts
    if not formatted_alerts:
        healthy_count = len(alerts.get('healthy', []))
        formatted_alerts.append({
            'type': 'success',
            'title': 'All Systems Normal',
            'detail': f"{healthy_count} VMs running normally",
            'time': 'Just now'
        })
    
    return formatted_alerts

def get_vm_data():
    """Get VM data with Zabbix integration and caching"""
    now = datetime.now()
    
    # Check cache
    if (cache['data'] is not None and 
        cache['timestamp'] is not None and 
        (now - cache['timestamp']).total_seconds() < cache['cache_duration']):
        print(f"📋 Using cached data (age: {(now - cache['timestamp']).total_seconds():.1f}s)")
        return cache['data']
    
    print(f"🔍 Fetching fresh data from Zabbix...")
    
    # If Zabbix is not available, use demo data
    if not ZABBIX_AVAILABLE:
        print(f"⚠️ Zabbix module not available, using demo data")
        return get_demo_data_with_status("Zabbix module not available")
    
    try:
        # Try to fetch fresh data from Zabbix
        client = EnhancedZabbixClient()
        
        print(f"🔌 Attempting to connect to Zabbix...")
        if not client.connect():
            print(f"❌ Zabbix connection failed")
            cache['error_count'] += 1
            cache['last_error'] = "Connection failed"
            return get_demo_data_with_error()
        
        print(f"✅ Connected to Zabbix successfully")
        
        # Fetch hosts
        print(f"📡 Fetching VM hosts...")
        hosts = client.fetch_hosts()
        
        if not hosts:
            print(f"⚠️ No hosts found in Zabbix")
            cache['error_count'] += 1
            cache['last_error'] = "No hosts found"
            client.disconnect()
            return get_demo_data_with_error()
        
        print(f"📊 Found {len(hosts)} hosts, enriching with performance data...")
        
        # Enrich with performance data
        vm_data = client.enrich_host_data(hosts)
        summary = calculate_enhanced_summary(vm_data)
        
        print(f"📈 Data enriched successfully")
        
        # Analyze alerts
        alerts = {}
        if ALERTS_AVAILABLE:
            try:
                alert_system = EnhancedAlertSystem()
                alerts = alert_system.analyze_vm_alerts(vm_data)
                print(f"🚨 Alert analysis completed")
            except Exception as alert_error:
                print(f"⚠️ Alert system error: {alert_error}")
                alerts = create_basic_alerts(vm_data)
        else:
            alerts = create_basic_alerts(vm_data)
        
        # Format for mobile API
        mobile_data = {
            'total': summary['total'],
            'online': summary['online'],
            'offline': summary['offline'],
            'performance': {
                'cpu': round(summary['performance']['avg_cpu'], 1),
                'memory': round(summary['performance']['avg_memory'], 1),
                'disk': round(summary['performance']['avg_disk'], 1)
            },
            'alerts': format_alerts(alerts),
            'system_status': summary['system_status'],
            'last_updated': now.isoformat(),
            'uptime_percentage': round((summary['online'] / summary['total'] * 100) if summary['total'] > 0 else 100, 1),
            'data_source': 'zabbix',
            'error_count': 0,
            'cache_duration': cache['cache_duration'],
            'cache_age_seconds': 0
        }
        
        # Update cache and historical data
        cache['data'] = mobile_data
        cache['timestamp'] = now
        cache['error_count'] = 0
        cache['last_error'] = None
        
        # Update historical data for trends
        update_historical_cache(mobile_data)
        
        client.disconnect()
        
        print(f"✅ Real Zabbix data cached successfully")
        print(f"📊 Summary: {summary['total']} total, {summary['online']} online, {summary['offline']} offline")
        
        return mobile_data
        
    except Exception as e:
        print(f"❌ Error fetching VM data: {e}")
        import traceback
        traceback.print_exc()
        
        cache['error_count'] += 1
        cache['last_error'] = str(e)
        
        try:
            if 'client' in locals():
                client.disconnect()
        except:
            pass
        
        print(f"🔄 Falling back to demo data (error #{cache['error_count']})")
        return get_demo_data_with_error()

def get_demo_data_with_status(status_msg):
    """Demo data with custom status message"""
    mobile_data = {
        'total': 27,
        'online': 26,
        'offline': 1,
        'performance': {
            'cpu': 4.6,
            'memory': 23.3,
            'disk': 12.5
        },
        'alerts': [
            {
                'type': 'warning',
                'title': 'Demo Mode',
                'detail': status_msg,
                'time': 'Now'
            }
        ],
        'system_status': 'demo',
        'last_updated': datetime.now().isoformat(),
        'uptime_percentage': 96.3,
        'data_source': 'demo',
        'cache_age_seconds': 0
    }
    
    # Update historical data for demo mode
    update_historical_cache(mobile_data)
    return mobile_data

def get_demo_data_with_error():
    """Demo data with error information"""
    mobile_data = {
        'total': 27,
        'online': 26,
        'offline': 1,
        'performance': {
            'cpu': 4.6,
            'memory': 23.3,
            'disk': 12.5
        },
        'alerts': [
            {
                'type': 'critical',
                'title': 'Zabbix Connection Error',
                'detail': f'Unable to connect to Zabbix (Error #{cache["error_count"]})',
                'time': 'Now'
            },
            {
                'type': 'warning',
                'title': 'Using Demo Data',
                'detail': 'Displaying sample data instead',
                'time': 'Now'
            }
        ],
        'system_status': 'error',
        'last_updated': datetime.now().isoformat(),
        'uptime_percentage': 96.3,
        'data_source': 'demo_fallback',
        'error_count': cache['error_count'],
        'last_error': cache['last_error'],
        'cache_age_seconds': 0
    }
    
    # Update historical data for demo mode
    update_historical_cache(mobile_data)
    return mobile_data

@app.route('/')
def index():
    """Root route"""
    return '''
    <h1>🖥️ VM Infrastructure Monitoring v2.0 - Enhanced</h1>
    <p>🚀 New Features:</p>
    <ul>
        <li>📈 <strong>Trends Charts</strong> - 24-hour performance graphs</li>
        <li>🗜️ <strong>Compressed API</strong> - Up to 70% faster responses</li>
        <li>📊 <strong>Historical Analytics</strong> - Performance trends & statistics</li>
        <li>⚡ <strong>Optimized Caching</strong> - Smart data management</li>
    </ul>
    <p>Choose your interface:</p>
    <ul>
        <li><a href="/mobile">📱 Enhanced Mobile Dashboard</a></li>
        <li><a href="/Services">🌱 Carbon Services Monitor</a></li>
        <li><a href="/api/dashboard">🔌 API Endpoint (Compressed)</a></li>
        <li><a href="/api/trends">📈 Trends Data API</a></li>
        <li><a href="/status">💚 Health Check</a></li>
        <li><a href="/debug">🔧 Debug Info</a></li>
    </ul>
    '''

@app.route('/api/dashboard')
@gzip_response
def api_dashboard():
    """API endpoint for dashboard data with compression"""
    data = get_vm_data()
    # Calculate cache age
    if cache['timestamp']:
        data['cache_age_seconds'] = (datetime.now() - cache['timestamp']).total_seconds()
    else:
        data['cache_age_seconds'] = 0
    
    # Add compression info
    data['compression_enabled'] = True
    data['api_version'] = '2.0'
    
    return data

@app.route('/api/trends')
@gzip_response
def api_trends():
    """API endpoint for trends data"""
    trends_data = get_trends_data()
    
    response_data = {
        'trends': trends_data,
        'generated_at': datetime.now().isoformat(),
        'data_points': len(cache['historical_data']) if cache['historical_data'] else 0,
        'compression_enabled': True,
        'api_version': '2.0'
    }
    
    return response_data

@app.route('/api/services')
@gzip_response
def api_services():
    """API endpoint for Carbon Services health data"""
    try:
        carbon_data = get_carbon_services_sync()
        carbon_data['api_version'] = '2.1'
        carbon_data['compression_enabled'] = True
        return carbon_data
    except Exception as e:
        return jsonify({
            'error': f'Carbon services check failed: {str(e)}',
            'services': {},
            'summary': {
                'total_services': 0,
                'healthy_services': 0,
                'warning_services': 0,
                'error_services': 0,
                'availability_percentage': 0,
                'overall_status': 'error'
            },
            'logs': [],
            'last_updated': datetime.now().isoformat()
        })

@app.route('/api/dashboard/enhanced')
@gzip_response
def api_dashboard_enhanced():
    """Enhanced dashboard API with VM + Service health data"""
    # Get VM data
    vm_data = get_vm_data()
    
    # Get service health data
    if SERVICE_HEALTH_AVAILABLE:
        try:
            service_data = get_service_health_data()
        except Exception as e:
            service_data = {
                'services': {},
                'summary': {
                    'total_count': 0,
                    'healthy_count': 0,
                    'warning_count': 0,
                    'critical_count': 0,
                    'availability_percentage': 0,
                    'overall_status': 'error'
                },
                'error': str(e)
            }
    else:
        service_data = {
            'services': {},
            'summary': {
                'total_count': 0,
                'healthy_count': 0,
                'warning_count': 0,
                'critical_count': 0,
                'availability_percentage': 0,
                'overall_status': 'unavailable'
            }
        }
    
    # Calculate combined health score
    vm_health_score = vm_data.get('summary', {}).get('uptime_percentage', 0)
    service_health_score = service_data.get('summary', {}).get('availability_percentage', 0)
    
    if SERVICE_HEALTH_AVAILABLE and service_data.get('summary', {}).get('total_count', 0) > 0:
        combined_health_score = (vm_health_score + service_health_score) / 2
    else:
        combined_health_score = vm_health_score
    
    # Combine data
    enhanced_data = {
        **vm_data,
        'services': service_data,
        'combined_health': {
            'vm_health_score': vm_health_score,
            'service_health_score': service_health_score,
            'combined_score': round(combined_health_score, 1),
            'overall_status': 'healthy' if combined_health_score >= 95 else 'warning' if combined_health_score >= 80 else 'critical'
        },
        'api_version': '2.1-enhanced',
        'compression_enabled': True
    }
    
    return enhanced_data

@app.route('/debug')
def debug_info():
    """Debug information endpoint"""
    return jsonify({
        'modules_available': {
            'zabbix_client': ZABBIX_AVAILABLE,
            'alert_system': ALERTS_AVAILABLE,
            'flask': True,
            'flask_cors': True,
            'gzip_compression': True
        },
        'cache_info': {
            'has_data': cache['data'] is not None,
            'last_update': cache['timestamp'].isoformat() if cache['timestamp'] else None,
            'cache_age_seconds': (datetime.now() - cache['timestamp']).total_seconds() if cache['timestamp'] else None,
            'cache_duration': cache['cache_duration'],
            'error_count': cache['error_count'],
            'last_error': cache['last_error'],
            'historical_data_points': len(cache['historical_data']) if cache['historical_data'] else 0,
            'trends_last_update': cache['trends_timestamp'].isoformat() if cache['trends_timestamp'] else None
        },
        'performance_info': {
            'compression_enabled': True,
            'api_version': '2.0',
            'features': ['Historical Trends', 'Gzip Compression', 'Smart Caching', 'Real-time Analytics']
        },
        'server_time': datetime.now().isoformat(),
        'python_version': sys.version,
        'working_directory': str(Path.cwd())
    })


@app.route('/mobile')
def mobile_dashboard():
    """Enhanced mobile dashboard v2.0 with trends charts"""
    from flask import make_response
    import time
    
    html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">
    <title>🖥️ VM Infrastructure Dashboard v2.3.0 - FORCE REFRESH</title>
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🖥️</text></svg>">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        :root {
            --primary-color: #00ff88;
            --secondary-color: #667eea;
            --accent-color: #764ba2;
            --success-color: #00ff88;
            --warning-color: #ffaa00;
            --error-color: #ff4444;
            --info-color: #0088ff;
            --background-primary: #0c0c0c;
            --background-secondary: #1a1a1a;
            --background-dark: #0c0c0c;
            --card-dark: rgba(20, 20, 20, 0.95);
            --text-light: #e0e0e0;
            --text-secondary: #aaa;
            --text-dark: #333333;
            --border-color: #333;
            --shadow-color: rgba(0, 0, 0, 0.5);
        }
        
        body {
            font-family: 'JetBrains Mono', 'Monaco', 'Consolas', monospace;
            background: linear-gradient(135deg, var(--background-primary) 0%, var(--background-secondary) 100%);
            min-height: 100vh;
            color: var(--text-light);
            padding: 20px;
            transition: all 0.3s ease;
        }
        
        
        .header {
            text-align: center;
            margin-bottom: 30px;
            position: relative;
        }
        
        .header h1 {
            font-size: 24px;
            margin-bottom: 5px;
            color: var(--primary-color);
            text-shadow: 0 0 10px rgba(0, 255, 136, 0.3);
        }
        
        .version-badge {
            display: inline-block;
            background: var(--info-color);
            color: white;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: bold;
            margin-left: 8px;
        }
        
        
        .tabs {
            display: flex;
            justify-content: center;
            margin-bottom: 30px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 5px;
            backdrop-filter: blur(10px);
        }
        
        .tab {
            flex: 1;
            padding: 10px 20px;
            text-align: center;
            background: transparent;
            border: none;
            color: white;
            cursor: pointer;
            border-radius: 10px;
            transition: all 0.3s ease;
            font-size: 14px;
        }
        
        .tab.active {
            background: rgba(255, 255, 255, 0.3);
            transform: translateY(-2px);
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
        }
        
        .status-cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }
        
        .status-card {
            background: var(--card-dark);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 20px;
            text-align: center;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            border: 1px solid var(--border-color);
            box-shadow: 0 5px 15px var(--shadow-color);
        }
        
        
        .status-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 35px var(--shadow-color);
            border-color: var(--primary-color);
        }
        
        .status-card .number {
            font-size: 32px;
            font-weight: bold;
            margin-bottom: 5px;
            color: var(--primary-color);
        }
        
        .status-card .label {
            font-size: 14px;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .section {
            background: var(--card-dark);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 30px;
            border: 1px solid var(--border-color);
        }
        
        
        .section h3 {
            margin-bottom: 20px;
            font-size: 18px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .metrics {
            display: grid;
            gap: 15px;
        }
        
        .metric {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .metric-name {
            font-weight: 500;
        }
        
        .metric-bar-container {
            flex: 1;
            margin: 0 15px;
            height: 8px;
            background: rgba(255, 255, 255, 0.2);
            border-radius: 4px;
            overflow: hidden;
        }
        
        .metric-bar {
            height: 100%;
            border-radius: 4px;
            transition: width 0.5s ease;
        }
        
        .metric-value {
            font-weight: bold;
            min-width: 40px;
            text-align: right;
        }
        
        .chart-container {
            position: relative;
            height: 300px;
            margin: 20px 0;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            padding: 15px;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        
        .stat-card {
            background: rgba(255, 255, 255, 0.1);
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            border-left: 4px solid var(--info-color);
        }
        
        .stat-card.warning {
            border-left-color: var(--warning-color);
        }
        
        .stat-card.success {
            border-left-color: var(--success-color);
        }
        
        .stat-card.error {
            border-left-color: var(--error-color);
        }
        
        .stat-value {
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .stat-label {
            font-size: 12px;
            opacity: 0.8;
            text-transform: uppercase;
        }
        
        .alert {
            display: flex;
            align-items: flex-start;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 10px;
            border-left: 4px solid;
            transition: all 0.3s ease;
        }
        
        .alert:hover {
            transform: translateX(5px);
        }
        
        .alert.critical {
            background: rgba(244, 67, 54, 0.1);
            border-left-color: var(--error-color);
        }
        
        .alert.warning {
            background: rgba(255, 152, 0, 0.1);
            border-left-color: var(--warning-color);
        }
        
        .alert.success {
            background: rgba(76, 175, 80, 0.1);
            border-left-color: var(--success-color);
        }
        
        .alert-icon {
            font-size: 20px;
            margin-right: 15px;
            margin-top: 2px;
        }
        
        .alert-content {
            flex: 1;
        }
        
        .alert-title {
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .alert-detail {
            font-size: 14px;
            opacity: 0.8;
        }
        
        .alert-time {
            font-size: 12px;
            opacity: 0.6;
            margin-left: 10px;
            margin-top: 2px;
        }
        
        .loading {
            text-align: center;
            padding: 50px;
            font-size: 18px;
        }
        
        .loading .spinner {
            display: inline-block;
            width: 40px;
            height: 40px;
            border: 3px solid rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            border-top-color: white;
            animation: spin 1s ease-in-out infinite;
            margin-bottom: 20px;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        .error {
            background: rgba(244, 67, 54, 0.2);
            padding: 20px;
            border-radius: 12px;
            margin: 20px 0;
            border-left: 4px solid var(--error-color);
        }
        
        .footer {
            text-align: center;
            margin-top: 30px;
            padding: 20px;
            font-size: 12px;
            opacity: 0.7;
        }
        
        .refresh-btn {
            background: rgba(255, 255, 255, 0.2);
            border: none;
            border-radius: 25px;
            padding: 10px 20px;
            color: white;
            cursor: pointer;
            font-size: 14px;
            margin: 0 10px;
            transition: all 0.3s ease;
        }
        
        .refresh-btn:hover {
            background: rgba(255, 255, 255, 0.3);
            transform: translateY(-2px);
        }
        
        .data-source-indicator {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: bold;
            text-transform: uppercase;
            margin-left: 10px;
        }
        
        .data-source-zabbix {
            background: var(--success-color);
            color: white;
        }
        
        .data-source-demo {
            background: var(--warning-color);
            color: white;
        }
        
        .data-source-error {
            background: var(--error-color);
            color: white;
        }
        
        .performance-indicator {
            display: inline-block;
            padding: 2px 6px;
            border-radius: 8px;
            font-size: 10px;
            font-weight: bold;
            margin-left: 8px;
        }
        
        .performance-indicator.fast {
            background: var(--success-color);
            color: white;
        }
        
        .performance-indicator.compressed {
            background: var(--info-color);
            color: white;
        }
        
        @media (max-width: 768px) {
            body {
                padding: 10px;
            }
            
            .status-cards {
                grid-template-columns: repeat(2, 1fr);
            }
            
            .header h1 {
                font-size: 20px;
            }
            
            
            .chart-container {
                height: 250px;
            }
            
            .tabs {
                flex-direction: column;
            }
            
            .tab {
                margin-bottom: 5px;
            }
        }
        
        .keyboard-shortcuts {
            position: fixed;
            top: 10px;
            left: 10px;
            background: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 10px;
            border-radius: 8px;
            font-size: 12px;
            opacity: 0;
            visibility: hidden;
            transition: all 0.3s ease;
            z-index: 1000;
        }
        
        .keyboard-shortcuts.show {
            opacity: 1;
            visibility: visible;
        }
        
        .feature-highlight {
            background: linear-gradient(45deg, var(--info-color), var(--primary-color));
            color: white;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
        }
        
        .feature-highlight h4 {
            margin-bottom: 8px;
            font-size: 16px;
        }
        
        .feature-highlight p {
            font-size: 13px;
            opacity: 0.9;
        }
        
        /* Service Health Specific Styles */
        .service-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }

        .service-group {
            margin-bottom: 30px;
        }

        .service-group-header {
            margin-bottom: 20px;
            padding: 15px 20px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            border-left: 4px solid #00ff88;
        }

        .service-group-header h3 {
            margin: 0;
            font-size: 1.2rem;
            font-weight: 600;
            color: #ffffff;
        }

        .service-group-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 20px;
        }
        
        .service-card {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            padding: 20px;
            border-left: 4px solid;
            transition: all 0.3s ease;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .service-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2);
        }

        .service-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }

        .service-header h4 {
            margin: 0;
            font-size: 16px;
            font-weight: 600;
            color: white;
        }

        .status-badge {
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .status-badge.ok { background: var(--success-color); color: white; }
        .status-badge.warning { background: var(--warning-color); color: white; }
        .status-badge.error { background: var(--error-color); color: white; }
        .status-badge.unknown { background: #666; color: white; }

        .service-metrics {
            margin: 15px 0;
        }

        .metric-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }

        .metric-row:last-child {
            border-bottom: none;
        }

        .metric-label {
            font-size: 13px;
            color: rgba(255, 255, 255, 0.7);
            min-width: 70px;
        }

        .metric-value {
            font-size: 13px;
            color: var(--success-color);
            font-weight: 600;
            min-width: 50px;
        }

        .metric-time {
            font-size: 13px;
            color: white;
            font-weight: 500;
            min-width: 60px;
        }

        .metric-info {
            font-size: 10px;
            color: rgba(255, 255, 255, 0.5);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .sub-services {
            margin-top: 15px;
        }

        .sub-service-status {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 6px 0;
        }

        .sub-service-name {
            font-size: 12px;
            color: rgba(255, 255, 255, 0.8);
            text-transform: lowercase;
        }

        .sub-service-badge {
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 10px;
            font-weight: bold;
            text-transform: uppercase;
        }

        .sub-service-badge.status-healthy { background: var(--success-color); color: white; }
        .sub-service-badge.status-warning { background: var(--warning-color); color: white; }
        .sub-service-badge.status-error { background: var(--error-color); color: white; }

        .alerts-container {
            margin-top: 15px;
        }

        .alert-item {
            display: flex;
            align-items: center;
            padding: 15px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 8px;
            border-left: 4px solid var(--warning-color);
            margin-bottom: 10px;
        }

        .alert-item.warning {
            border-left-color: var(--warning-color);
        }

        .alert-item.error {
            border-left-color: var(--error-color);
        }

        .alert-icon {
            font-size: 20px;
            margin-right: 12px;
        }

        .alert-content {
            flex: 1;
        }

        .alert-title {
            font-weight: 600;
            color: white;
            margin-bottom: 4px;
        }

        .alert-description {
            font-size: 13px;
            color: rgba(255, 255, 255, 0.8);
        }

        .alert-badge {
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 10px;
            font-weight: bold;
            text-transform: uppercase;
            background: var(--warning-color);
            color: white;
        }
        
        .service-cards-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        
        .service-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        
        .service-header h4 {
            margin: 0;
            font-size: 18px;
            color: #fff;
        }
        
        .status-badge {
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
            text-transform: uppercase;
        }
        
        .status-badge.ok { background: #00ff88; color: #000; }
        .status-badge.error { background: #ff4444; color: #fff; }
        .status-badge.warning { background: #ffaa00; color: #000; }
        .status-badge.unknown { background: #666; color: #fff; }
        
        .service-metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 10px;
            margin-bottom: 15px;
        }
        
        .metric {
            text-align: center;
            padding: 8px;
            background: rgba(0,0,0,0.3);
            border-radius: 8px;
        }
        
        .metric-label {
            display: block;
            font-size: 11px;
            color: #ccc;
            margin-bottom: 4px;
        }
        
        .metric-value {
            display: block;
            font-size: 14px;
            font-weight: bold;
            color: #00ff88;
        }
        
        .sub-services h5 {
            margin: 0 0 8px 0;
            font-size: 14px;
            color: #ccc;
        }
        
        .sub-service-list {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }
        
        .sub-service {
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: bold;
        }
        
        .sub-service.status-healthy { background: #00ff88; color: #000; }
        .sub-service.status-error { background: #ff4444; color: #fff; }
        .sub-service.status-warning { background: #ffaa00; color: #000; }
        .sub-service.status-unknown { background: #666; color: #fff; }
        
        .status-healthy { border-left-color: #00ff88; }
        .status-error { border-left-color: #ff4444; }
        .status-warning { border-left-color: #ffaa00; }
        .status-unknown { border-left-color: #666; }
        
        /* Trends specific styles */
        .trends-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        
        .trend-card {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 15px;
            text-align: center;
        }
        
        .trend-card h5 {
            margin: 0 0 10px 0;
            color: #ccc;
            font-size: 14px;
        }
        
        .trend-value {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 5px;
        }
        
        .current-value {
            font-size: 24px;
            font-weight: bold;
            color: #00ff88;
        }
        
        .trend-change {
            font-size: 12px;
            font-weight: bold;
            padding: 2px 8px;
            border-radius: 10px;
        }
        
        .trend-up { background: #ff4444; color: #fff; }
        .trend-down { background: #00ff88; color: #000; }
        .trend-stable { background: #666; color: #fff; }
        
        /* Service details styles */
        .service-overview {
            margin-bottom: 20px;
        }
        
        .summary-card {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 20px;
        }
        
        .summary-card h4 {
            margin: 0 0 15px 0;
            color: #fff;
        }
        
        .status-indicators {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        
        .indicator {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 14px;
        }
        
        .indicator-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
        }
        
        .indicator.status-healthy .indicator-dot { background: #00ff88; }
        .indicator.status-error .indicator-dot { background: #ff4444; }
        .indicator.status-warning .indicator-dot { background: #ffaa00; }
        .indicator.status-unknown .indicator-dot { background: #666; }
        
        .service-details {
            margin: 15px 0;
        }
        
        .detail-row {
            display: flex;
            justify-content: space-between;
            margin-bottom: 8px;
            padding: 5px 0;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        
        .detail-label {
            color: #ccc;
            font-size: 13px;
        }
        
        .detail-value {
            color: #fff;
            font-size: 13px;
            font-weight: bold;
        }
        
        .sub-service-item {
            display: flex;
            justify-content: space-between;
            margin-bottom: 5px;
            padding: 5px 8px;
            border-radius: 5px;
            font-size: 12px;
        }
        
        .sub-service-item.status-healthy { background: rgba(0, 255, 136, 0.2); }
        .sub-service-item.status-error { background: rgba(255, 68, 68, 0.2); }
        .sub-service-item.status-warning { background: rgba(255, 170, 0, 0.2); }
        .sub-service-item.status-unknown { background: rgba(102, 102, 102, 0.2); }
        
        .sub-service-name {
            color: #ccc;
        }
        
        .sub-service-status {
            font-weight: bold;
        }
        
        .mock-chart {
            background: rgba(0,0,0,0.3);
            border-radius: 8px;
            padding: 15px;
            margin-top: 15px;
        }
        
        .mock-chart pre {
            margin: 0;
            font-size: 11px;
            max-height: 200px;
            overflow-y: auto;
        }
        
        .service-card.status-healthy { border-left-color: var(--success-color); }
        .service-card.status-warning { border-left-color: var(--warning-color); }
        .service-card.status-critical, .service-card.status-error { border-left-color: var(--error-color); }
        
        .service-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        
        .service-name {
            font-size: 16px;
            font-weight: bold;
            color: var(--text-light);
        }
        
        .service-status-badge {
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: bold;
            text-transform: uppercase;
        }
        
        .service-status-badge.status-healthy {
            background: rgba(76, 175, 80, 0.2);
            color: #4CAF50;
            border: 1px solid #4CAF50;
        }
        
        .service-status-badge.status-warning {
            background: rgba(255, 152, 0, 0.2);
            color: #FF9800;
            border: 1px solid #FF9800;
        }
        
        .service-status-badge.status-critical, .service-status-badge.status-error {
            background: rgba(244, 67, 54, 0.2);
            color: #F44336;
            border: 1px solid #F44336;
        }
        
        .service-metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
            gap: 12px;
            margin: 15px 0;
        }
        
        .service-metric {
            text-align: center;
            padding: 8px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 8px;
        }
        
        .service-metric-value {
            font-size: 14px;
            font-weight: bold;
            color: var(--text-light);
            margin-bottom: 4px;
        }
        
        .service-metric-label {
            font-size: 11px;
            color: rgba(255, 255, 255, 0.7);
            text-transform: uppercase;
        }
        
        .service-endpoints {
            margin-top: 15px;
        }
        
        .service-endpoint {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 6px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            font-size: 13px;
        }
        
        .service-endpoint:last-child { border-bottom: none; }
        
        .endpoint-name { color: rgba(255, 255, 255, 0.8); }
        
        .endpoint-status {
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 10px;
            font-weight: bold;
            text-transform: uppercase;
        }
        
        .endpoint-status.status-ok {
            background: rgba(76, 175, 80, 0.3);
            color: #4CAF50;
        }
        
        .endpoint-status.status-error {
            background: rgba(244, 67, 54, 0.3);
            color: #F44336;
        }
        
        .alerts-container {
            max-height: 300px;
            overflow-y: auto;
        }
        
        .service-alert {
            background: rgba(255, 255, 255, 0.1);
            border-left: 4px solid;
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 10px;
        }
        
        .service-alert.alert-critical { border-left-color: var(--error-color); }
        .service-alert.alert-warning { border-left-color: var(--warning-color); }
        
        .alert-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }
        
        .alert-level {
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 10px;
            font-weight: bold;
            text-transform: uppercase;
        }
        
        .alert-level.critical {
            background: rgba(244, 67, 54, 0.3);
            color: #F44336;
        }
        
        .alert-level.warning {
            background: rgba(255, 152, 0, 0.3);
            color: #FF9800;
        }
        
        .alert-message {
            font-size: 13px;
            color: rgba(255, 255, 255, 0.9);
            line-height: 1.4;
        }
        
        .service-loading {
            text-align: center;
            padding: 40px;
            color: rgba(255, 255, 255, 0.7);
        }
        
        .service-error {
            background: rgba(244, 67, 54, 0.2);
            border: 1px solid #F44336;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            color: #F44336;
        }
    </style>
</head>
<body>
    <div class="keyboard-shortcuts" id="shortcuts">
        <strong>Keyboard Shortcuts:</strong><br>
        R - Refresh data<br>
        T - Toggle theme<br>
        1,2,3,4 - Switch tabs<br>
        ? - Show/hide shortcuts
    </div>

    <div class="header">
        <h1>🖥️ VM Infrastructure Dashboard
            <span class="version-badge">v2.0</span>
        </h1>
        <p>Real-time monitoring system
            <span class="data-source-indicator" id="dataSourceIndicator">Loading...</span>
            <span class="performance-indicator compressed" id="compressionIndicator">GZIP</span>
            <a href="/Services" style="margin-left: 10px; color: #00ff88; text-decoration: none; font-weight: bold;">🔧 Services Monitor</a>
        </p>
    </div>

    <div class="feature-highlight">
        <h4>🚀 New in v2.0</h4>
        <p>📈 Historical trends charts • 🗜️ 70% faster API responses • 📊 24-hour analytics • ⚡ Smart caching</p>
    </div>

    <div class="tabs">
        <button class="tab active" onclick="showTab('overview')">📊 Overview</button>
        <button class="tab" onclick="showTab('services')">🛡️ Services</button>
        <button class="tab" onclick="showTab('trends')">📈 Trends</button>
        <button class="tab" onclick="showTab('alerts')">🚨 Alerts</button>
    </div>

    <div class="loading" id="loading">
        <div class="spinner"></div>
        🔄 Loading enhanced dashboard...
    </div>

    <div id="dashboard" style="display: none;">
        <!-- Overview Tab -->
        <div id="overview-tab" class="tab-content active">
            <div class="status-cards">
                <div class="status-card">
                    <div class="number" id="totalVMs">--</div>
                    <div class="label">Total VMs</div>
                </div>
                <div class="status-card">
                    <div class="number" id="onlineVMs" style="color: #4CAF50;">--</div>
                    <div class="label">Online</div>
                </div>
                <div class="status-card">
                    <div class="number" id="offlineVMs" style="color: #F44336;">--</div>
                    <div class="label">Offline</div>
                </div>
                <div class="status-card">
                    <div class="number" id="uptimePercentage">--%</div>
                    <div class="label">Uptime</div>
                </div>
            </div>

            <div class="section">
                <h3>📊 Performance Metrics</h3>
                <div class="metrics">
                    <div class="metric">
                        <span class="metric-name">🔥 CPU Usage</span>
                        <div class="metric-bar-container">
                            <div class="metric-bar" id="cpuBar" style="background: #FF6B6B;"></div>
                        </div>
                        <span class="metric-value" id="cpuValue">--%</span>
                    </div>
                    <div class="metric">
                        <span class="metric-name">🧠 Memory Usage</span>
                        <div class="metric-bar-container">
                            <div class="metric-bar" id="memoryBar" style="background: #4ECDC4;"></div>
                        </div>
                        <span class="metric-value" id="memoryValue">--%</span>
                    </div>
                    <div class="metric">
                        <span class="metric-name">💾 Disk Usage</span>
                        <div class="metric-bar-container">
                            <div class="metric-bar" id="diskBar" style="background: #45B7D1;"></div>
                        </div>
                        <span class="metric-value" id="diskValue">--%</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Services Tab -->
        <div id="services-tab" class="tab-content">
            <div class="section">
                <h3>🛡️ Service Health Monitoring</h3>
                <div id="serviceHealthGrid" class="service-grid">
                    <div class="service-loading">Loading services...</div>
                </div>
            </div>
        </div>

        <!-- Trends Tab -->
        <div id="trends-tab" class="tab-content">
            <div class="section">
                <h3>📈 24-Hour Performance Trends</h3>
                
                <div class="stats-grid" id="trendsStats">
                    <div class="stat-card">
                        <div class="stat-value" id="avgCpu24h">--%</div>
                        <div class="stat-label">Avg CPU 24h</div>
                    </div>
                    <div class="stat-card warning">
                        <div class="stat-value" id="maxCpu24h">--%</div>
                        <div class="stat-label">Peak CPU 24h</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value" id="avgMemory24h">--%</div>
                        <div class="stat-label">Avg Memory 24h</div>
                    </div>
                    <div class="stat-card success">
                        <div class="stat-value" id="uptime24h">--%</div>
                        <div class="stat-label">Uptime 24h</div>
                    </div>
                </div>
                
                <div class="chart-container">
                    <canvas id="performanceChart"></canvas>
                </div>
            </div>

            <div class="section">
                <h3>🔗 VM Status Timeline</h3>
                <div class="chart-container">
                    <canvas id="statusChart"></canvas>
                </div>
            </div>

            <div class="section">
                <h3>🚨 Alerts Timeline</h3>
                <div class="chart-container">
                    <canvas id="alertsChart"></canvas>
                </div>
            </div>
        </div>

        <!-- Alerts Tab -->
        <div id="alerts-tab" class="tab-content">
            <div class="section">
                <h3>🚨 System Alerts</h3>
                <div id="alertsContainer">
                    <!-- Alerts will be populated by JavaScript -->
                </div>
            </div>
        </div>
    </div>

    <div class="footer">
        <button class="refresh-btn" onclick="loadDashboardData()">🔄 Refresh</button>
        <button class="refresh-btn" onclick="loadTrendsData()">📈 Update Trends</button>
        <button class="refresh-btn" onclick="toggleShortcuts()">⌨️ Shortcuts</button>
        <br><br>
        <div id="lastUpdated">Last updated: --</div>
        <div id="cacheInfo" style="font-size: 10px; margin-top: 5px;">Cache: --</div>
        <div id="performanceInfo" style="font-size: 10px; margin-top: 2px;">Performance: --</div>
    </div>

    <script>
        let dashboardData = null;
        let trendsData = null;
        let serviceHealthData = null;
        let refreshInterval = null;
        let showShortcuts = false;
        let performanceChart = null;
        let statusChart = null;
        let alertsChart = null;
        let currentTab = 'overview';

        // Tab management
        function showTab(tabName) {
            console.log('🔄 showTab called with:', tabName);
            
            if (!tabName) {
                console.error('❌ showTab: tabName is undefined');
                return;
            }
            
            // Hide all tab contents
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            
            // Remove active class from all tabs
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Show selected tab content
            const targetTab = document.getElementById(tabName + '-tab');
            if (targetTab) {
                targetTab.classList.add('active');
                console.log('✅ Tab activated:', tabName + '-tab');
            } else {
                console.error('❌ Tab not found:', tabName + '-tab');
            }
            
            // Add active class to clicked tab (safe check)
            if (typeof event !== 'undefined' && event && event.target) {
                event.target.classList.add('active');
            } else {
                // If called programmatically, find and activate the corresponding tab button
                const tabButton = document.querySelector(`button[onclick="showTab('${tabName}')"]`);
                if (tabButton) {
                    tabButton.classList.add('active');
                }
            }
            
            currentTab = tabName;
            
            // Load data based on tab
            if (tabName === 'trends' && !trendsData) {
                console.log('📈 Loading trends data...');
                loadTrendsData();
            } else if (tabName === 'services') {
                console.log('🛡️ Loading service health data dynamically...');
                // Load services dynamically using updateServiceHealthCards
                fetch('/api/services/health')
                    .then(response => response.json())
                    .then(services => {
                        console.log('📊 Loaded services for Services tab:', services);
                        updateServiceHealthCards(services);
                    })
                    .catch(error => {
                        console.error('❌ Error loading services:', error);
                        const grid = document.getElementById('serviceHealthGrid');
                        if (grid) {
                            grid.innerHTML = '<div class="service-error">❌ Failed to load services</div>';
                        }
                    });
            }
        }


        // Show/hide keyboard shortcuts
        function toggleShortcuts() {
            showShortcuts = !showShortcuts;
            const shortcuts = document.getElementById('shortcuts');
            shortcuts.classList.toggle('show', showShortcuts);
        }

        // Load dashboard data with performance tracking
        async function loadDashboardData() {
            const startTime = performance.now();
            
            try {
                console.log('Loading dashboard data...');
                document.getElementById('loading').style.display = 'block';
                document.getElementById('dashboard').style.display = 'none';

                const response = await fetch('/api/dashboard', {
                    headers: {
                        'Accept-Encoding': 'gzip, deflate'
                    }
                });
                
                console.log('Dashboard API response status:', response.status);
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }

                const data = await response.json();
                console.log('Dashboard data loaded:', data);
                dashboardData = data;
                
                const endTime = performance.now();
                const loadTime = endTime - startTime;
                
                updateDashboard(data);
                updatePerformanceInfo(loadTime, response);
                
                document.getElementById('loading').style.display = 'none';
                document.getElementById('dashboard').style.display = 'block';
                
                console.log('Dashboard updated successfully');
                
            } catch (error) {
                console.error('Error loading dashboard data:', error);
                document.getElementById('loading').style.display = 'none';
                showError(`Failed to load dashboard: ${error.message}`);
            }
        }

        // Load trends data
        async function loadTrendsData() {
            const startTime = performance.now();
            
            try {
                const response = await fetch('/api/trends', {
                    headers: {
                        'Accept-Encoding': 'gzip, deflate'
                    }
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }

                const data = await response.json();
                trendsData = data.trends;
                
                const endTime = performance.now();
                console.log(`Trends data loaded in ${(endTime - startTime).toFixed(1)}ms`);
                
                updateTrendsView(data);
                
            } catch (error) {
                console.error('Error loading trends data:', error);
                showError(`Failed to load trends: ${error.message}`, 'trends-tab');
            }
        }

        // Update trends view with Carbon Services data
        function updateTrendsView(data) {
            try {
                // Show Carbon Services in Trends tab
                const trendsTabContent = document.getElementById('trends-tab');
                if (!trendsTabContent) {
                    console.error('Trends tab content not found');
                    return;
                }
                
                // Get Carbon services data
                fetch('/api/services/health')
                    .then(response => response.json())
                    .then(carbonData => {
                        const carbonReceipt = carbonData.carbon_receipt || {};
                        const carbonFootprint = carbonData.carbon_footprint || {};
                        
                        trendsTabContent.innerHTML = `
                            <div class="section">
                                <h3>🌱 Carbon Services Status</h3>
                                <div class="service-cards-grid">
                                    <div class="service-card ${getStatusClass(carbonReceipt.status)}">
                                        <div class="service-header">
                                            <h4>📋 Carbon Receipt API</h4>
                                            <span class="status-badge ${carbonReceipt.status || 'unknown'}">${carbonReceipt.status || 'Unknown'}</span>
                                        </div>
                                        <div class="service-metrics">
                                            <div class="metric">
                                                <span class="metric-label">Uptime:</span>
                                                <span class="metric-value">${carbonReceipt.uptime || 'N/A'}</span>
                                            </div>
                                            <div class="metric">
                                                <span class="metric-label">Database:</span>
                                                <span class="metric-value">${carbonReceipt.database_status || 'N/A'}</span>
                                            </div>
                                            <div class="metric">
                                                <span class="metric-label">Response Time:</span>
                                                <span class="metric-value">${carbonReceipt.response_time_ms || 0}ms</span>
                                            </div>
                                        </div>
                                        <div class="sub-services">
                                            <h5>Sub-Services:</h5>
                                            <div class="sub-service-list">
                                                ${Object.entries(carbonReceipt.sub_services || {}).map(([key, service]) => 
                                                    `<span class="sub-service ${getStatusClass(service)}">${key}: ${service.status || 'Unknown'}</span>`
                                                ).join('')}
                                            </div>
                                        </div>
                                    </div>
                                    
                                    <div class="service-card ${getStatusClass(carbonFootprint.status)}">
                                        <div class="service-header">
                                            <h4>🌍 Carbon Footprint API</h4>
                                            <span class="status-badge ${carbonFootprint.status || 'unknown'}">${carbonFootprint.status || 'Unknown'}</span>
                                        </div>
                                        <div class="service-metrics">
                                            <div class="metric">
                                                <span class="metric-label">Uptime:</span>
                                                <span class="metric-value">${carbonFootprint.uptime || 'N/A'}</span>
                                            </div>
                                            <div class="metric">
                                                <span class="metric-label">Database:</span>
                                                <span class="metric-value">${carbonFootprint.database_status || 'N/A'}</span>
                                            </div>
                                            <div class="metric">
                                                <span class="metric-label">Response Time:</span>
                                                <span class="metric-value">${carbonFootprint.response_time_ms || 0}ms</span>
                                            </div>
                                        </div>
                                        <div class="sub-services">
                                            <h5>Sub-Services:</h5>
                                            <div class="sub-service-list">
                                                ${Object.entries(carbonFootprint.sub_services || {}).map(([key, service]) => 
                                                    `<span class="sub-service ${getStatusClass(service)}">${key}: ${service.status || 'Unknown'}</span>`
                                                ).join('')}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        `;
                    })
                    .catch(error => {
                        console.error('Error loading carbon services:', error);
                        trendsTabContent.innerHTML = `
                            <div class="section">
                                <h3>🌱 Carbon Services Status</h3>
                                <div class="error-message">
                                    <p>⚠️ Unable to load Carbon Services data</p>
                                    <p>Error: ${error.message}</p>
                                </div>
                            </div>
                        `;
                    });
                    
            } catch (error) {
                console.error('Error updating trends view:', error);
            }
        }
        
        // Helper function to get status class
        function getStatusClass(status) {
            // Handle both string and object status
            let statusStr = '';
            if (typeof status === 'string') {
                statusStr = status;
            } else if (typeof status === 'object' && status !== null) {
                statusStr = status.status || status.name || '';
            } else {
                statusStr = String(status || '');
            }
            
            switch(statusStr.toLowerCase()) {
                case 'ok': 
                case 'healthy': 
                case 'up': 
                    return 'status-healthy';
                case 'warning': 
                case 'degraded': 
                case 'timeout':
                    return 'status-warning';
                case 'error': 
                case 'down': 
                case 'critical': 
                    return 'status-error';
                default: 
                    return 'status-unknown';
            }
        }
        
        // Helper function to get trend class
        function getTrendClass(change) {
            if (change > 0) return 'trend-up';
            if (change < 0) return 'trend-down';
            return 'trend-stable';
        }

        // Load service health data
        async function loadServiceHealthData() {
            console.log('🚀 loadServiceHealthData() called');
            const startTime = performance.now();
            
            try {
                console.log('📡 Fetching /api/services/health...');
                const response = await fetch('/api/services/health', {
                    headers: {
                        'Accept-Encoding': 'gzip, deflate'
                    }
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }

                const data = await response.json();
                serviceHealthData = data;
                
                const endTime = performance.now();
                console.log(`✅ Service health data loaded in ${(endTime - startTime).toFixed(1)}ms`);
                console.log('📦 Data received:', data);
                
                updateServiceHealthCards(data);
                
            } catch (error) {
                console.error('Error loading service health data:', error);
                showServiceHealthError(`Failed to load service health: ${error.message}`);
            }
        }

        // Load service health data
        async function loadServiceHealth() {
            const startTime = performance.now();
            
            try {
                const response = await fetch('/api/services', {
                    headers: {
                        'Accept-Encoding': 'gzip, deflate'
                    }
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }

                const data = await response.json();
                serviceHealthData = data;
                
                const endTime = performance.now();
                const loadTime = endTime - startTime;
                
                updateServiceHealth(data);
                
                console.log(`🛡️ Service health loaded in ${loadTime.toFixed(2)}ms`);
                
            } catch (error) {
                console.error('Error loading service health data:', error);
                showServiceError(error.message);
            }
        }

        // Update service health UI
        function updateServiceHealth(data) {
            if (!data || data.error) {
                showServiceError(data?.error || 'Service health data unavailable');
                return;
            }

            const summary = data.summary || {};
            const services = data.services || {};

            // Update service stats
            document.getElementById('totalServices').textContent = summary.total_count || 0;
            document.getElementById('healthyServices').textContent = summary.healthy_count || 0;
            document.getElementById('warningServices').textContent = summary.warning_count || 0;
            document.getElementById('criticalServices').textContent = summary.critical_count || 0;
            document.getElementById('serviceAvailability').textContent = `${summary.availability_percentage || 0}%`;

            // Update service health cards
            updateServiceHealthCards(services);
            
            // Update service alerts
            updateServiceAlerts(data);
        }

        // Update service health cards
        function updateServiceHealthCards(services) {
            console.log('🔧 updateServiceHealthCards called with:', services);
            console.log('🔧 Services data type:', typeof services);
            console.log('🔧 Services keys count:', services ? Object.keys(services).length : 'null/undefined');
            
            const grid = document.getElementById('serviceHealthGrid');
            console.log('🔧 serviceHealthGrid element:', grid);
            
            if (!grid) {
                console.error('❌ serviceHealthGrid element not found!');
                return;
            }
            
            grid.innerHTML = '';

            if (!services || Object.keys(services).length === 0) {
                console.log('❌ No services data:', services);
                grid.innerHTML = '<div class="service-loading">No service data available</div>';
                return;
            }

            // Separate services into two groups
            const carbonFootprintServices = [];
            const carbonReceiptServices = [];

            Object.entries(services).forEach(([serviceId, serviceData]) => {
                console.log('🔧 Processing service:', serviceId, serviceData);
                if (['carbon_footprint_uat', 'carbon_footprint_prd', 'etax_software', 'rancher_management', 'database_cluster'].includes(serviceId)) {
                    console.log('🌍 Adding to Carbon Footprint:', serviceId);
                    carbonFootprintServices.push({id: serviceId, data: serviceData});
                } else if (['etax_api', 'one_api', 'one_box_api', 'vekin_api'].includes(serviceId)) {
                    console.log('📋 Adding to Carbon Receipt:', serviceId);
                    carbonReceiptServices.push({id: serviceId, data: serviceData});
                } else {
                    console.log('⚠️ Service not matched:', serviceId);
                }
            });
            
            console.log('🌍 Carbon Footprint Services:', carbonFootprintServices);
            console.log('📋 Carbon Receipt Services:', carbonReceiptServices);

            // Create Carbon Footprint Services section
            if (carbonFootprintServices.length > 0) {
                const footprintSection = document.createElement('div');
                footprintSection.className = 'service-group';
                footprintSection.innerHTML = `
                    <div class="service-group-header">
                        <h3>🌍 Carbon Footprint Services (${carbonFootprintServices.length})</h3>
                    </div>
                    <div class="service-group-grid" id="carbonFootprintGrid"></div>
                `;
                grid.appendChild(footprintSection);

                const footprintGrid = footprintSection.querySelector('#carbonFootprintGrid');
                carbonFootprintServices.forEach(service => {
                    if (service && service.data) {
                        const card = createServiceHealthCard(service.id, service.data);
                        footprintGrid.appendChild(card);
                    } else {
                        console.error('❌ Invalid service data:', service);
                    }
                });
            }

            // Create Carbon Receipt Services section  
            if (carbonReceiptServices.length > 0) {
                const receiptSection = document.createElement('div');
                receiptSection.className = 'service-group';
                receiptSection.innerHTML = `
                    <div class="service-group-header">
                        <h3>📋 Carbon Receipt Services (${carbonReceiptServices.length})</h3>
                    </div>
                    <div class="service-group-grid" id="carbonReceiptGrid"></div>
                `;
                grid.appendChild(receiptSection);

                const receiptGrid = receiptSection.querySelector('#carbonReceiptGrid');
                carbonReceiptServices.forEach(service => {
                    if (service && service.data) {
                        const card = createServiceHealthCard(service.id, service.data);
                        receiptGrid.appendChild(card);
                    } else {
                        console.error('❌ Invalid service data:', service);
                    }
                });
            }
        }

        // REMOVED DUPLICATE FUNCTION - Using createServiceHealthCard(serviceId, data) below

        // Format endpoint names
        function formatEndpointName(endpoint) {
            return endpoint
                .replace(/_/g, ' ')
                .replace(/status|api/gi, '')
                .replace(/\\s+/g, ' ')
                .trim()
                .replace(/^./, str => str.toUpperCase()) || endpoint;
        }

        // Update service alerts
        function updateServiceAlerts(data) {
            const container = document.getElementById('serviceAlerts');
            container.innerHTML = '';

            // Get alerts from service health data
            const alerts = [];
            
            if (data.services) {
                Object.entries(data.services).forEach(([serviceId, service]) => {
                    if (service.health_level === 'critical') {
                        alerts.push({
                            level: 'critical',
                            service: service.name,
                            message: service.error || 'Service is in critical state',
                            timestamp: service.last_check
                        });
                    } else if (service.health_level === 'warning') {
                        const issues = [];
                        if (service.db_latency_ms > 100) issues.push(`High DB latency: ${service.db_latency_ms}ms`);
                        if (service.response_time_ms > 5000) issues.push(`Slow response: ${service.response_time_ms}ms`);
                        
                        if (issues.length > 0) {
                            alerts.push({
                                level: 'warning',
                                service: service.name,
                                message: issues.join(', '),
                                timestamp: service.last_check
                            });
                        }
                    }
                });
            }

            if (alerts.length === 0) {
                container.innerHTML = '<div class="service-loading">✅ No active service alerts</div>';
                return;
            }

            alerts.forEach(alert => {
                const alertDiv = document.createElement('div');
                alertDiv.className = `service-alert alert-${alert.level}`;
                
                alertDiv.innerHTML = `
                    <div class="alert-header">
                        <strong>${alert.service}</strong>
                        <span class="alert-level ${alert.level}">${alert.level}</span>
                    </div>
                    <div class="alert-message">${alert.message}</div>
                `;
                
                container.appendChild(alertDiv);
            });
        }

        // Show service error
        function showServiceError(errorMessage) {
            const container = document.getElementById('serviceHealthGrid');
            container.innerHTML = `
                <div class="service-error">
                    <h3>⚠️ Service Health Unavailable</h3>
                    <p>${errorMessage}</p>
                    <button onclick="loadServiceHealth()" style="margin-top: 10px; padding: 8px 16px; background: #F44336; color: white; border: none; border-radius: 4px; cursor: pointer;">
                        Retry
                    </button>
                </div>
            `;
            
            // Clear service stats
            document.getElementById('totalServices').textContent = '--';
            document.getElementById('healthyServices').textContent = '--';
            document.getElementById('warningServices').textContent = '--';
            document.getElementById('criticalServices').textContent = '--';
            document.getElementById('serviceAvailability').textContent = '--%';
            
            // Clear alerts
            document.getElementById('serviceAlerts').innerHTML = `
                <div class="service-loading">❌ Service alerts unavailable</div>
            `;
        }

        // Update service health view - DEPRECATED - redirecting to new function
        function updateServiceHealthView(data) {
            console.log('⚠️ updateServiceHealthView is deprecated, redirecting to updateServiceHealthCards');
            if (data && data.services) {
                updateServiceHealthCards(data.services);
            } else {
                updateServiceHealthCards(data);
            }
        }

        // Create service health card
        function createServiceHealthCard(serviceId, data) {
            console.log('🔧 createServiceHealthCard called with serviceId:', serviceId, 'data:', data);
            
            if (!data) {
                console.error('❌ createServiceHealthCard: data is undefined for serviceId:', serviceId);
                const errorCard = document.createElement('div');
                errorCard.className = 'service-card status-critical';
                errorCard.innerHTML = '<div class="service-header"><div class="service-name">Error: No Data</div></div>';
                return errorCard;
            }
            
            console.log('🔧 Service data status:', data.status);
            const card = document.createElement('div');
            
            // Map status to health_level 
            const healthLevel = data.status === 'ok' ? 'healthy' : 
                               data.status === 'warning' || data.status === 'timeout' ? 'warning' : 'critical';
            
            card.className = `service-card status-${healthLevel}`;
            
            const statusBadgeClass = healthLevel === 'healthy' ? 'healthy' : 
                                   healthLevel === 'warning' ? 'warning' : 'critical';
            
            card.innerHTML = `
                <div class="service-header">
                    <div class="service-name">${data.name || serviceId}</div>
                    <div class="service-status-badge ${statusBadgeClass}">${data.status || 'unknown'}</div>
                </div>
                <div class="service-metrics">
                    <div class="service-metric">
                        <div class="service-metric-value">${data.status === 'ok' ? 'Connected' : 'Disconnected'}</div>
                        <div class="service-metric-label">Connect</div>
                    </div>
                    <div class="service-metric">
                        <div class="service-metric-value">${data.status === 'ok' ? 'OK' : 'N/A'}</div>
                        <div class="service-metric-label">Database</div>
                    </div>
                    <div class="service-metric">
                        <div class="service-metric-value">${data.response_time ? Math.round(data.response_time) + 'ms' : 'N/A'}</div>
                        <div class="service-metric-label">Response Time</div>
                    </div>
                    <div class="service-metric">
                        <div class="service-metric-value">${data.status === 'ok' ? '99.9%' : '0%'}</div>
                        <div class="service-metric-label">Uptime</div>
                    </div>
                </div>
                ${createServiceEndpoints(data.sub_services || {})}
                ${data.error ? `<div class="service-error">⚠️ ${data.error}</div>` : ''}
            `;
            
            return card;
        }

        // Create service endpoints display
        function createServiceEndpoints(subServices) {
            if (!subServices || Object.keys(subServices).length === 0) {
                return '';
            }
            
            const endpointsHtml = Object.entries(subServices).map(([serviceName, serviceInfo]) => {
                const status = serviceInfo.status || 'unknown';
                const statusClass = status === 'ok' ? 'status-ok' : 'status-error';
                return `
                    <div class="service-endpoint">
                        <span class="endpoint-name">${serviceName}</span>
                        <span class="endpoint-status ${statusClass}">${status}</span>
                    </div>
                `;
            }).join('');
            
            return `<div class="service-endpoints">${endpointsHtml}</div>`;
        }

        // Update service alerts
        function updateServiceAlerts(services) {
            const alertsContainer = document.getElementById('serviceAlerts');
            const alerts = [];

            if (services) {
                Object.entries(services).forEach(([serviceId, serviceData]) => {
                    if (serviceData.health_level === 'critical') {
                        alerts.push({
                            level: 'critical',
                            service: serviceData.name || serviceId,
                            message: serviceData.error || 'Service is in critical state',
                            timestamp: serviceData.last_check
                        });
                    } else if (serviceData.health_level === 'warning') {
                        alerts.push({
                            level: 'warning',
                            service: serviceData.name || serviceId,
                            message: `High latency detected: DB ${serviceData.db_latency_ms}ms, Response ${serviceData.response_time_ms}ms`,
                            timestamp: serviceData.last_check
                        });
                    }
                });
            }

            if (alerts.length > 0) {
                alertsContainer.innerHTML = alerts.map(alert => `
                    <div class="service-alert ${alert.level}">
                        <div class="alert-level">${alert.level}</div>
                        <div class="alert-message">${alert.service}: ${alert.message}</div>
                        <div class="alert-timestamp">${new Date(alert.timestamp).toLocaleString()}</div>
                    </div>
                `).join('');
            } else {
                alertsContainer.innerHTML = '<div class="no-alerts">✅ No service alerts - All systems healthy</div>';
            }
        }

        // Show service health error
        function showServiceHealthError(message) {
            const serviceStats = document.getElementById('serviceStats');
            const serviceHealthGrid = document.getElementById('serviceHealthGrid');
            
            if (serviceStats) {
                serviceStats.innerHTML = `
                    <div class="service-loading">❌ Service health unavailable</div>
                `;
            }
            
            if (serviceHealthGrid) {
                serviceHealthGrid.innerHTML = `
                    <div class="service-loading">❌ ${message}</div>
                `;
            }
            
            const serviceAlerts = document.getElementById('serviceAlerts');
            if (serviceAlerts) {
                serviceAlerts.innerHTML = `
                    <div class="service-loading">❌ Service alerts unavailable</div>
                `;
            }
        }

        // Update dashboard with data
        function updateDashboard(data) {
            console.log('Updating dashboard with data:', data);
            
            try {
                // Update status cards with safety checks
                const totalElement = document.getElementById('totalVMs');
                const onlineElement = document.getElementById('onlineVMs');
                const offlineElement = document.getElementById('offlineVMs');
                const uptimeElement = document.getElementById('uptimePercentage');
                
                // Use data from API directly with fallbacks
                const total = data.total || (data.online || 0) + (data.offline || 0);
                const online = data.online || 0;
                const offline = data.offline || 0;
                const uptime = data.uptime_percentage || (total > 0 ? Math.round((online / total) * 100) : 0);
                
                if (totalElement) totalElement.textContent = total;
                if (onlineElement) onlineElement.textContent = online;
                if (offlineElement) offlineElement.textContent = offline;
                if (uptimeElement) uptimeElement.textContent = `${uptime}%`;

                // Update performance metrics
                const performance = data.performance || {};
                updateMetric('cpu', performance.cpu || 0);
                updateMetric('memory', performance.memory || 0);
                updateMetric('disk', performance.disk || 0);

                // Update alerts
                updateAlerts(data.alerts || []);

                console.log('Dashboard update completed successfully');
                
            } catch (error) {
                console.error('Error updating dashboard:', error);
            }

            // Update data source indicator
            updateDataSourceIndicator(data.data_source, data.system_status);

            // Update footer info
            const lastUpdated = new Date(data.last_updated || Date.now()).toLocaleString();
            document.getElementById('lastUpdated').textContent = `Last updated: ${lastUpdated}`;
            
            const cacheAge = data.cache_age_seconds || 0;
            document.getElementById('cacheInfo').textContent = 
                `Cache: ${cacheAge.toFixed(1)}s old | Source: ${data.data_source || 'unknown'} | API: ${data.api_version || '1.0'}`;
        }

        // Update trends statistics
        function updateTrendsData(trends) {
            if (!trends || !trends.summary_stats) return;
            
            const stats = trends.summary_stats;
            
            document.getElementById('avgCpu24h').textContent = `${stats.avg_cpu_24h || 0}%`;
            document.getElementById('maxCpu24h').textContent = `${stats.max_cpu_24h || 0}%`;
            document.getElementById('avgMemory24h').textContent = `${stats.avg_memory_24h || 0}%`;
            document.getElementById('uptime24h').textContent = `${stats.uptime_24h || 0}%`;
        }

        // Update performance metric
        function updateMetric(type, value) {
            const bar = document.getElementById(`${type}Bar`);
            const valueElement = document.getElementById(`${type}Value`);
            
            if (bar && valueElement) {
                bar.style.width = `${Math.min(value, 100)}%`;
                valueElement.textContent = `${value}%`;
                
                // Color based on value
                let color = '#4CAF50'; // Green
                if (value > 80) color = '#F44336'; // Red
                else if (value > 60) color = '#FF9800'; // Orange
                
                bar.style.background = color;
            }
        }

        // Update alerts section with Service Health data
        function updateAlerts(alerts) {
            // Show Service Health data in Alerts tab instead
            fetch('/api/services/health')
                .then(response => response.json())
                .then(serviceData => {
                    const alertsTab = document.getElementById('alerts-tab');
                    if (alertsTab) {
                        const carbonReceipt = serviceData.carbon_receipt || {};
                        const carbonFootprint = serviceData.carbon_footprint || {};
                        
                        alertsTab.innerHTML = `
                            <div class="section">
                                <h3>🛡️ Service Health Monitoring</h3>
                                <div class="service-overview">
                                    <div class="service-summary">
                                        <div class="summary-card">
                                            <h4>Service Status Overview</h4>
                                            <div class="status-indicators">
                                                <div class="indicator ${getStatusClass(carbonReceipt.status)}">
                                                    <span class="indicator-dot"></span>
                                                    Carbon Receipt: ${carbonReceipt.status || 'Unknown'}
                                                </div>
                                                <div class="indicator ${getStatusClass(carbonFootprint.status)}">
                                                    <span class="indicator-dot"></span>
                                                    Carbon Footprint: ${carbonFootprint.status || 'Unknown'}
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="service-cards-grid">
                                    <div class="service-card ${getStatusClass(carbonReceipt.status)}">
                                        <div class="service-header">
                                            <h4>📋 Carbon Receipt API</h4>
                                            <span class="status-badge ${carbonReceipt.status || 'unknown'}">${carbonReceipt.status || 'Unknown'}</span>
                                        </div>
                                        <div class="service-details">
                                            <div class="detail-row">
                                                <span class="detail-label">🌐 Endpoint:</span>
                                                <span class="detail-value">uat-carbonreceipt.one.th</span>
                                            </div>
                                            <div class="detail-row">
                                                <span class="detail-label">⏱️ Uptime:</span>
                                                <span class="detail-value">${carbonReceipt.uptime || 'N/A'}</span>
                                            </div>
                                            <div class="detail-row">
                                                <span class="detail-label">🗄️ Database:</span>
                                                <span class="detail-value">${carbonReceipt.database_status || 'N/A'}</span>
                                            </div>
                                            <div class="detail-row">
                                                <span class="detail-label">📡 Response Time:</span>
                                                <span class="detail-value">${carbonReceipt.response_time_ms || 0}ms</span>
                                            </div>
                                        </div>
                                        <div class="sub-services">
                                            <h5>🔧 Sub-Services:</h5>
                                            <div class="sub-service-list">
                                                ${Object.entries(carbonReceipt.sub_services || {}).map(([key, service]) => 
                                                    `<div class="sub-service-item ${getStatusClass(service)}">
                                                        <span class="sub-service-name">${key}:</span>
                                                        <span class="sub-service-status">${service.status || 'Unknown'}</span>
                                                    </div>`
                                                ).join('')}
                                            </div>
                                        </div>
                                    </div>
                                    
                                    <div class="service-card ${getStatusClass(carbonFootprint.status)}">
                                        <div class="service-header">
                                            <h4>🌍 Carbon Footprint API</h4>
                                            <span class="status-badge ${carbonFootprint.status || 'unknown'}">${carbonFootprint.status || 'Unknown'}</span>
                                        </div>
                                        <div class="service-details">
                                            <div class="detail-row">
                                                <span class="detail-label">🌐 Endpoint:</span>
                                                <span class="detail-value">uat-carbonfootprint.one.th</span>
                                            </div>
                                            <div class="detail-row">
                                                <span class="detail-label">⏱️ Uptime:</span>
                                                <span class="detail-value">${carbonFootprint.uptime || 'N/A'}</span>
                                            </div>
                                            <div class="detail-row">
                                                <span class="detail-label">🗄️ Database:</span>
                                                <span class="detail-value">${carbonFootprint.database_status || 'N/A'}</span>
                                            </div>
                                            <div class="detail-row">
                                                <span class="detail-label">📡 Response Time:</span>
                                                <span class="detail-value">${carbonFootprint.response_time_ms || 0}ms</span>
                                            </div>
                                        </div>
                                        <div class="sub-services">
                                            <h5>🔧 Sub-Services:</h5>
                                            <div class="sub-service-list">
                                                ${Object.entries(carbonFootprint.sub_services || {}).map(([key, service]) => 
                                                    `<div class="sub-service-item ${getStatusClass(service)}">
                                                        <span class="sub-service-name">${key}:</span>
                                                        <span class="sub-service-status">${service.status || 'Unknown'}</span>
                                                    </div>`
                                                ).join('')}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        `;
                    }
                })
                .catch(error => {
                    console.error('Error loading service health:', error);
                    const alertsTab = document.getElementById('alerts-tab');
                    if (alertsTab) {
                        alertsTab.innerHTML = `
                            <div class="section">
                                <h3>🛡️ Service Health Monitoring</h3>
                                <div class="error-message">
                                    <p>⚠️ Unable to load Service Health data</p>
                                    <p>Error: ${error.message}</p>
                                </div>
                            </div>
                        `;
                    }
                });
            return; // Skip original alerts logic
        }

        // Update data source indicator
        function updateDataSourceIndicator(source, status) {
            const indicator = document.getElementById('dataSourceIndicator');
            indicator.className = 'data-source-indicator';
            
            if (source === 'zabbix' && status === 'healthy') {
                indicator.textContent = 'Live Data';
                indicator.classList.add('data-source-zabbix');
            } else if (source === 'demo' || source === 'demo_fallback') {
                indicator.textContent = 'Demo Mode';
                indicator.classList.add('data-source-demo');
            } else {
                indicator.textContent = 'Error Mode';
                indicator.classList.add('data-source-error');
            }
        }

        // Update performance information
        function updatePerformanceInfo(loadTime, response) {
            const isCompressed = response.headers.get('content-encoding') === 'gzip';
            const contentLength = response.headers.get('content-length');
            
            let performanceText = `Load: ${loadTime.toFixed(2)}ms`;
            if (isCompressed) {
                performanceText += ` | Compressed: Yes`;
                document.getElementById('compressionIndicator').style.display = 'inline-block';
            } else {
                document.getElementById('compressionIndicator').style.display = 'none';
            }
            
            if (contentLength) {
                const sizeKB = (parseInt(contentLength) / 1024).toFixed(1);
                performanceText += ` | Size: ${sizeKB}KB`;
            }
            
            document.getElementById('performanceInfo').textContent = performanceText;
        }

        // Initialize and update charts
        function initializeCharts() {
            const isDark = document.body.classList.contains('dark-mode');
            const textColor = isDark ? '#ffffff' : '#333333';
            const gridColor = isDark ? '#444444' : '#e0e0e0';
            
            // Performance Chart
            const performanceCtx = document.getElementById('performanceChart').getContext('2d');
            performanceChart = new Chart(performanceCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [
                        {
                            label: 'CPU %',
                            data: [],
                            borderColor: '#FF6B6B',
                            backgroundColor: 'rgba(255, 107, 107, 0.1)',
                            tension: 0.4
                        },
                        {
                            label: 'Memory %',
                            data: [],
                            borderColor: '#4ECDC4',
                            backgroundColor: 'rgba(78, 205, 196, 0.1)',
                            tension: 0.4
                        },
                        {
                            label: 'Disk %',
                            data: [],
                            borderColor: '#45B7D1',
                            backgroundColor: 'rgba(69, 183, 209, 0.1)',
                            tension: 0.4
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            labels: {
                                color: textColor
                            }
                        }
                    },
                    scales: {
                        x: {
                            ticks: {
                                color: textColor
                            },
                            grid: {
                                color: gridColor
                            }
                        },
                        y: {
                            ticks: {
                                color: textColor
                            },
                            grid: {
                                color: gridColor
                            },
                            beginAtZero: true,
                            max: 100
                        }
                    }
                }
            });

            // VM Status Chart
            const statusCtx = document.getElementById('statusChart').getContext('2d');
            statusChart = new Chart(statusCtx, {
                type: 'bar',
                data: {
                    labels: [],
                    datasets: [
                        {
                            label: 'Online VMs',
                            data: [],
                            backgroundColor: 'rgba(76, 175, 80, 0.8)',
                            borderColor: '#4CAF50',
                            borderWidth: 1
                        },
                        {
                            label: 'Offline VMs',
                            data: [],
                            backgroundColor: 'rgba(244, 67, 54, 0.8)',
                            borderColor: '#F44336',
                            borderWidth: 1
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            labels: {
                                color: textColor
                            }
                        }
                    },
                    scales: {
                        x: {
                            ticks: {
                                color: textColor
                            },
                            grid: {
                                color: gridColor
                            },
                            stacked: true
                        },
                        y: {
                            ticks: {
                                color: textColor
                            },
                            grid: {
                                color: gridColor
                            },
                            stacked: true,
                            beginAtZero: true
                        }
                    }
                }
            });

            // Alerts Chart
            const alertsCtx = document.getElementById('alertsChart').getContext('2d');
            alertsChart = new Chart(alertsCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [
                        {
                            label: 'Active Alerts',
                            data: [],
                            borderColor: '#FF9800',
                            backgroundColor: 'rgba(255, 152, 0, 0.1)',
                            tension: 0.4,
                            fill: true
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            labels: {
                                color: textColor
                            }
                        }
                    },
                    scales: {
                        x: {
                            ticks: {
                                color: textColor
                            },
                            grid: {
                                color: gridColor
                            }
                        },
                        y: {
                            ticks: {
                                color: textColor
                            },
                            grid: {
                                color: gridColor
                            },
                            beginAtZero: true
                        }
                    }
                }
            });
        }

        // Update charts with trends data
        function updateChartsData(trends) {
            if (!trends || !performanceChart) return;

            // Update performance chart
            if (trends.performance_trends) {
                performanceChart.data.labels = trends.performance_trends.labels;
                performanceChart.data.datasets[0].data = trends.performance_trends.cpu_data;
                performanceChart.data.datasets[1].data = trends.performance_trends.memory_data;
                performanceChart.data.datasets[2].data = trends.performance_trends.disk_data;
                performanceChart.update();
            }

            // Update VM status chart
            if (trends.vm_status_trends) {
                statusChart.data.labels = trends.vm_status_trends.labels;
                statusChart.data.datasets[0].data = trends.vm_status_trends.online_data;
                statusChart.data.datasets[1].data = trends.vm_status_trends.offline_data;
                statusChart.update();
            }

            // Update alerts chart
            if (trends.alerts_trends) {
                alertsChart.data.labels = trends.alerts_trends.labels;
                alertsChart.data.datasets[0].data = trends.alerts_trends.alerts_data;
                alertsChart.update();
            }
        }

        // Update charts theme

        // Show error message
        function showError(message) {
            document.getElementById('loading').style.display = 'none';
            document.getElementById('dashboard').innerHTML = `
                <div class="error">
                    <h3>❌ Error Loading Dashboard</h3>
                    <p>${message}</p>
                    <button class="refresh-btn" onclick="loadDashboardData()">🔄 Retry</button>
                </div>
            `;
            document.getElementById('dashboard').style.display = 'block';
        }

        // Auto-refresh functionality
        function startAutoRefresh() {
            if (refreshInterval) clearInterval(refreshInterval);
            refreshInterval = setInterval(() => {
                loadDashboardData();
                // Update trends if on trends tab
                if (currentTab === 'trends') {
                    loadTrendsData();
                } else if (currentTab === 'services') {
                    loadServiceHealthData();
                }
            }, 30000); // Refresh every 30 seconds
        }

        function stopAutoRefresh() {
            if (refreshInterval) {
                clearInterval(refreshInterval);
                refreshInterval = null;
            }
        }

        // Keyboard shortcuts
        document.addEventListener('keydown', function(event) {
            // Ignore if user is typing in an input field
            if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA') {
                return;
            }

            switch(event.key.toLowerCase()) {
                case 'r':
                    event.preventDefault();
                    loadDashboardData();
                    if (currentTab === 'trends') {
                        loadTrendsData();
                    } else if (currentTab === 'services') {
                        loadServiceHealthData();
                    }
                    break;
                case 't':
                    event.preventDefault();
                    toggleTheme();
                    break;
                case '1':
                    event.preventDefault();
                    showTab('overview');
                    document.querySelectorAll('.tab')[0].click();
                    break;
                case '2':
                    event.preventDefault();
                    showTab('services');
                    document.querySelectorAll('.tab')[1].click();
                    break;
                case '3':
                    event.preventDefault();
                    showTab('trends');
                    document.querySelectorAll('.tab')[2].click();
                    break;
                case '4':
                    event.preventDefault();
                    showTab('alerts');
                    document.querySelectorAll('.tab')[3].click();
                    break;
                case '?':
                    event.preventDefault();
                    toggleShortcuts();
                    break;
            }
        });

        // Page visibility API for auto-refresh management
        document.addEventListener('visibilitychange', function() {
            if (document.hidden) {
                stopAutoRefresh();
            } else {
                startAutoRefresh();
                loadDashboardData(); // Refresh when page becomes visible
                if (currentTab === 'trends') {
                    loadTrendsData();
                }
            }
        });

        // Initialize dashboard
        document.addEventListener('DOMContentLoaded', function() {
            console.log('DOM loaded, initializing dashboard...');
            
            // Force hide loading after 2 seconds if still showing
            setTimeout(() => {
                const loading = document.getElementById('loading');
                const dashboard = document.getElementById('dashboard');
                if (loading && loading.style.display !== 'none') {
                    console.log('Force hiding loading screen...');
                    loading.style.display = 'none';
                    if (dashboard) {
                        dashboard.style.display = 'block';
                    }
                }
            }, 2000);
            
            loadDashboardData();
            
            // Initialize charts after a short delay to ensure DOM is ready
            setTimeout(() => {
                initializeCharts();
            }, 500);
            
            startAutoRefresh();
        });

        // Handle page unload
        window.addEventListener('beforeunload', function() {
            stopAutoRefresh();
        });

        // Handle tab clicks
        document.querySelectorAll('.tab').forEach((tab, index) => {
            tab.addEventListener('click', function() {
                const tabNames = ['overview', 'trends', 'alerts'];
                showTab(tabNames[index]);
            });
        });
        // Force initialization fallback
        function forceInitializeDashboard() {
            console.log('🔧 Force initializing dashboard...');
            
            // Hide loading, show dashboard
            const loading = document.getElementById('loading');
            const dashboard = document.getElementById('dashboard');
            
            if (loading) {
                loading.style.display = 'none';
                console.log('✅ Loading hidden');
            }
            if (dashboard) {
                dashboard.style.display = 'block';
                console.log('✅ Dashboard shown');
            }
            
            // Load data immediately
            loadDashboardData().then(() => {
                console.log('✅ Data loaded successfully');
            }).catch(error => {
                console.error('❌ Force load failed:', error);
                // Set fallback data
                const elements = {
                    'totalVMs': '34',
                    'onlineVMs': '34', 
                    'offlineVMs': '0',
                    'uptimePercentage': '100%'
                };
                
                Object.entries(elements).forEach(([id, value]) => {
                    const el = document.getElementById(id);
                    if (el) el.textContent = value;
                });
            });
        }

        // Auto-run force init after 5 seconds if still loading
        setTimeout(() => {
            const loading = document.getElementById('loading');
            if (loading && loading.style.display !== 'none') {
                console.log('⚠️ Dashboard still loading after 5s, force initializing...');
                forceInitializeDashboard();
            }
        }, 5000);

        // Make available globally
        window.forceInit = forceInitializeDashboard;
        
    </script>
</body>
</html>'''
    
    # สร้าง response พร้อม anti-cache headers
    response = make_response(html)
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    response.headers['Last-Modified'] = time.strftime('%a, %d %b %Y %H:%M:%S GMT')
    response.headers['ETag'] = f'"{int(time.time())}"'
    return response

@app.route('/debug-test')
def debug_test():
    """Debug test page"""
    try:
        with open('debug_test.html', 'r') as f:
            return f.read()
    except FileNotFoundError:
        return '<h1>Debug test file not found</h1>'

# Carbon Services Monitoring Integration
try:
    from carbon_service_monitor import get_carbon_service_data_sync, get_carbon_service_summary, get_carbon_service_logs, cleanup_carbon_monitor
    CARBON_SERVICES_AVAILABLE = True
    print("✅ Carbon services monitoring loaded successfully")
except ImportError as e:
    print(f"⚠️ Carbon services monitoring not available: {e}")
    CARBON_SERVICES_AVAILABLE = False

@app.route('/Services')
def services_dashboard():
    """Carbon Services Monitoring Dashboard"""
    try:
        with open('templates/carbon_service_dashboard.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return '''
        <html><head><title>Error</title></head><body>
        <h1>❌ Carbon Services Dashboard Template Not Found</h1>
        <p>Please ensure templates/carbon_service_dashboard.html exists</p>
        <a href="/">← Back to Dashboard</a>
        </body></html>
        ''', 404

@app.route('/api/services/health')
@gzip_response
def api_carbon_services_health():
    """API endpoint for carbon services health data"""
    try:
        carbon_data = get_carbon_services_sync()
        return jsonify(carbon_data['services'])
    except Exception as e:
        return jsonify({
            'error': f'Error fetching carbon services data: {str(e)}',
            'carbon_receipt': {
                'name': 'Carbon Receipt API',
                'status': 'error',
                'error_message': str(e)
            },
            'carbon_footprint': {
                'name': 'Carbon Footprint API',
                'status': 'error', 
                'error_message': str(e)
            }
        }), 500

@app.route('/api/services/summary')
@gzip_response
def api_carbon_services_summary():
    """API endpoint for carbon services summary metrics"""
    try:
        carbon_data = get_carbon_services_sync()
        return jsonify(carbon_data['summary'])
    except Exception as e:
        return jsonify({
            'error': f'Error fetching services summary: {str(e)}',
            'total_services': 0,
            'healthy_services': 0,
            'warning_services': 0,
            'error_services': 0,
            'availability_percentage': 0,
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'success_rate': 0,
            'avg_response_time': 0,
            'last_updated': None
        }), 500

@app.route('/api/services/logs')
@gzip_response
def api_carbon_services_logs():
    """API endpoint for carbon services logs"""
    try:
        level_filter = request.args.get('level', '')
        service_filter = request.args.get('service', '')
        limit = int(request.args.get('limit', 50))
        
        carbon_data = get_carbon_services_sync()
        logs = carbon_data.get('logs', [])
        
        # Apply filters
        if level_filter:
            logs = [log for log in logs if log['level'] == level_filter]
        if service_filter:
            logs = [log for log in logs if service_filter in log['service']]
            
        # Apply limit
        logs = logs[:limit]
        
        return jsonify(logs)
        
    except Exception as e:
        return jsonify([{
            'timestamp': datetime.now().isoformat(),
            'level': 'ERROR',
            'service': 'system',
            'message': f'Error fetching logs: {str(e)}',
            'details': {'error': str(e)}
        }]), 500

@app.route('/status')
def status():
    """Health check with enhanced info"""
    return jsonify({
        'status': 'ok',
        'service': 'VM Mobile Dashboard API v2.0 - Enhanced + Carbon Services',
        'timestamp': datetime.now().isoformat(),
        'version': '2.0.1-carbon-services',
        'features': [
            'Zabbix Integration' if ZABBIX_AVAILABLE else 'Demo Mode',
            'Alert System' if ALERTS_AVAILABLE else 'Basic Alerts',
            'Carbon Services Monitoring' if CARBON_SERVICES_AVAILABLE else 'Carbon Services Unavailable',
            'Historical Trends Charts',
            'Gzip Compression',
            'Smart Caching',
            'Performance Analytics',
            'Real-time Updates'
        ],
        'performance': {
            'compression_enabled': True,
            'cache_duration': cache['cache_duration'],
            'historical_data_points': len(cache['historical_data']) if cache['historical_data'] else 0,
            'api_version': '2.0'
        },
        'modules': {
            'zabbix': ZABBIX_AVAILABLE,
            'alerts': ALERTS_AVAILABLE,
            'carbon_services': CARBON_SERVICES_AVAILABLE,
            'gzip_compression': True,
            'chart_js': True
        }
    })

if __name__ == '__main__':
    print("🚀 Starting Enhanced VM Mobile Dashboard API v2.0 + Carbon Services...")
    print("🆕 New Features:")
    print("   📈 Historical Trends Charts (24-hour data)")
    print("   🗜️ Gzip Compression (up to 70% size reduction)")
    print("   📊 Performance Analytics & Statistics")
    print("   ⚡ Optimized Caching System")
    print("   🎛️ Tabbed Interface (Overview/Trends/Alerts)")
    print("   🌱 Carbon Services Monitoring Dashboard")
    print("")
    print("📱 Enhanced Mobile Dashboard: http://localhost:5000/mobile")
    print("🌱 Carbon Services Dashboard: http://localhost:5000/Services")
    print("🔌 Compressed API Endpoint: http://localhost:5000/api/dashboard")
    print("📈 Trends Data API: http://localhost:5000/api/trends")
    print("🌱 Carbon Services API: http://localhost:5000/api/services/health")
    print("💚 Health Check: http://localhost:5000/status")
    print("🔧 Debug Info: http://localhost:5000/debug")
    print("")
    print("✨ Performance Features:")
    print(f"   📊 Zabbix Integration: {'✅ Available' if ZABBIX_AVAILABLE else '❌ Not Available'}")
    print(f"   🚨 Alert System: {'✅ Available' if ALERTS_AVAILABLE else '❌ Not Available'}")
    print(f"   🌱 Carbon Services: {'✅ Available' if CARBON_SERVICES_AVAILABLE else '❌ Not Available'}")
    print("   🗜️ Gzip Compression: ✅ Enabled")
    print("   📈 Chart.js Integration: ✅ Enabled")
    print("   🔄 Smart Caching: ✅ 30s dashboard + 5m trends")
    print("   ⌨️ Keyboard Shortcuts: ✅ R, T, 1-3, ?")
    print("")
    app.run(host='0.0.0.0', port=5000, debug=True)