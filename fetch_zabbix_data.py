#!/usr/bin/env python3
"""
Enhanced Zabbix Data Fetcher - FIXED VERSION with Correct CPU Keys
Advanced monitoring with comprehensive metrics and error handling
Fixed based on actual Zabbix key analysis: system.cpu.util (working) vs system.cpu.util[] (not found)
Now includes VM Power State Change Detection
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

# Import VM State Tracker
try:
    from vm_state_tracker import VMStateTracker
    STATE_TRACKER_AVAILABLE = True
except ImportError:
    STATE_TRACKER_AVAILABLE = False
    print("Warning: VM State Tracker not available. Power change detection disabled.")

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
            print("INFO: {}".format(message))
    except:
        print("INFO: {}".format(message))

def safe_log_error(message):
    """Safe logging error"""
    try:
        log = get_logger()
        if log:
            log.error(message)
        else:
            print("ERROR: {}".format(message))
    except:
        print("ERROR: {}".format(message))

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
                    # UPDATED keys for Zabbix 7.0 - NEW FORMAT
                    'vfs.fs.size[/,pused]',                  # Zabbix 7.0 standard format
                    'vfs.fs.size["/",pused]',                # Alternative with quotes
                    'vfs.fs.pused[/]',                       # Simple format
                    'vfs.fs.pused["/"]',                     # Simple with quotes
                    
                    # Root filesystem variations for Zabbix 7.0
                    'vfs.fs.size[/,used,percentage]',        # Extended format
                    'vfs.fs.size[/,pfree]',                  # Percentage free (need to calculate)
                    'vfs.fs.discovery[/,pused]',             # Discovery format
                    
                    # Alternative partition patterns
                    'vfs.fs.size[/home,pused]',              # Home partition
                    'vfs.fs.size[/var,pused]',               # Var partition
                    'vfs.fs.size[/opt,pused]',               # Opt partition
                    'vfs.fs.size[/boot,pused]',              # Boot partition
                    
                    # Windows partitions (Zabbix 7.0 format)
                    'vfs.fs.size[C:,pused]',                 # Windows C drive
                    'vfs.fs.size[D:,pused]',                 # Windows D drive
                    'vfs.fs.size["C:",pused]',               # Windows with quotes
                    'vfs.fs.size["D:",pused]',               # Windows with quotes
                    
                    # LEGACY formats (keep for compatibility)
                    'vfs.fs.dependent.size[/,pused]',        # Old format
                    'vfs.fs.dependent.size[/home,pused]',    # Old format
                    'vfs.fs.dependent.size[/var,pused]',     # Old format
                    'vfs.fs.dependent[/,pused]',
                    
                    # VMware/Virtual machine specific
                    'vm.vmware.hv.datastore.size[*,pused]',  # VMware
                    'system.disk.used.percent',               # Generic system
                    'disk.usage.percent'                      # Alternative generic
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
            
            safe_log_info("🔌 Connecting to Zabbix: {}".format(self.config['url']))
            
            # Create API connection with correct parameters
            self.zapi = ZabbixAPI(self.config['url'])
            
            # Login
            self.zapi.login(
                user=self.config['user'],
                password=self.config['password']
            )
            
            # Verify connection
            api_version = self.zapi.api_version()
            safe_log_info("✅ Connected to Zabbix API v{}".format(api_version))
            self.connection_established = True
            self.last_error = None
            return True
            
        except Exception as e:
            self.last_error = "Connection error: {}".format(e)
            safe_log_error("❌ {}".format(self.last_error))
            return False
    
    def _clean_vm_name(self, name: str) -> str:
        """Clean VM name to remove duplicates and standardize format"""
        try:
            # Remove common duplicates
            cleaned = name
            
            # Remove duplicate "PRD_One-Climate-" prefixes
            if "PRD_One-Climate-" in cleaned:
                # Keep only the last occurrence
                parts = cleaned.split("PRD_One-Climate-")
                if len(parts) > 2:  # Multiple occurrences
                    cleaned = "PRD_One-Climate-" + parts[-1]
            
            # Remove duplicate "One-Climate-" patterns
            if "One-Climate-" in cleaned and cleaned.count("One-Climate-") > 1:
                parts = cleaned.split("One-Climate-")
                # Keep the first meaningful part
                if len(parts) > 2:
                    cleaned = "One-Climate-" + parts[-1]
            
            # Remove leading/trailing underscores and clean up
            cleaned = cleaned.strip("_")
            
            # Replace multiple underscores with single
            while "__" in cleaned:
                cleaned = cleaned.replace("__", "_")
            
            # Special cases for common patterns
            if "ONE-CLIMATE-PRD_One-Climate-" in cleaned:
                # Remove the redundant prefix
                cleaned = cleaned.replace("ONE-CLIMATE-PRD_One-Climate-", "PRD_One-Climate-")
            
            # Clean up any remaining redundant patterns
            if "PRD_PRD_" in cleaned:
                cleaned = cleaned.replace("PRD_PRD_", "PRD_")
            
            # Fix Zabbix server name duplicates - remove IP suffix
            if "Zabbix server_" in cleaned:
                # Keep only "Zabbix server" part, remove IP suffix
                cleaned = "Zabbix server"
            elif cleaned.startswith("Zabbix server ") or cleaned.startswith("Zabbix server-"):
                # Normalize to just "Zabbix server"
                cleaned = "Zabbix server"
            
            return cleaned
            
        except Exception as e:
            safe_log_error("Error cleaning VM name '{}': {}".format(name, e))
            return name  # Return original if cleaning fails
    
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
                # Clean up VM name to remove duplicates
                clean_name = self._clean_vm_name(host['name'])
                
                host_data = {
                    'hostid': host.get('hostid', ''),
                    'name': clean_name,
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
            
            safe_log_info("📊 Fetched {} hosts from Zabbix".format(len(vm_hosts)))
            return vm_hosts
            
        except Exception as e:
            safe_log_error("❌ Error fetching hosts: {}".format(e))
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
        safe_log_info("🔍 Getting {} for host {}".format(metric_type, hostid))
        
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
                                    
                                    safe_log_info("✅ Found {}: {} = {}% (age: {}s)".format(metric_type, item['key_'], value, data_age))
                                    
                                    # Prefer recent data, but accept older data if it's the only option
                                    if data_age < 600:  # 10 minutes
                                        return value
                                    elif data_age < 3600:  # 1 hour - still acceptable
                                        logger.debug("⚠️ Using older data: {}s old".format(data_age))
                                        return value
                                    else:
                                        logger.debug("❌ Data too old: {}s".format(data_age))
                                        continue
                                else:
                                    safe_log_info("❌ Value out of range: {}% for {}".format(value, item['key_']))
                                    continue
                            else:
                                # For other metrics, return any valid numeric value
                                if value >= 0:
                                    safe_log_info("✅ Found {}: {} = {}".format(metric_type, item['key_'], value))
                                    return value
                                    
                        except (ValueError, TypeError) as e:
                            safe_log_error("❌ Invalid value for {}: {} - {}".format(item['key_'], item.get('lastvalue'), e))
                            continue
                    else:
                        logger.debug("❌ No lastvalue for {}".format(key))
                        
            except Exception as e:
                safe_log_error("❌ Error getting {} for host {}: {}".format(key, hostid, e))
                continue
        
        # FALLBACK: If no specific keys work, try to find ANY matching items
        if metric_type == 'cpu':
            try:
                logger.debug("🔍 Fallback: searching for any CPU items for host {}".format(hostid))
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
                                safe_log_info("🆘 Fallback CPU found: {} = {}%".format(item['key_'], value))
                                return value
                        except:
                            continue
                            
            except Exception as e:
                safe_log_error("❌ Fallback search failed for host {}: {}".format(hostid, e))
        
        safe_log_info("❌ No valid {} data found for host {}".format(metric_type, hostid))
        return 0.0
    
    def _get_disk_usage_exact(self, hostid: str) -> float:
        """ENHANCED disk usage detection for Zabbix 7.0 with comprehensive debugging"""
        safe_log_info("🔍 Getting disk usage for host {} (Enhanced Zabbix 7.0 Detection)".format(hostid))
        
        try:
            # PRIORITY 1: Zabbix 7.0 standard formats (FIXED for dependent items)
            priority_keys = [
                'vfs.fs.dependent.size[/,pused]',        # Zabbix 7.0 dependent items (FIXED!)
                'vfs.fs.size[/,pused]',                  # Standard format
                'vfs.fs.size["/",pused]',                # With quotes
                'vfs.fs.pused[/]',                       # Simple format
                'vfs.fs.pused["/"]',                     # Simple with quotes
            ]
            
            # PRIORITY 2: Extended and alternative formats
            extended_keys = [
                'vfs.fs.size[/,used,percentage]',        # Extended format
                'vfs.fs.discovery[/,pused]',             # Discovery format
                'system.disk.used.percent',               # Generic system
                'disk.usage.percent',                     # Alternative generic
            ]
            
            # PRIORITY 3: Legacy and partition-specific keys
            legacy_keys = [
                'vfs.fs.dependent.size[/,pused]',        # Legacy format
                'vfs.fs.size[/home,pused]',              # Home partition
                'vfs.fs.size[/var,pused]',               # Var partition
                'vfs.fs.size[/opt,pused]',               # Opt partition
                'vfs.fs.size[C:,pused]',                 # Windows C
                'vfs.fs.size["C:",pused]',               # Windows C with quotes
            ]
            
            all_keys = priority_keys + extended_keys + legacy_keys
            disk_values = []
            found_keys = []
            
            safe_log_info("🔍 Testing {} disk key formats for host {}".format(len(all_keys), hostid))
            
            for i, key in enumerate(all_keys):
                try:
                    safe_log_info("   Testing key {}/{}: {}".format(i+1, len(all_keys), key))
                    
                    # Try exact match first
                    items = self.zapi.item.get(
                        hostids=hostid,
                        filter={'key_': key},
                        output=['lastvalue', 'lastclock', 'key_', 'name'],
                        limit=1
                    )
                    
                    if items and items[0].get('lastvalue') is not None:
                        try:
                            value = float(items[0]['lastvalue'])
                            
                            # Handle pfree (percentage free) - convert to pused
                            if 'pfree' in key:
                                value = 100 - value  # Convert free to used
                                safe_log_info("   🔄 Converted pfree {}% to pused {}%".format(100-value, value))
                            
                            if 0 <= value <= 100:
                                # Check data freshness
                                last_clock = int(items[0].get('lastclock', 0))
                                current_time = int(time.time())
                                data_age = current_time - last_clock
                                
                                disk_values.append(value)
                                found_keys.append(key)
                                
                                safe_log_info("   ✅ FOUND DISK USAGE: {} = {}% (age: {}s, priority: {})".format(
                                    key, value, data_age,
                                    "HIGH" if key in priority_keys else "MEDIUM" if key in extended_keys else "LOW"
                                ))
                                
                                # If we found a high-priority key with recent data, use it immediately
                                if key in priority_keys and data_age < 600:  # 10 minutes
                                    safe_log_info("✅ Using high-priority recent data: {}%".format(value))
                                    return value
                            else:
                                safe_log_info("   ❌ Value out of range: {}%".format(value))
                        except (ValueError, TypeError) as e:
                            safe_log_info("   ❌ Invalid value: {} - {}".format(items[0].get('lastvalue'), e))
                    else:
                        safe_log_info("   ❌ No data for key: {}".format(key))
                        
                except Exception as e:
                    safe_log_info("   ❌ Error testing key {}: {}".format(key, e))
                    continue
            
            # Analyze results
            if disk_values:
                safe_log_info("🎯 Found {} disk values: {}".format(len(disk_values), disk_values))
                safe_log_info("🔑 Found keys: {}".format(found_keys))
                
                # Prioritize root filesystem patterns
                root_patterns = ['[/,pused]', '["/",pused]', 'pused[/]', 'pused["/"]']
                for i, key in enumerate(found_keys):
                    for pattern in root_patterns:
                        if pattern in key:
                            safe_log_info("✅ Using root filesystem key: {} = {}%".format(key, disk_values[i]))
                            return disk_values[i]
                
                # Return the highest usage (most critical)
                max_usage = max(disk_values)
                max_index = disk_values.index(max_usage)
                safe_log_info("✅ Using highest usage: {} = {}%".format(found_keys[max_index], max_usage))
                return max_usage
            
            # FALLBACK: Search for ANY disk-related items
            safe_log_info("🆘 No exact matches found, trying comprehensive search...")
            fallback_searches = ['vfs.fs', 'disk', 'filesystem', 'storage']
            
            for search_term in fallback_searches:
                try:
                    items = self.zapi.item.get(
                        hostids=hostid,
                        search={'key_': search_term},
                        output=['lastvalue', 'key_', 'name'],
                        filter={'status': 0}  # Only enabled items
                    )
                    
                    safe_log_info("🔍 Found {} items for search term '{}'".format(len(items), search_term))
                    
                    for item in items:
                        key = item.get('key_', '')
                        name = item.get('name', '')
                        if item.get('lastvalue') is not None and ('pused' in key or 'percent' in key.lower() or 'usage' in name.lower()):
                            try:
                                value = float(item['lastvalue'])
                                if 0 <= value <= 100:
                                    safe_log_info("🆘 FALLBACK FOUND: {} = {}% (name: {})".format(key, value, name))
                                    return value
                            except (ValueError, TypeError):
                                continue
                                
                except Exception as e:
                    safe_log_info("❌ Fallback search failed for '{}': {}".format(search_term, e))
                    continue
            
            safe_log_info("❌ No disk usage data found for host {}".format(hostid))
            return 0.0
            
        except Exception as e:
            safe_log_error("❌ Critical error getting disk usage for host {}: {}".format(hostid, e))
            return 0.0
    
    def enrich_host_data(self, hosts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enrich host data with comprehensive metrics"""
        if not hosts:
            return []
        
        safe_log_info("🔍 Enriching data for {} hosts...".format(len(hosts)))
        
        enriched_hosts = []
        for i, host in enumerate(hosts):
            try:
                host_name = host.get('name', 'Unknown')
                host_id = host.get('hostid')
                
                safe_log_info("🔍 Processing host {}/{}: {} (ID: {})".format(i+1, len(hosts), host_name, host_id))
                
                # Get hostid safely
                if not host_id:
                    safe_log_info("⚠️ Host {} missing hostid - using defaults".format(host_name))
                    host['cpu_load'] = 0.0
                    host['memory_used'] = 0.0
                    host['disk_used'] = 0.0
                else:
                    # Get current metrics with enhanced logging
                    host['cpu_load'] = self.get_item_value(host_id, 'cpu')
                    host['memory_used'] = self.get_item_value(host_id, 'memory')
                    host['disk_used'] = self.get_item_value(host_id, 'disk')
                
                # Determine online status
                host['is_online'] = self._determine_online_status(host)
                
                # Calculate health score
                host['health_score'] = self._calculate_health_score(host)
                
                # Get performance rating
                host['performance_rating'] = self._get_performance_rating(host)
                
                # Add alert status
                host['alert_status'] = self._get_alert_status(host)
                
                # Enhanced logging for metrics
                safe_log_info("📊 Host {}: CPU={:.1f}%, Memory={:.1f}%, Disk={:.1f}%, Health={}, Status={}".format(
                    host_name,
                    host['cpu_load'],
                    host['memory_used'], 
                    host['disk_used'],
                    host['health_score'],
                    'Online' if host['is_online'] else 'Offline'
                ))
                
                enriched_hosts.append(host)
                
            except Exception as e:
                logger.warning("⚠️ Error enriching host {}: {}".format(host.get('name', 'unknown'), e))
                # Add with defaults
                for key in ['cpu_load', 'memory_used', 'disk_used']:
                    host.setdefault(key, 0.0)
                host['is_online'] = False
                host['health_score'] = 0
                host['performance_rating'] = 'Unknown'
                host['alert_status'] = 'error'
                enriched_hosts.append(host)
        
        # Detect power state changes
        power_changes = self.detect_power_state_changes(enriched_hosts)
        if power_changes and power_changes.get('has_changes', False):
            safe_log_info("🔄 Power state changes detected: {} total changes".format(power_changes.get('total_changes', 0)))
            
            # Add power change information to the enriched data
            for host in enriched_hosts:
                host['power_changes'] = power_changes
        
        safe_log_info("✅ Data enrichment completed for {} hosts".format(len(enriched_hosts)))
        return enriched_hosts
    
    def detect_power_state_changes(self, hosts: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Detect VM power state changes using VM State Tracker"""
        if not STATE_TRACKER_AVAILABLE:
            return None
        
        try:
            # Initialize state tracker
            tracker = VMStateTracker("logs/vm_states.json")
            
            # Detect changes
            changes = tracker.detect_power_changes(hosts)
            
            # Generate alerts for changes
            alerts = tracker.generate_power_change_alerts(changes)
            
            # Get summary statistics
            stats = tracker.get_summary_stats(changes)
            
            # Clean up old states (keep last 7 days)
            tracker.cleanup_old_states(days_to_keep=7)
            
            return {
                'changes': changes,
                'alerts': alerts,
                'stats': stats,
                'has_changes': stats.get('has_changes', False),
                'total_changes': stats.get('total_changes', 0),
                'powered_on_count': stats.get('powered_on_count', 0),
                'powered_off_count': stats.get('powered_off_count', 0),
                'recovered_count': stats.get('recovered_count', 0),
                'new_vms_count': stats.get('new_vms_count', 0),
                'timestamp': stats.get('timestamp')
            }
            
        except Exception as e:
            safe_log_error("❌ Error detecting power state changes: {}".format(e))
            return None
    
    def get_power_change_summary(self, power_changes: Optional[Dict[str, Any]]) -> str:
        """Get human-readable summary of power changes"""
        if not power_changes or not power_changes.get('has_changes', False):
            return "No power state changes detected"
        
        summary_parts = []
        
        if power_changes.get('powered_on_count', 0) > 0:
            summary_parts.append("🟢 {} powered on".format(power_changes['powered_on_count']))
        
        if power_changes.get('powered_off_count', 0) > 0:
            summary_parts.append("🔴 {} powered off".format(power_changes['powered_off_count']))
        
        if power_changes.get('recovered_count', 0) > 0:
            summary_parts.append("🟡 {} recovered".format(power_changes['recovered_count']))
        
        if power_changes.get('new_vms_count', 0) > 0:
            summary_parts.append("✨ {} new VMs".format(power_changes['new_vms_count']))
        
        return ", ".join(summary_parts) if summary_parts else "No significant changes"
    
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
        
        safe_log_info("✅ Generated enhanced charts in {}".format(output_dir))
        return True
        
    except Exception as e:
        safe_log_error("❌ Error generating charts: {}".format(e))
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
    plt.savefig("{}/vm_status_chart.png".format(output_dir), dpi=300, bbox_inches='tight')
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
            ax1.axvline(np.mean(cpu_data), color='red', linestyle='--', label='Avg: {:.1f}%'.format(np.mean(cpu_data)))
            ax1.legend()
        
        # Memory Usage Distribution
        ax2.hist(memory_data, bins=10, color='#e74c3c', alpha=0.7, edgecolor='black')
        ax2.set_title('Memory Usage Distribution', fontweight='bold')
        ax2.set_xlabel('Memory Usage (%)')
        ax2.set_ylabel('Number of VMs')
        if memory_data:
            ax2.axvline(np.mean(memory_data), color='blue', linestyle='--', label='Avg: {:.1f}%'.format(np.mean(memory_data)))
            ax2.legend()
        
        # Disk Usage Distribution
        ax3.hist(disk_data, bins=10, color='#9b59b6', alpha=0.7, edgecolor='black')
        ax3.set_title('Disk Usage Distribution', fontweight='bold')
        ax3.set_xlabel('Disk Usage (%)')
        ax3.set_ylabel('Number of VMs')
        if disk_data:
            ax3.axvline(np.mean(disk_data), color='green', linestyle='--', label='Avg: {:.1f}%'.format(np.mean(disk_data)))
            ax3.legend()
    
    plt.tight_layout()
    plt.savefig("{}/performance_distribution.png".format(output_dir), dpi=300, bbox_inches='tight')
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
    plt.savefig("{}/resource_overview.png".format(output_dir), dpi=300, bbox_inches='tight')
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
    plt.savefig("{}/alert_status.png".format(output_dir), dpi=300, bbox_inches='tight')
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
        safe_log_error("Error generating status chart: {}".format(e))
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
            
            safe_log_info("🖥️  Testing CPU keys for: {}".format(host_name))
            
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
                        safe_log_info("   ✅ {}: {value}%".format(test_key))
                    else:
                        safe_log_info("   ❌ {}: Not found or no data".format(test_key))
                        
                except Exception as e:
                    safe_log_info("   ❌ {}: Error - {e}".format(test_key))
        
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
                # Ensure summary exists (FIX FOR SUMMARY ERROR)
        if 'summary' not in locals():
            summary = {
                'total': len(enriched_hosts),
                'online': len([h for h in enriched_hosts if h.get('is_online', False)]),
                'offline': len([h for h in enriched_hosts if not h.get('is_online', False)]),
                'online_percent': 0.0,
                'offline_percent': 0.0,
                'performance': {
                    'avg_cpu': 0.0,
                    'peak_cpu': 0.0,
                    'avg_memory': 0.0,
                    'avg_disk': 0.0
                },
                'alerts': {
                    'critical': 0,
                    'warning': 0
                },
                'system_status': 'HEALTHY'
            }
            if summary['total'] > 0:
                summary['online_percent'] = (summary['online'] / summary['total']) * 100
                summary['offline_percent'] = (summary['offline'] / summary['total']) * 100
        
        safe_log_info("📋 Collection Results (CPU Focus):")
        safe_log_info("   Total VMs: {}".format(summary['total']))
        safe_log_info("   Online: {} ({:.1f}%)".format(summary['online'], summary['online_percent']))
        safe_log_info("   Offline: {} ({:.1f}%)".format(summary['offline'], summary['offline_percent']))
        safe_log_info("   Avg CPU: {:.1f}%".format(summary['performance']['avg_cpu']))
        safe_log_info("   Peak CPU: {:.1f}%".format(summary['performance']['peak_cpu']))
        safe_log_info("   Avg Memory: {:.1f}%".format(summary['performance']['avg_memory']))
        safe_log_info("   Avg Disk: {:.1f}%".format(summary['performance']['avg_disk']))
        safe_log_info("   Critical Alerts: {}".format(summary['alerts']['critical']))
        safe_log_info("   Warning Alerts: {}".format(summary['alerts']['warning']))
        safe_log_info("   System Status: {}".format(summary['system_status'].upper()))
        
        # Show detailed CPU analysis
        safe_log_info("💻 Detailed CPU Analysis:")
        online_vms = [vm for vm in vm_data if vm.get('is_online', False)]
        cpu_values = [vm.get('cpu_load', 0) for vm in online_vms]
        
        if cpu_values:
            non_zero_cpu = [cpu for cpu in cpu_values if cpu > 0]
            safe_log_info("   VMs with CPU data: {}/{}".format(len(non_zero_cpu), len(online_vms)))
            safe_log_info("   CPU Range: {:.1f}% - {:.1f}%".format(min(cpu_values), max(cpu_values)))
            safe_log_info("   VMs with >1% CPU: {}".format(len([cpu for cpu in cpu_values if cpu > 1])))
            safe_log_info("   VMs with >10% CPU: {}".format(len([cpu for cpu in cpu_values if cpu > 10])))
            
            # Show top CPU users
            sorted_vms = sorted(online_vms, key=lambda x: x.get('cpu_load', 0), reverse=True)
            safe_log_info("   Top 5 CPU users:")
            for i, vm in enumerate(sorted_vms[:5]):
                cpu = vm.get('cpu_load', 0)
                name = vm.get('name', 'Unknown')[:30]
                safe_log_info("     {}. {name}: {cpu:.1f}%".format(i+1))
        
        safe_log_info("=" * 60)
        safe_log_info("✅ Enhanced data collection completed successfully!")
        
        return vm_data, summary
        
    except KeyboardInterrupt:
        safe_log_info("⚠️ Collection interrupted by user")
        return None, None
    except Exception as e:
        safe_log_error("❌ Error during collection: {}".format(e))
        import traceback
        traceback.print_exc()
        return None, None
    finally:
        client.disconnect()

if __name__ == "__main__":
    vm_data, summary = main()
    if vm_data:
        print(f"\n🎯 FIXED VERSION Collection Summary:")
        print("   • {} VMs processed".format(len(vm_data)))
        print("   • {} online, {summary['offline']} offline".format(summary['online']))
        print("   • Avg CPU Usage: {:.1f}%".format(summary['performance']['avg_cpu']))
        print("   • Peak CPU Usage: {:.1f}%".format(summary['performance']['peak_cpu']))
        print("   • Avg Disk Usage: {:.1f}%".format(summary['performance']['avg_disk']))
        print("   • {} critical alerts".format(summary['alerts']['critical']))
        print("   • System status: {}".format(summary['system_status']))
        
        # Show CPU status
        online_vms = [vm for vm in vm_data if vm.get('is_online', False)]
        cpu_values = [vm.get('cpu_load', 0) for vm in online_vms]
        non_zero_cpu = [cpu for cpu in cpu_values if cpu > 0]
        
        print(f"\n💻 CPU Analysis:")
        print("   • {}/{len(online_vms)} VMs reporting CPU data".format(len(non_zero_cpu)))
        print(f"   • Using fixed key: 'system.cpu.util' (confirmed working)")
        print(f"   • Removed broken key: 'system.cpu.util[]' (not found in Zabbix)")
        
    else:
        print("❌ Data collection failed")
        sys.exit(1)