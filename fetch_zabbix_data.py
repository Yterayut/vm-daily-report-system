#!/usr/bin/env python3
"""
Enhanced Zabbix Data Fetcher - FIXED VERSION with Correct CPU Keys
Advanced monitoring with comprehensive metrics and error handling
Fixed based on actual Zabbix key analysis: system.cpu.util (working) vs system.cpu.util[] (not found)
"""

import os
import ssl
import matplotlib.pyplot as plt
import numpy as np
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from pyzabbix import ZabbixAPI, ZabbixAPIException
from pathlib import Path

# Load environment variables
try:
    from load_env import load_env_file, get_config_dict
    load_env_file()
    config = get_config_dict()
except ImportError:
    config = {
        'zabbix': {
            'url': os.getenv('ZABBIX_URL', 'http://localhost/zabbix/api_jsonrpc.php'),
            'user': os.getenv('ZABBIX_USER', 'Admin'),
            'password': os.getenv('ZABBIX_PASS', 'zabbix'),
            'timeout': int(os.getenv('ZABBIX_TIMEOUT', '30')),
            'verify_ssl': os.getenv('ZABBIX_VERIFY_SSL', 'false').lower() == 'true'
        }
    }

# Safe logger setup
logger = None

def get_logger():
    """Get logger instance safely"""
    global logger
    if logger is None:
        try:
            import logging
            logger = logging.getLogger(__name__)
        except:
            logger = None
    return logger

def safe_log_info(message):
    """Safe logging info"""
    try:
        log = get_logger()
        if log:
            log.info(message)
        else:
            print(f"INFO: {message}")
    except:
        print(f"INFO: {message}")

def safe_log_error(message):
    """Safe logging error"""
    try:
        log = get_logger()
        if log:
            log.error(message)
        else:
            print(f"ERROR: {message}")
    except:
        print(f"ERROR: {message}")

class EnhancedZabbixClient:
    """Enhanced Zabbix client with advanced monitoring capabilities"""
    
    def __init__(self):
        self.zapi = None
        self.config = config['zabbix']
        self.connection_established = False
        self.last_error = None
        
        # FIXED metric definitions based on actual Zabbix key analysis
        self.metric_definitions = {
            'cpu': {
                'keys': [
                    # PRIMARY: Keys confirmed working from analysis
                    'system.cpu.util',               # ✅ CONFIRMED WORKING - Primary key
                    'system.cpu.util[,user]',        # ✅ CONFIRMED WORKING - User CPU
                    'system.cpu.util[,system]',      # ✅ CONFIRMED WORKING - System CPU
                    'system.cpu.util[,idle]',        # Idle CPU time
                    'system.cpu.util[,iowait]',      # I/O wait time
                    
                    # SECONDARY: Alternative formats (may work on different systems)
                    'system.cpu.utilization',        # Alternative name
                    'cpu.util',                      # Short format
                    'proc.cpu.util',                 # Process CPU
                    
                    # LOAD AVERAGE: Different approach
                    'system.cpu.load[,avg1]',        # 1-minute load
                    'system.cpu.load[,avg5]',        # 5-minute load
                    'system.cpu.load[percpu,avg1]',  # Per-CPU load
                    
                    # PLATFORM SPECIFIC: For different OS
                    'perf_counter[\\Processor(_Total)\\% Processor Time]',  # Windows
                    'vmware.hv.cpu.usage',           # VMware
                    'vm.vmware.hv.cpu.usage',        # VMware VMs
                    
                    # FALLBACK: Last resort keys
                    'cpu.usage',
                    'cpu.percent',
                    'system.cpu.usage.percent'
                ],
                'name': 'CPU Usage',
                'unit': '%',
                'threshold_warning': 70,
                'threshold_critical': 85
            },
            'memory': {
                'keys': [
                    # Memory utilization keys (similar analysis pattern)
                    'vm.memory.util',
                    'vm.memory.utilization',
                    'memory.util',
                    'memory.usage.percent',
                    'system.memory.util',
                    'vm.vmware.hv.memory.usage',
                    
                    # Alternative memory keys
                    'vm.memory.utilization',
                    'memory.util',
                    'proc.memory.util'
                ],
                'name': 'Memory Usage',
                'unit': '%',
                'threshold_warning': 75,
                'threshold_critical': 90
            },
            'disk': {
                'keys': [
                    # CORRECT keys based on debug results for Zabbix 7.0.12
                    'vfs.fs.dependent.size[/,pused]',        # Primary key for root filesystem
                    'vfs.fs.dependent.size[/home,pused]',    # Home partition
                    'vfs.fs.dependent.size[/var,pused]',     # Var partition
                    'vfs.fs.dependent.size[/opt,pused]',     # Opt partition
                    'vfs.fs.dependent.size[/boot,pused]',    # Boot partition
                    'vfs.fs.dependent.size[/tmp,pused]',     # Tmp partition
                    'vfs.fs.dependent.size[/usr,pused]',     # Usr partition
                    
                    # Windows partitions
                    'vfs.fs.dependent.size[C:,pused]',       # Windows C drive
                    'vfs.fs.dependent.size[D:,pused]',       # Windows D drive
                    
                    # Fallback patterns
                    'vfs.fs.dependent[/,pused]',
                    'vfs.fs.size[/,pused]',
                    'vfs.fs.pused[/]'
                ],
                'name': 'Disk Usage',
                'unit': '%',
                'threshold_warning': 80,
                'threshold_critical': 90
            }
        }
    
    def connect(self) -> bool:
        """Enhanced connection with proper ZabbixAPI initialization"""
        try:
            if self.connection_established and self.zapi:
                # Test existing connection
                try:
                    self.zapi.api_version()
                    return True
                except:
                    self.connection_established = False
            
            safe_log_info(f"🔌 Connecting to Zabbix: {self.config['url']}")
            
            # Create API connection with correct parameters
            self.zapi = ZabbixAPI(self.config['url'])
            
            # Login
            self.zapi.login(
                user=self.config['user'],
                password=self.config['password']
            )
            
            # Verify connection
            api_version = self.zapi.api_version()
            safe_log_info(f"✅ Connected to Zabbix API v{api_version}")
            self.connection_established = True
            self.last_error = None
            return True
            
        except Exception as e:
            self.last_error = f"Connection error: {e}"
            safe_log_error(f"❌ {self.last_error}")
            return False
    
    def disconnect(self):
        """Properly disconnect from Zabbix"""
        if self.zapi and self.connection_established:
            try:
                self.zapi.user.logout()
                safe_log_info("👋 Disconnected from Zabbix")
            except:
                pass
            finally:
                self.zapi = None
                self.connection_established = False
    
    def fetch_hosts(self) -> List[Dict[str, Any]]:
        """Fetch all monitored hosts with enhanced filtering"""
        if not self.connect():
            return []
        
        try:
            # Get hosts with detailed information
            hosts = self.zapi.host.get(
                output=['hostid', 'name', 'host', 'status', 'available'],
                selectInterfaces=['ip', 'dns', 'port'],
                selectGroups=['name'],
                filter={'status': 0}  # Only enabled hosts
            )
            
            vm_hosts = []
            for host in hosts:
                host_data = {
                    'hostid': host['hostid'],
                    'name': host['name'],
                    'hostname': host['host'],
                    'status': int(host.get('status', 1)),
                    'available': int(host.get('available', 0)),
                    'groups': [group['name'] for group in host.get('groups', [])],
                    'interfaces': host.get('interfaces', [])
                }
                
                # Get primary IP address
                primary_ip = 'N/A'
                for interface in host_data['interfaces']:
                    if interface.get('ip'):
                        primary_ip = interface['ip']
                        break
                
                host_data['ip'] = primary_ip
                vm_hosts.append(host_data)
            
            safe_log_info(f"📊 Fetched {len(vm_hosts)} hosts from Zabbix")
            return vm_hosts
            
        except Exception as e:
            safe_log_error(f"❌ Error fetching hosts: {e}")
            return []
    
    def get_item_value(self, hostid: str, metric_type: str) -> float:
        """ENHANCED item value retrieval with improved CPU key logic"""
        if not self.connection_established:
            return 0.0
        
        metric_config = self.metric_definitions.get(metric_type, {})
        item_keys = metric_config.get('keys', [])
        
        # Special handling for disk metrics with exact key matching
        if metric_type == 'disk':
            return self._get_disk_usage_exact(hostid)
        
        # ENHANCED CPU and Memory retrieval with better validation
        logger.debug(f"🔍 Getting {metric_type} for host {hostid}")
        
        for key in item_keys:
            try:
                # Try exact match first
                items = self.zapi.item.get(
                    hostids=hostid,
                    filter={'key_': key},  # Exact match
                    output=['lastvalue', 'lastclock', 'key_', 'name'],
                    limit=1
                )
                
                # If no exact match, try search for partial match
                if not items:
                    items = self.zapi.item.get(
                        hostids=hostid,
                        search={'key_': key},
                        output=['lastvalue', 'lastclock', 'key_', 'name'],
                        limit=3
                    )
                
                for item in items:
                    if item.get('lastvalue') is not None:
                        try:
                            value = float(item['lastvalue'])
                            
                            # Enhanced validation for CPU/Memory
                            if metric_type in ['cpu', 'memory']:
                                # Accept reasonable percentage values (0-100%)
                                if 0 <= value <= 100:
                                    # Check if data is recent (within last 10 minutes)
                                    last_clock = int(item.get('lastclock', 0))
                                    current_time = int(time.time())
                                    data_age = current_time - last_clock
                                    
                                    logger.debug(f"✅ Found {metric_type}: {item['key_']} = {value}% (age: {data_age}s)")
                                    
                                    # Prefer recent data, but accept older data if it's the only option
                                    if data_age < 600:  # 10 minutes
                                        return value
                                    elif data_age < 3600:  # 1 hour - still acceptable
                                        logger.debug(f"⚠️ Using older data: {data_age}s old")
                                        return value
                                    else:
                                        logger.debug(f"❌ Data too old: {data_age}s")
                                        continue
                                else:
                                    logger.debug(f"❌ Value out of range: {value}% for {item['key_']}")
                                    continue
                            else:
                                # For other metrics, return any valid numeric value
                                if value >= 0:
                                    logger.debug(f"✅ Found {metric_type}: {item['key_']} = {value}")
                                    return value
                                    
                        except (ValueError, TypeError) as e:
                            logger.debug(f"❌ Invalid value for {item['key_']}: {item.get('lastvalue')} - {e}")
                            continue
                    else:
                        logger.debug(f"❌ No lastvalue for {key}")
                        
            except Exception as e:
                logger.debug(f"❌ Error getting {key} for host {hostid}: {e}")
                continue
        
        # FALLBACK: If no specific keys work, try to find ANY matching items
        if metric_type == 'cpu':
            try:
                logger.debug(f"🔍 Fallback: searching for any CPU items for host {hostid}")
                fallback_items = self.zapi.item.get(
                    hostids=hostid,
                    search={'key_': 'cpu'},
                    output=['lastvalue', 'lastclock', 'key_', 'name'],
                    filter={'status': 0}  # Only enabled items
                )
                
                for item in fallback_items:
                    if item.get('lastvalue'):
                        try:
                            value = float(item['lastvalue'])
                            if 0 <= value <= 100:
                                logger.debug(f"🆘 Fallback CPU found: {item['key_']} = {value}%")
                                return value
                        except:
                            continue
                            
            except Exception as e:
                logger.debug(f"❌ Fallback search failed for host {hostid}: {e}")
        
        logger.debug(f"❌ No valid {metric_type} data found for host {hostid}")
        return 0.0
    
    def _get_disk_usage_exact(self, hostid: str) -> float:
        """Get disk usage using exact key matching for Zabbix 7.0.12"""
        try:
            # Try exact matches for common filesystem paths
            exact_keys = [
                'vfs.fs.dependent.size[/,pused]',        # Root filesystem - highest priority
                'vfs.fs.dependent.size[/home,pused]',    # Home partition
                'vfs.fs.dependent.size[/var,pused]',     # Var partition
                'vfs.fs.dependent.size[/opt,pused]',     # Opt partition
                'vfs.fs.dependent.size[/boot,pused]',    # Boot partition
                'vfs.fs.dependent.size[C:,pused]',       # Windows C drive
                'vfs.fs.dependent.size[D:,pused]'        # Windows D drive
            ]
            
            disk_values = []
            found_keys = []
            
            for key in exact_keys:
                try:
                    items = self.zapi.item.get(
                        hostids=hostid,
                        filter={'key_': key},  # Exact match
                        output=['lastvalue', 'key_']
                    )
                    
                    if items and items[0].get('lastvalue') is not None:
                        value = float(items[0]['lastvalue'])
                        if 0 <= value <= 100:
                            disk_values.append(value)
                            found_keys.append(key)
                            logger.debug(f"Found exact disk usage: {key} = {value}%")
                
                except (ValueError, TypeError, Exception) as e:
                    logger.debug(f"Error with key {key}: {e}")
                    continue
            
            if disk_values:
                # Prioritize root filesystem, otherwise return the highest usage
                if found_keys:
                    # Check if we have root filesystem
                    root_indices = [i for i, key in enumerate(found_keys) if key.endswith('[/,pused]')]
                    if root_indices:
                        root_usage = disk_values[root_indices[0]]
                        logger.debug(f"Host {hostid} root filesystem usage: {root_usage}%")
                        return root_usage
                
                # Return the highest disk usage (most critical)
                max_usage = max(disk_values)
                logger.debug(f"Host {hostid} max disk usage: {max_usage}%")
                return max_usage
            
            # Fallback: search for any vfs.fs.dependent items with pused
            logger.debug(f"No exact matches found for host {hostid}, trying search...")
            items = self.zapi.item.get(
                hostids=hostid,
                search={'key_': 'vfs.fs.dependent'},
                output=['lastvalue', 'key_']
            )
            
            for item in items:
                key = item.get('key_', '')
                if 'pused' in key and item.get('lastvalue') is not None:
                    try:
                        value = float(item['lastvalue'])
                        if 0 <= value <= 100:
                            logger.debug(f"Found fallback disk usage: {key} = {value}%")
                            return value
                    except (ValueError, TypeError):
                        continue
            
            logger.debug(f"No disk usage items found for host {hostid}")
            return 0.0
            
        except Exception as e:
            logger.debug(f"Error getting disk usage for host {hostid}: {e}")
            return 0.0
    
    def enrich_host_data(self, hosts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enrich host data with comprehensive metrics"""
        if not hosts:
            return []
        
        safe_log_info(f"🔍 Enriching data for {len(hosts)} hosts...")
        
        enriched_hosts = []
        for i, host in enumerate(hosts):
            try:
                host_name = host.get('name', 'Unknown')
                host_id = host.get('hostid', 'Unknown')
                
                logger.debug(f"🔍 Processing host {i+1}/{len(hosts)}: {host_name} (ID: {host_id})")
                
                # Get current metrics with enhanced logging
                host['cpu_load'] = self.get_item_value(host['hostid'], 'cpu')
                host['memory_used'] = self.get_item_value(host['hostid'], 'memory')
                host['disk_used'] = self.get_item_value(host['hostid'], 'disk')
                
                # Determine online status
                host['is_online'] = self._determine_online_status(host)
                
                # Calculate health score
                host['health_score'] = self._calculate_health_score(host)
                
                # Get performance rating
                host['performance_rating'] = self._get_performance_rating(host)
                
                # Add alert status
                host['alert_status'] = self._get_alert_status(host)
                
                # Enhanced logging for metrics
                safe_log_info(f"📊 Host {host_name}: "
                           f"CPU={host['cpu_load']:.1f}%, "
                           f"Memory={host['memory_used']:.1f}%, "
                           f"Disk={host['disk_used']:.1f}%, "
                           f"Health={host['health_score']}, "
                           f"Status={'Online' if host['is_online'] else 'Offline'}")
                
                enriched_hosts.append(host)
                
            except Exception as e:
                logger.warning(f"⚠️ Error enriching host {host.get('name', 'unknown')}: {e}")
                # Add with defaults
                for key in ['cpu_load', 'memory_used', 'disk_used']:
                    host.setdefault(key, 0.0)
                host['is_online'] = False
                host['health_score'] = 0
                host['performance_rating'] = 'Unknown'
                host['alert_status'] = 'error'
                enriched_hosts.append(host)
        
        safe_log_info(f"✅ Data enrichment completed for {len(enriched_hosts)} hosts")
        return enriched_hosts
    
    def _determine_online_status(self, host: Dict[str, Any]) -> bool:
        """Enhanced online status determination"""
        # Check Zabbix availability status
        if host.get('available') == 1:
            return True
        
        # Check if we have recent metric data
        has_recent_data = any([
            host.get('cpu_load', 0) > 0,
            host.get('memory_used', 0) > 0,
            host.get('disk_used', 0) > 0
        ])
        
        return has_recent_data and host.get('status') == 0
    
    def _calculate_health_score(self, host: Dict[str, Any]) -> int:
        """Calculate overall health score (0-100)"""
        if not host.get('is_online', False):
            return 0
        
        score = 100
        
        # CPU impact
        cpu = host.get('cpu_load', 0)
        if cpu > 85:
            score -= 30
        elif cpu > 70:
            score -= 15
        
        # Memory impact
        memory = host.get('memory_used', 0)
        if memory > 90:
            score -= 25
        elif memory > 75:
            score -= 10
        
        # Disk impact
        disk = host.get('disk_used', 0)
        if disk > 90:
            score -= 20
        elif disk > 80:
            score -= 8
        
        return max(0, score)
    
    def _get_performance_rating(self, host: Dict[str, Any]) -> str:
        """Get performance rating based on metrics"""
        if not host.get('is_online', False):
            return 'Offline'
        
        health_score = host.get('health_score', 0)
        
        if health_score >= 90:
            return 'Excellent'
        elif health_score >= 75:
            return 'Good'
        elif health_score >= 60:
            return 'Fair'
        elif health_score >= 40:
            return 'Poor'
        else:
            return 'Critical'
    
    def _get_alert_status(self, host: Dict[str, Any]) -> str:
        """Get alert status based on thresholds"""
        if not host.get('is_online', False):
            return 'critical'
        
        cpu = host.get('cpu_load', 0)
        memory = host.get('memory_used', 0)
        disk = host.get('disk_used', 0)
        
        # Critical alerts
        if cpu > 85 or memory > 90 or disk > 90:
            return 'critical'
        
        # Warning alerts
        if cpu > 70 or memory > 75 or disk > 80:
            return 'warning'
        
        return 'ok'

def calculate_enhanced_summary(vm_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate enhanced summary with performance metrics"""
    if not vm_data:
        return {
            'total': 0, 'online': 0, 'offline': 0,
            'online_percent': 0, 'offline_percent': 0,
            'performance': {}, 'alerts': {},
            'system_status': 'unknown'
        }
    
    total = len(vm_data)
    online = sum(1 for vm in vm_data if vm.get('is_online', False))
    offline = total - online
    
    # Performance metrics
    online_vms = [vm for vm in vm_data if vm.get('is_online', False)]
    
    if online_vms:
        avg_cpu = sum(vm.get('cpu_load', 0) for vm in online_vms) / len(online_vms)
        avg_memory = sum(vm.get('memory_used', 0) for vm in online_vms) / len(online_vms)
        avg_disk = sum(vm.get('disk_used', 0) for vm in online_vms) / len(online_vms)
        avg_health = sum(vm.get('health_score', 0) for vm in online_vms) / len(online_vms)
    else:
        avg_cpu = avg_memory = avg_disk = avg_health = 0
    
    # Alert counts
    critical_alerts = sum(1 for vm in vm_data if vm.get('alert_status') == 'critical')
    warning_alerts = sum(1 for vm in vm_data if vm.get('alert_status') == 'warning')
    
    # Performance ratings
    ratings = {}
    for vm in vm_data:
        rating = vm.get('performance_rating', 'Unknown')
        ratings[rating] = ratings.get(rating, 0) + 1
    
    return {
        'total': total,
        'online': online,
        'offline': offline,
        'online_percent': (online / total * 100) if total > 0 else 0,
        'offline_percent': (offline / total * 100) if total > 0 else 0,
        'performance': {
            'avg_cpu': round(avg_cpu, 1),
            'avg_memory': round(avg_memory, 1),
            'avg_disk': round(avg_disk, 1),
            'avg_health': round(avg_health, 1),
            'peak_cpu': max([vm.get('cpu_load', 0) for vm in vm_data], default=0),
            'peak_memory': max([vm.get('memory_used', 0) for vm in vm_data], default=0),
            'peak_disk': max([vm.get('disk_used', 0) for vm in vm_data], default=0)
        },
        'alerts': {
            'critical': critical_alerts,
            'warning': warning_alerts,
            'ok': total - critical_alerts - warning_alerts - offline
        },
        'ratings': ratings,
        'system_status': 'healthy' if offline == 0 and critical_alerts == 0 else 'degraded' if critical_alerts < 3 else 'critical'
    }

def generate_enhanced_charts(vm_data: List[Dict[str, Any]], summary: Dict[str, Any], output_dir: str = 'static'):
    """Generate comprehensive charts for the report"""
    try:
        os.makedirs(output_dir, exist_ok=True)
        
        # Set style for professional charts
        plt.style.use('default')
        
        # 1. VM Status Distribution Chart
        _generate_status_chart(summary, output_dir)
        
        # 2. Performance Metrics Chart
        _generate_performance_chart(vm_data, output_dir)
        
        # 3. Resource Utilization Chart
        _generate_resource_chart(vm_data, output_dir)
        
        # 4. Alert Status Chart
        _generate_alert_chart(summary, output_dir)
        
        safe_log_info(f"✅ Generated enhanced charts in {output_dir}")
        return True
        
    except Exception as e:
        safe_log_error(f"❌ Error generating charts: {e}")
        return False

def _generate_status_chart(summary: Dict[str, Any], output_dir: str):
    """Generate VM status distribution chart"""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    labels = ['Online', 'Offline']
    sizes = [summary['online'], summary['offline']]
    colors = ['#27ae60', '#e74c3c']
    explode = (0.05, 0.05)
    
    if sum(sizes) > 0:
        wedges, texts, autotexts = ax.pie(
            sizes, labels=labels, colors=colors, explode=explode,
            autopct='%1.1f%%', startangle=90, shadow=True,
            textprops={'fontsize': 12, 'fontweight': 'bold'}
        )
        
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
    
    ax.set_title('VM Status Distribution', fontsize=16, fontweight='bold', pad=20)
    plt.tight_layout()
    plt.savefig(f"{output_dir}/vm_status_chart.png", dpi=300, bbox_inches='tight')
    plt.close()

def _generate_performance_chart(vm_data: List[Dict[str, Any]], output_dir: str):
    """Generate performance metrics chart"""
    if not vm_data:
        return
    
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 5))
    
    online_vms = [vm for vm in vm_data if vm.get('is_online', False)]
    
    if online_vms:
        cpu_data = [vm.get('cpu_load', 0) for vm in online_vms]
        memory_data = [vm.get('memory_used', 0) for vm in online_vms]
        disk_data = [vm.get('disk_used', 0) for vm in online_vms]
        
        # CPU Usage Distribution
        ax1.hist(cpu_data, bins=10, color='#3498db', alpha=0.7, edgecolor='black')
        ax1.set_title('CPU Usage Distribution', fontweight='bold')
        ax1.set_xlabel('CPU Usage (%)')
        ax1.set_ylabel('Number of VMs')
        if cpu_data:
            ax1.axvline(np.mean(cpu_data), color='red', linestyle='--', label=f'Avg: {np.mean(cpu_data):.1f}%')
            ax1.legend()
        
        # Memory Usage Distribution
        ax2.hist(memory_data, bins=10, color='#e74c3c', alpha=0.7, edgecolor='black')
        ax2.set_title('Memory Usage Distribution', fontweight='bold')
        ax2.set_xlabel('Memory Usage (%)')
        ax2.set_ylabel('Number of VMs')
        if memory_data:
            ax2.axvline(np.mean(memory_data), color='blue', linestyle='--', label=f'Avg: {np.mean(memory_data):.1f}%')
            ax2.legend()
        
        # Disk Usage Distribution
        ax3.hist(disk_data, bins=10, color='#9b59b6', alpha=0.7, edgecolor='black')
        ax3.set_title('Disk Usage Distribution', fontweight='bold')
        ax3.set_xlabel('Disk Usage (%)')
        ax3.set_ylabel('Number of VMs')
        if disk_data:
            ax3.axvline(np.mean(disk_data), color='green', linestyle='--', label=f'Avg: {np.mean(disk_data):.1f}%')
            ax3.legend()
    
    plt.tight_layout()
    plt.savefig(f"{output_dir}/performance_distribution.png", dpi=300, bbox_inches='tight')
    plt.close()

def _generate_resource_chart(vm_data: List[Dict[str, Any]], output_dir: str):
    """Generate resource utilization overview chart"""
    if not vm_data:
        return
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    online_vms = [vm for vm in vm_data if vm.get('is_online', False)][:20]  # Top 20 for readability
    
    if online_vms:
        vm_names = [vm.get('name', 'Unknown')[:15] + '...' if len(vm.get('name', '')) > 15 else vm.get('name', 'Unknown') for vm in online_vms]
        cpu_data = [vm.get('cpu_load', 0) for vm in online_vms]
        memory_data = [vm.get('memory_used', 0) for vm in online_vms]
        disk_data = [vm.get('disk_used', 0) for vm in online_vms]
        
        x = np.arange(len(vm_names))
        width = 0.25
        
        ax.bar(x - width, cpu_data, width, label='CPU %', color='#3498db', alpha=0.8)
        ax.bar(x, memory_data, width, label='Memory %', color='#e74c3c', alpha=0.8)
        ax.bar(x + width, disk_data, width, label='Disk %', color='#9b59b6', alpha=0.8)
        
        ax.set_title('Resource Utilization Overview (Top 20 VMs)', fontsize=14, fontweight='bold')
        ax.set_xlabel('Virtual Machines')
        ax.set_ylabel('Usage Percentage')
        ax.set_xticks(x)
        ax.set_xticklabels(vm_names, rotation=45, ha='right')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Add threshold lines
        ax.axhline(y=80, color='orange', linestyle='--', alpha=0.7, label='Warning (80%)')
        ax.axhline(y=90, color='red', linestyle='--', alpha=0.7, label='Critical (90%)')
    
    plt.tight_layout()
    plt.savefig(f"{output_dir}/resource_overview.png", dpi=300, bbox_inches='tight')
    plt.close()

def _generate_alert_chart(summary: Dict[str, Any], output_dir: str):
    """Generate alert status chart"""
    fig, ax = plt.subplots(figsize=(8, 6))
    
    alerts = summary.get('alerts', {})
    labels = ['OK', 'Warning', 'Critical']
    sizes = [alerts.get('ok', 0), alerts.get('warning', 0), alerts.get('critical', 0)]
    colors = ['#27ae60', '#f39c12', '#e74c3c']
    
    if sum(sizes) > 0:
        wedges, texts, autotexts = ax.pie(
            sizes, labels=labels, colors=colors,
            autopct='%1.1f%%', startangle=90,
            textprops={'fontsize': 11, 'fontweight': 'bold'}
        )
        
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
    
    ax.set_title('Alert Status Distribution', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(f"{output_dir}/alert_status.png", dpi=300, bbox_inches='tight')
    plt.close()

# Backward compatibility functions
def connect_zabbix() -> bool:
    """Backward compatible connection function"""
    client = EnhancedZabbixClient()
    return client.connect()

def fetch_vm_data() -> List[Dict[str, Any]]:
    """Backward compatible VM data fetch"""
    client = EnhancedZabbixClient()
    try:
        hosts = client.fetch_hosts()
        return client.enrich_host_data(hosts)
    finally:
        client.disconnect()

def enrich_vm_data(vm_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Backward compatible data enrichment"""
    client = EnhancedZabbixClient()
    try:
        return client.enrich_host_data(vm_data)
    finally:
        client.disconnect()

def calculate_summary(vm_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Backward compatible summary calculation"""
    return calculate_enhanced_summary(vm_data)

def generate_pie_chart(summary: Dict[str, Any]) -> bool:
    """Backward compatible chart generation"""
    return generate_enhanced_charts([], summary)

def generate_status_chart(summary: Dict[str, Any], output_path: str = "static/vm_status_chart.png") -> bool:
    """Backward compatible status chart"""
    try:
        output_dir = os.path.dirname(output_path)
        _generate_status_chart(summary, output_dir)
        return True
    except Exception as e:
        safe_log_error(f"Error generating status chart: {e}")
        return False

def main():
    """Enhanced main function for testing with detailed CPU debugging"""
    import sys
    import logging
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    safe_log_info("🚀 Enhanced Zabbix Data Fetcher - FIXED CPU Keys Version")
    safe_log_info("=" * 60)
    
    client = EnhancedZabbixClient()
    
    try:
        # Test connection
        if not client.connect():
            safe_log_error("❌ Failed to connect to Zabbix API")
            sys.exit(1)
        
        # Fetch hosts
        safe_log_info("📡 Fetching VM data from Zabbix...")
        hosts = client.fetch_hosts()
        
        if not hosts:
            logger.warning("⚠️ No hosts found")
            return None, None
        
        # Show CPU key analysis for first few hosts
        safe_log_info("🔍 CPU Key Analysis for first 3 hosts:")
        safe_log_info("-" * 50)
        
        for host in hosts[:3]:
            host_name = host.get('name', 'Unknown')
            host_id = host.get('hostid', 'Unknown')
            
            safe_log_info(f"🖥️  Testing CPU keys for: {host_name}")
            
            # Test primary CPU keys
            cpu_keys_to_test = [
                'system.cpu.util',           # Primary (should work)
                'system.cpu.util[]',         # Secondary (might not work)
                'system.cpu.util[,user]',    # User CPU (should work)
                'system.cpu.util[,system]'   # System CPU (should work)
            ]
            
            for test_key in cpu_keys_to_test:
                try:
                    items = client.zapi.item.get(
                        hostids=host_id,
                        filter={'key_': test_key},
                        output=['lastvalue', 'key_']
                    )
                    
                    if items and items[0].get('lastvalue'):
                        value = items[0]['lastvalue']
                        safe_log_info(f"   ✅ {test_key}: {value}%")
                    else:
                        safe_log_info(f"   ❌ {test_key}: Not found or no data")
                        
                except Exception as e:
                    safe_log_info(f"   ❌ {test_key}: Error - {e}")
        
        safe_log_info("-" * 50)
        
        # Enrich data with enhanced CPU retrieval
        safe_log_info("🔍 Enriching VM data with enhanced CPU metrics...")
        vm_data = client.enrich_host_data(hosts)
        
        # Calculate summary
        summary = calculate_enhanced_summary(vm_data)
        
        # Generate charts
        safe_log_info("📊 Generating enhanced charts...")
        generate_enhanced_charts(vm_data, summary)
        
        # Display results with CPU focus
        safe_log_info("📋 Collection Results (CPU Focus):")
        safe_log_info(f"   Total VMs: {summary['total']}")
        safe_log_info(f"   Online: {summary['online']} ({summary['online_percent']:.1f}%)")
        safe_log_info(f"   Offline: {summary['offline']} ({summary['offline_percent']:.1f}%)")
        safe_log_info(f"   Avg CPU: {summary['performance']['avg_cpu']:.1f}%")
        safe_log_info(f"   Peak CPU: {summary['performance']['peak_cpu']:.1f}%")
        safe_log_info(f"   Avg Memory: {summary['performance']['avg_memory']:.1f}%")
        safe_log_info(f"   Avg Disk: {summary['performance']['avg_disk']:.1f}%")
        safe_log_info(f"   Critical Alerts: {summary['alerts']['critical']}")
        safe_log_info(f"   Warning Alerts: {summary['alerts']['warning']}")
        safe_log_info(f"   System Status: {summary['system_status'].upper()}")
        
        # Show detailed CPU analysis
        safe_log_info("💻 Detailed CPU Analysis:")
        online_vms = [vm for vm in vm_data if vm.get('is_online', False)]
        cpu_values = [vm.get('cpu_load', 0) for vm in online_vms]
        
        if cpu_values:
            non_zero_cpu = [cpu for cpu in cpu_values if cpu > 0]
            safe_log_info(f"   VMs with CPU data: {len(non_zero_cpu)}/{len(online_vms)}")
            safe_log_info(f"   CPU Range: {min(cpu_values):.1f}% - {max(cpu_values):.1f}%")
            safe_log_info(f"   VMs with >1% CPU: {len([cpu for cpu in cpu_values if cpu > 1])}")
            safe_log_info(f"   VMs with >10% CPU: {len([cpu for cpu in cpu_values if cpu > 10])}")
            
            # Show top CPU users
            sorted_vms = sorted(online_vms, key=lambda x: x.get('cpu_load', 0), reverse=True)
            safe_log_info("   Top 5 CPU users:")
            for i, vm in enumerate(sorted_vms[:5]):
                cpu = vm.get('cpu_load', 0)
                name = vm.get('name', 'Unknown')[:30]
                safe_log_info(f"     {i+1}. {name}: {cpu:.1f}%")
        
        safe_log_info("=" * 60)
        safe_log_info("✅ Enhanced data collection completed successfully!")
        
        return vm_data, summary
        
    except KeyboardInterrupt:
        safe_log_info("⚠️ Collection interrupted by user")
        return None, None
    except Exception as e:
        safe_log_error(f"❌ Error during collection: {e}")
        import traceback
        traceback.print_exc()
        return None, None
    finally:
        client.disconnect()

if __name__ == "__main__":
    vm_data, summary = main()
    if vm_data:
        print(f"\n🎯 FIXED VERSION Collection Summary:")
        print(f"   • {len(vm_data)} VMs processed")
        print(f"   • {summary['online']} online, {summary['offline']} offline")
        print(f"   • Avg CPU Usage: {summary['performance']['avg_cpu']:.1f}%")
        print(f"   • Peak CPU Usage: {summary['performance']['peak_cpu']:.1f}%")
        print(f"   • Avg Disk Usage: {summary['performance']['avg_disk']:.1f}%")
        print(f"   • {summary['alerts']['critical']} critical alerts")
        print(f"   • System status: {summary['system_status']}")
        
        # Show CPU status
        online_vms = [vm for vm in vm_data if vm.get('is_online', False)]
        cpu_values = [vm.get('cpu_load', 0) for vm in online_vms]
        non_zero_cpu = [cpu for cpu in cpu_values if cpu > 0]
        
        print(f"\n💻 CPU Analysis:")
        print(f"   • {len(non_zero_cpu)}/{len(online_vms)} VMs reporting CPU data")
        print(f"   • Using fixed key: 'system.cpu.util' (confirmed working)")
        print(f"   • Removed broken key: 'system.cpu.util[]' (not found in Zabbix)")
        
    else:
        print("❌ Data collection failed")
        sys.exit(1)