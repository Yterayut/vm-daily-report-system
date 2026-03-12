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
            # 🌍 Carbon Footprint - INFRA UAT (Main Service)
            'carbon_footprint_uat': {
                'name': 'Carbon Footprint',
                'url': 'https://uat-carbonfootprint.one.th/api/v2/health',
                'status': 'unknown',
                'response_time': 0,
                'last_check': None,
                'error_count': 0,
                'sub_services': {},
                'environment': 'uat',
                'service_type': 'carbon_footprint',
                'is_main': True
            },

            # 🌍 Carbon Footprint - INFRA PRD (Main Service)
            'carbon_footprint_prd': {
                'name': 'Carbon Footprint',
                'url': 'https://carbonfootprint.one.th/api/v2/health',
                'status': 'unknown',
                'response_time': 0,
                'last_check': None,
                'error_count': 0,
                'sub_services': {},
                'environment': 'prd',
                'service_type': 'carbon_footprint',
                'is_main': True
            },

            # 🌱 Carbon Receipt - INFRA UAT (Main Service)
            'carbon_receipt_uat': {
                'name': 'Carbon Receipt',
                'url': 'https://uat-carbonreceipt.one.th/api/v1/health',
                'status': 'unknown',
                'response_time': 0,
                'last_check': None,
                'error_count': 0,
                'sub_services': {},
                'environment': 'uat',
                'service_type': 'carbon_receipt',
                'is_main': True
            },

            # 🌱 Carbon Receipt - INFRA PRD (Main Service)
            'carbon_receipt_prd': {
                'name': 'Carbon Receipt',
                'url': 'https://carbonreceipt.one.th/api/v1/health',
                'status': 'unknown',
                'response_time': 0,
                'last_check': None,
                'error_count': 0,
                'sub_services': {},
                'environment': 'prd',
                'service_type': 'carbon_receipt',
                'is_main': True
            },

            # 🖥️ Mobile Dashboard (Main Service)
            'mobile_dashboard': {
                'name': 'Mobile Dashboard',
                'url': 'http://192.168.20.10:5000/status',
                'status': 'unknown',
                'response_time': 0,
                'last_check': None,
                'error_count': 0,
                'sub_services': {},
                'environment': 'prd',
                'service_type': 'dashboard',
                'is_main': True
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
                    content_type = response.headers.get('Content-Type', '')
                    raw_text = await response.text()
                    data = {}

                    # Support both JSON health endpoints and HTML pages (e.g. /mobile)
                    if 'application/json' in content_type:
                        try:
                            data = json.loads(raw_text)
                        except json.JSONDecodeError:
                            data = {}
                    else:
                        try:
                            data = json.loads(raw_text)
                        except json.JSONDecodeError:
                            data = {}
                    
                    # Update service status
                    if data:
                        service['status'] = 'ok' if response.status == 200 and data.get('status') == 'ok' else 'error'
                    else:
                        service['status'] = 'ok' if response.status == 200 else 'error'
                    service['response_time'] = round(response_time, 1)
                    service['last_check'] = datetime.now().isoformat()
                    service['error_count'] = 0 if service['status'] == 'ok' else service['error_count'] + 1

                    # Store main service metadata (database, uptime, db_latency)
                    service['database'] = data.get('database', 'unknown')
                    service['uptime'] = data.get('uptime', 'unknown')
                    service['db_latency_ms'] = data.get('db_latency_ms', 0)

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
                        'etax_api': 'etax_api_status',      # Fixed: was 'etax_status'
                        'one_api': 'one_api_status',        # Fixed: was 'one_status'
                        'one_box_api': 'one_box_api_status', # Fixed: was 'one_box_status'
                        'vekin_api': 'vekin_api_status'     # Fixed: was 'vekin_status'
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
                return future.result(timeout=60)  # 60s for slow UAT APIs (20-30s response time)
        except RuntimeError:
            # No running loop, safe to create new one
            return asyncio.run(check_all_carbon_services())
    except Exception as e:
        print(f"❌ Error in carbon services sync wrapper: {e}")
        import traceback
        traceback.print_exc()
        # Return minimal error data - no fallback
        raise

async def check_all_carbon_services():
    """Check all carbon services asynchronously and organize by groups"""
    tasks = []
    for service_key in carbon_monitor.services.keys():
        tasks.append(carbon_monitor.check_service_health(service_key))

    try:
        await asyncio.gather(*tasks, return_exceptions=True)
    except Exception as e:
        carbon_monitor.add_log('ERROR', 'system', f"Failed to check services: {str(e)}")

    # Organize services into 4 groups with sub-services
    groups = {
        'carbon_footprint_uat': {
            'title': 'Carbon Footprint - INFRA UAT',
            'icon': '🌍',
            'main_service': None,
            'sub_services': []
        },
        'carbon_footprint_prd': {
            'title': 'Carbon Footprint - INFRA PRD',
            'icon': '🌍',
            'main_service': None,
            'sub_services': []
        },
        'carbon_receipt_uat': {
            'title': 'Carbon Receipt - INFRA UAT',
            'icon': '🌱',
            'main_service': None,
            'sub_services': []
        },
        'carbon_receipt_prd': {
            'title': 'Carbon Receipt - INFRA PRD',
            'icon': '🌱',
            'main_service': None,
            'sub_services': []
        },
        'mobile_dashboard': {
            'title': 'Mobile Dashboard - PRD',
            'icon': '🖥️',
            'main_service': None,
            'sub_services': []
        }
    }

    # Process each service and assign to groups
    for service_key, service_data in carbon_monitor.services.items():
        if service_key == 'carbon_footprint_uat':
            groups['carbon_footprint_uat']['main_service'] = service_data
            # Add sub-services from API response
            if service_data.get('sub_services'):
                for sub_name, sub_data in service_data['sub_services'].items():
                    groups['carbon_footprint_uat']['sub_services'].append({
                        'name': sub_name,
                        'status': sub_data.get('status', 'unknown'),
                        'key': sub_name.lower().replace(' ', '_')
                    })

        elif service_key == 'carbon_footprint_prd':
            groups['carbon_footprint_prd']['main_service'] = service_data
            # Add sub-services from API response
            if service_data.get('sub_services'):
                for sub_name, sub_data in service_data['sub_services'].items():
                    groups['carbon_footprint_prd']['sub_services'].append({
                        'name': sub_name,
                        'status': sub_data.get('status', 'unknown'),
                        'key': sub_name.lower().replace(' ', '_')
                    })

        elif service_key == 'carbon_receipt_uat':
            groups['carbon_receipt_uat']['main_service'] = service_data
            # Add sub-services from API response (including Etax API)
            if service_data.get('sub_services'):
                for sub_name, sub_data in service_data['sub_services'].items():
                    # Rename Etax Api Status -> E-Tax Software
                    display_name = 'E-Tax Software' if 'etax' in sub_name.lower() else sub_name
                    groups['carbon_receipt_uat']['sub_services'].append({
                        'name': display_name,
                        'status': sub_data.get('status', 'unknown'),
                        'key': sub_name.lower().replace(' ', '_')
                    })

        elif service_key == 'carbon_receipt_prd':
            groups['carbon_receipt_prd']['main_service'] = service_data
            # Add sub-services from API response (including Etax API)
            if service_data.get('sub_services'):
                for sub_name, sub_data in service_data['sub_services'].items():
                    # Rename Etax Api Status -> E-Tax Software
                    display_name = 'E-Tax Software' if 'etax' in sub_name.lower() else sub_name
                    groups['carbon_receipt_prd']['sub_services'].append({
                        'name': display_name,
                        'status': sub_data.get('status', 'unknown'),
                        'key': sub_name.lower().replace(' ', '_')
                    })

        elif service_key == 'mobile_dashboard':
            groups['mobile_dashboard']['main_service'] = service_data

    return {
        'groups': groups,
        'summary': carbon_monitor.get_summary(),
        'logs': carbon_monitor.logs[:10],
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
    """Enhanced mobile dashboard v2.1 with Carbon Services"""
    from flask import render_template, make_response
    import time

    # Use template file instead of hardcoded HTML
    response = make_response(render_template('enhanced_mobile_dashboard.html'))

    # Anti-cache headers to force browser reload
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
        return jsonify(carbon_data)  # Return full object with services, summary, logs
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
